"""
Professional Actor Loop - Orquestador Unificado (Sprint D - Fortress Path v2.7)
================================================================================
Une las tres capas del sistema:

  MetaGPT Layer  →  CAMEL Debate Layer  →  Ollama Local Brain
  (Roles + SOPs)    (Razonamiento crítico)  (Inferencia privada)

Flujo de decisión:
  1. Carga el SOP del role is_active (MetaGPT Layer)
  2. Ejecuta los pasos del SOP secuencialmente
  3. Si un paso falla o hay una excepción → activa el Debate (CAMEL Layer)
  4. El debate produce un veredicto fundamentado
  5. Todo el proceso queda registrado en el CanonicalEnvelope
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from uuid import uuid4

from domain.meta_agent import SOP, BaseRole, SOPStep, AgentState
from services.sop_manager import SOPManager
from services.sop_prompt_builder import SOPPromptBuilder
from services.agent_debate import AgentDebateOrchestrator, DebateResult, DebateVerdict
from services.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


@dataclass
class ActorLoopContext:
    """Contexto de ejecución del Professional Actor Loop."""
    session_id: str = field(default_factory=lambda: str(uuid4()))
    tenant_id: str = ""
    customer_id: str = ""
    role_id: str = ""
    input_text: str = ""
    business_context: Dict[str, Any] = field(default_factory=dict)

    # Estado de ejecución
    active_sop: Optional[SOP] = None
    current_step: int = 0
    steps_completed: List[int] = field(default_factory=list)
    debate_results: List[DebateResult] = field(default_factory=list)
    final_response: str = ""
    escalated_to_human: bool = False
    processing_time_ms: int = 0


@dataclass
class ActorLoopResult:
    """Resultado final del Professional Actor Loop."""
    session_id: str
    success: bool
    response: str
    sop_adhered: bool
    debates_triggered: int
    final_verdict: str
    processing_time_ms: int
    audit_trail: List[Dict[str, Any]]


class ProfessionalActorLoop:
    """
    Orquestador del Professional Actor Loop.
    Combina MetaGPT (SOPs) + CAMEL (Debate) + Ollama (Inferencia local).
    """

    def __init__(
        self,
        sop_manager: SOPManager,
        debate_orchestrator: AgentDebateOrchestrator,
        tool_executor: Optional[ToolExecutor] = None,
        ollama_url: str = "http://localhost:11434",
        model: str = "llama3",
    ):
        self.sop_manager = sop_manager
        self.debate_orchestrator = debate_orchestrator
        self.tool_executor = tool_executor
        self.ollama_url = ollama_url
        self.model = model

    async def execute(self, ctx: ActorLoopContext) -> ActorLoopResult:
        """
        Punto de entrada principal del Professional Actor Loop.
        """
        start = time.time()
        audit_trail: List[Dict[str, Any]] = []
        debates_triggered = 0

        logger.info(f"[PAL] Iniciando sesión {ctx.session_id} para tenant {ctx.tenant_id}")

        # ─── PASO 1: Cargar SOP del Rol ───────────────────────────────────────
        sop = self.sop_manager.get_sop_for_role(ctx.role_id, ctx.input_text)
        if sop:
            ctx.active_sop = sop
            logger.info(f"[PAL] SOP is_active: {sop.name} ({len(sop.steps)} pasos)")
            audit_trail.append({
                "event": "sop_loaded",
                "sop_name": sop.name,
                "steps_count": len(sop.steps)
            })
        else:
            logger.warning(f"[PAL] Sin SOP para role {ctx.role_id}. Activando modo libre.")

        # ─── PASO 2: Ejecutar Pasos del SOP ──────────────────────────────────
        sop_success = True
        if ctx.active_sop:
            for step in sorted(ctx.active_sop.steps, key=lambda s: s.order):
                step_result = await self._execute_sop_step(step, ctx)

                if step_result["success"]:
                    ctx.steps_completed.append(step.order)
                    audit_trail.append({
                        "event": "sop_step_completed",
                        "step": step.order,
                        "instruction": step.instruction,
                    })
                else:
                    # ─── EXCEPCIÓN: Activar Debate CAMEL ──────────────────
                    logger.warning(f"[PAL] Paso {step.order} fallido. Activando debate...")
                    debates_triggered += 1

                    debate_topic = (
                        f"El paso '{step.instruction}' del SOP ha fallado.\n"
                        f"Error: {step_result.get('error', 'Desconocido')}\n"
                        f"Solicitud original: {ctx.input_text}"
                    )

                    debate = await self.debate_orchestrator.run_debate(
                        topic=debate_topic,
                        context=ctx.business_context,
                        scenario_type="order_validation",
                    )
                    ctx.debate_results.append(debate)
                    audit_trail.append({
                        "event": "debate_triggered",
                        **debate.to_audit_dict()
                    })

                    if debate.verdict == DebateVerdict.APPROVE:
                        logger.info(f"[PAL] Debate resuelto: APROBAR (confianza {debate.confidence:.0%})")
                        ctx.steps_completed.append(step.order)
                    elif debate.verdict == DebateVerdict.REJECT:
                        sop_success = False
                        ctx.final_response = f"La solicitud fue rechazada por el comité de especialistas: {debate.reasoning}"
                        break
                    else:  # ESCALATE o NEEDS_MORE_INFO
                        ctx.escalated_to_human = True
                        ctx.final_response = (
                            f"Tu caso requiere atención de un especialista humano.\n"
                            f"Razón: {debate.reasoning}\n"
                            f"ID de sesión para seguimiento: {ctx.session_id}"
                        )
                        sop_success = False
                        break

        # ─── PASO 3: Generar Respuesta Final ─────────────────────────────────
        if not ctx.final_response:
            ctx.final_response = await self._generate_final_response(ctx, sop_success)

        ctx.processing_time_ms = int((time.time() - start) * 1000)
        logger.info(
            f"[PAL] Sesión {ctx.session_id} completada en {ctx.processing_time_ms}ms. "
            f"Pasos: {len(ctx.steps_completed)}/{len(ctx.active_sop.steps) if ctx.active_sop else 0}. "
            f"Debates: {debates_triggered}"
        )

        final_verdict = "success"
        if ctx.escalated_to_human:
            final_verdict = "escalated"
        elif not sop_success:
            final_verdict = "rejected"

        return ActorLoopResult(
            session_id=ctx.session_id,
            success=sop_success and not ctx.escalated_to_human,
            response=ctx.final_response,
            sop_adhered=len(ctx.steps_completed) > 0,
            debates_triggered=debates_triggered,
            final_verdict=final_verdict,
            processing_time_ms=ctx.processing_time_ms,
            audit_trail=audit_trail,
        )

    async def _execute_sop_step(
        self, step: SOPStep, ctx: ActorLoopContext
    ) -> Dict[str, Any]:
        """
        Ejecuta un paso del SOP usando el nuevo Tool Runtime (Enterprise).
        """
        # Simulación determinista para el prototipo
        simulated_failures = ctx.business_context.get("simulated_failures", [])
        if step.order in simulated_failures:
            return {
                "success": False,
                "error": f"Fallo simulado en paso {step.order}: {step.instruction}",
                "step": step.order,
            }

        if step.required_action and self.tool_executor:
            from runtime.tool_intent import ToolIntent
            from runtime.tool_runtime import ToolRuntime
            import hashlib
            
            logger.info(f"[PAL] Paso {step.order} requiere herramienta: {step.required_action}")
            
            # 1. El LLM extrae el intento (Simulado aquí, pero estructurado formalmente)
            intent = ToolIntent(
                tool=step.required_action,
                confidence=0.95,
                extracted_parameters={"query": ctx.input_text},
                source_prompt_hash=hashlib.sha256(ctx.input_text.encode()).hexdigest(),
                reasoning="El usuario solicitó implícitamente esta acción en su texto."
            )
            
            # 2. El ToolRuntime ejecuta con todos los Guards de gobernanza
            # Idealmente ToolRuntime se inicializa a nivel de clase, pero lo instanciamos aquí por simplicidad del prototipo
            tool_runtime = ToolRuntime(tool_executor=self.tool_executor)
            
            runtime_ctx = {
                "role_id": ctx.role_id,
                "customer_id": ctx.customer_id,
                "session_id": ctx.session_id,
                "tenant_id": ctx.tenant_id
            }
            
            result = await tool_runtime.execute_intent(intent, runtime_ctx)
            
            if not result.success:
                return {
                    "success": False,
                    "error": result.error,
                    "status": result.status,
                    "step": step.order,
                }
                
            if result.status == "WAITING_APPROVAL":
                return {
                    "success": False,
                    "error": "Pausado esperando aprobación humana",
                    "status": result.status,
                    "step": step.order,
                }
                
            logger.info(f"[PAL] Herramienta {step.required_action} ejecutada exitosamente a través de ToolRuntime.")
            return {"success": True, "step": step.order, "data": result.data}

        await asyncio.sleep(0.05)  # Simula latencia de operación en pasos sin herramienta
        return {"success": True, "step": step.order}

    async def _generate_final_response(self, ctx: ActorLoopContext, success: bool) -> str:
        """Genera la respuesta final usando el LLM local (stub Ollama)."""
        if success and ctx.active_sop:
            steps_done = len(ctx.steps_completed)
            total_steps = len(ctx.active_sop.steps)
            return (
                f"✅ Proceso completado exitosamente ({steps_done}/{total_steps} pasos).\n"
                f"Tu solicitud ha sido procesada según el procedimiento '{ctx.active_sop.name}'."
            )
        return "La solicitud ha sido procesada. El equipo te contactará pronto."
