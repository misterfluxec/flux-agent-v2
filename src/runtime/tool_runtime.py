import logging
from typing import Dict, Any, Optional
from src.runtime.tool_intent import ToolIntent
from src.runtime.tool_contract import ToolContract
from src.runtime.tool_policy_guard import ToolPolicyGuard, PolicyGuardException
from src.runtime.idempotency import IdempotencyGuard, IdempotencyGuardException
from src.core.resilience.circuit_breaker import create_circuit_breaker
from src.core.resilience.retry import create_retry
from src.core.resilience.distributed_lock import DistributedLockManager
from src.core.observability.tracing import trace_method, get_tracing_manager

logger = logging.getLogger(__name__)

class ToolRuntimeResult:
    def __init__(self, success: bool, data: Any = None, error: str = None, status: str = "COMPLETED"):
        self.success = success
        self.data = data
        self.error = error
        self.status = status # COMPLETED, WAITING_APPROVAL, REJECTED, ERROR

class ToolRuntime:
    """
    Coordina la ejecución de herramientas aplicando estrictamente todas las capas
    de gobernanza (Enterprise Level).
    
    Pipeline: Intent -> PolicyGuard -> (BudgetGuard) -> (ApprovalGuard) -> IdempotencyGuard -> ToolExecutor
    """
    
    def __init__(self, tool_executor, redis_client=None):
        self.tool_executor = tool_executor
        self.idempotency_guard = IdempotencyGuard(redis_client)
        self.circuit_breaker = create_circuit_breaker("external_api")
        self.retry_policy = create_retry("http_api")
        # TODO: Cargar el registro real de ToolContracts
        self.tool_contracts: Dict[str, ToolContract] = {} 
        
    def register_contract(self, contract: ToolContract):
        self.tool_contracts[contract.id] = contract

    @trace_method("ToolRuntime.execute_intent")
    async def execute_intent(self, intent: ToolIntent, context: Dict[str, Any]) -> ToolRuntimeResult:
        """
        Inicia la ejecución protegida del ToolIntent
        """
        tracing = get_tracing_manager()
        span = tracing.get_current_span()
        if span:
            span.set_tag("tenant_id", context.get("tenant_id"))
            span.set_tag("customer_id", context.get("customer_id"))
            span.set_tag("tool_id", intent.tool)

        tool_id = intent.tool
        contract = self.tool_contracts.get(tool_id)
        
        if not contract:
            return ToolRuntimeResult(success=False, error=f"Herramienta desconocida o sin contrato: {tool_id}")
            
        role_id = context.get("role_id", "default_role")
        customer_id = context.get("customer_id", "unknown_customer")
        session_id = context.get("session_id", "unknown_session")
        
        # 1. Policy Guard
        policy_guard = ToolPolicyGuard(role_id)
        try:
            policy_guard.validate(intent, contract)
        except PolicyGuardException as e:
            logger.warning(f"[ToolRuntime] Policy Guard bloqueó la ejecución: {e}")
            return ToolRuntimeResult(success=False, error=str(e), status="REJECTED")
            
        # 2. Budget Guard (Evaluación Multi-Tenant)
        # TODO: Implementar validación real con TenantBudget en BD/Redis
        
        # 3. Pre-Execution Debate (CAMEL)
        # Si la herramienta es crítica o tiene alto riesgo de alucinación, debatir antes de pedir aprobación humana
        # TODO: Invocar debate si la confianza del intent es baja (< 0.8) y es una acción irreversible
        
        # 4. Approval Guard
        if contract.requires_human:
            from src.runtime.human_approval import ApprovalRequest
            # TODO: Emitir evento y pausar
            logger.info(f"[ToolRuntime] {tool_id} requiere aprobación humana. Pausando ejecución.")
            # Crear y registrar el request
            correlation_id = context.get("correlation_id", "unknown")
            req = ApprovalRequest.create(
                action=tool_id,
                reason=intent.reasoning,
                confidence=intent.confidence,
                requester=role_id,
                approver_role="manager", # TODO: Sacar de policy
                correlation_id=correlation_id
            )
            return ToolRuntimeResult(success=True, data=req.model_dump(), status="WAITING_APPROVAL")
            
        # 4. Idempotency Guard
        idem_key = None
        if contract.idempotent is False or contract.risk_level == "CRITICAL":
            intent_hash = intent.calculate_intent_hash()
            correlation_id = context.get("correlation_id", "unknown")
            tenant_id = context.get("tenant_id", "default_tenant")
            idem_key = self.idempotency_guard.generate_key(tool_id, tenant_id, customer_id, correlation_id, intent_hash)
            
            can_execute = await self.idempotency_guard.check_and_lock(idem_key)
            if not can_execute:
                logger.warning(f"[ToolRuntime] Ejecución duplicada prevenida por Idempotency Guard: {idem_key}")
                return ToolRuntimeResult(success=False, error="Duplicate execution prevented.", status="REJECTED")

        # 5. Ejecución en ToolExecutor con Distributed Lock, Circuit Breaker y Retry
        try:
            logger.info(f"[ToolRuntime] Ejecutando {tool_id} tras superar Guards...")
            # tool_executor espera (name, payload, tenant_id)
            tenant_id = context.get("tenant_id")
            
            # TODO: Conectar timeouts según el contrato (timeout_ms)
            async def _do_execute():
                return await self.tool_executor.execute(
                    name=tool_id,
                    payload=intent.extracted_parameters,
                    tenant_id=tenant_id
                )
            
            # Envolvemos con Distributed Lock para herramientas CRÍTICAS
            async def _execute_with_resilience():
                # Circuit breaker -> Retry -> execute
                return await self.circuit_breaker.call(
                    self.retry_policy.execute,
                    _do_execute
                )

            if contract.risk_level == "CRITICAL":
                lock_key = f"lock:tool:{tenant_id}:{customer_id}:{tool_id}"
                async with DistributedLockManager.acquire_lock(lock_key, timeout_seconds=120):
                    exec_result = await _execute_with_resilience()
            else:
                exec_result = await _execute_with_resilience()
            
            if idem_key:
                await self.idempotency_guard.mark_completed(idem_key, "EXECUTED")
                
            return ToolRuntimeResult(success=True, data=exec_result, status="COMPLETED")
            
        except Exception as e:
            logger.error(f"[ToolRuntime] Error en ejecución de herramienta: {e}")
            if idem_key:
                await self.idempotency_guard.mark_completed(idem_key, "FAILED")
            return ToolRuntimeResult(success=False, error=str(e), status="ERROR")
