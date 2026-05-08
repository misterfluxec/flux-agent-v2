import time
from uuid import uuid4
from src.domain.orchestrator import OrchestratorContext, OrchestratorOutput, OrchestratorStep
from src.domain.events import DomainEvent, EventMetadata, EventType, OrchestratorStartedPayload, OrchestratorStepCompletedPayload
from src.core.event_bus import EventBus
from src.services.policy_engine import PolicyEngine
from src.services.tool_executor import ToolExecutor
from src.services.ai_memory import AIMemoryManager

class AIOrchestrator:
    def __init__(self, redis, event_bus: EventBus, policy_engine: PolicyEngine, tool_executor: ToolExecutor, memory_manager: AIMemoryManager, llm_provider):
        self.redis = redis
        self.event_bus = event_bus
        self.policy_engine = policy_engine
        self.tool_executor = tool_executor
        self.memory_manager = memory_manager
        self.llm_provider = llm_provider
    
    async def _build_context(self, event: DomainEvent) -> OrchestratorContext:
        payload = event.payload.model_dump() if hasattr(event.payload, "model_dump") else event.payload
        return OrchestratorContext(
            conversation_id=event.metadata.conversation_id or uuid4(),
            tenant_id=event.metadata.tenant_id,
            agent_id=event.metadata.agent_id,
            customer_id=event.metadata.customer_id,
            channel=payload.get("channel", "system"),
            raw_input=payload.get("content", ""),
            input_metadata=payload.get("metadata", {}),
            correlation_id=event.metadata.correlation_id or uuid4()
        )

    async def _execute_step(self, ctx: OrchestratorContext, step: OrchestratorStep) -> bool:
        """Lógica de cada paso. Devuelve True si es exitoso."""
        if step == OrchestratorStep.MEMORY_RETRIEVAL:
            # Ejemplo simplificado
            ctx.retrieved_memory = {"history": "loaded"}
            return True
            
        elif step == OrchestratorStep.INTENT_DETECTION:
            ctx.detected_intent = "purchase"
            ctx.intent_confidence = 0.9
            return True
            
        elif step == OrchestratorStep.POLICY_EVALUATION:
            # Aquí llamamos a Policy Engine
            return True
            
        elif step == OrchestratorStep.TOOL_SELECTION:
            ctx.selected_tools = []
            return True
            
        elif step == OrchestratorStep.TOOL_EXECUTION:
            return True
            
        elif step == OrchestratorStep.RESPONSE_GENERATION:
            # Stub de LLM
            ctx.generated_response = "Esta es una respuesta simulada por el Orquestador."
            return True
            
        elif step == OrchestratorStep.MEMORY_PERSISTENCE:
            return True
            
        elif step == OrchestratorStep.EVENT_EMISSION:
            return True
            
        return False

    async def _generate_fallback_response(self, ctx: OrchestratorContext, reason: str) -> str:
        if reason == "policy_denied":
            return "Lo siento, según las políticas actuales no puedo realizar esa acción."
        return "Lo siento, ha ocurrido un error al procesar tu solicitud."

    async def process_event(self, event: DomainEvent) -> None:
        """Handler principal consumido desde Event Bus"""
        start_time = time.time()
        
        # 1. Construir contexto
        ctx = await self._build_context(event)
        
        # 2. Publicar evento de inicio
        await self.event_bus.publish(DomainEvent(
            metadata=EventMetadata(event_type=EventType.ORCHESTRATOR_STARTED, **ctx.metadata_for_event()),
            payload=OrchestratorStartedPayload(
                conversation_id=ctx.conversation_id,
                agent_id=ctx.agent_id,
                input_preview=ctx.raw_input[:200],
                steps_planned=[s.value for s in OrchestratorStep],
            ),
        ))
        
        try:
            # 3. Ejecutar pipeline paso a paso
            for step in OrchestratorStep:
                step_start = time.time()
                success = await self._execute_step(ctx, step)
                duration_ms = int((time.time() - step_start) * 1000)
                
                # Registrar que completó
                if success:
                    ctx.completed_steps.append(step)
                
                # Publicar progreso
                await self.event_bus.publish(DomainEvent(
                    metadata=EventMetadata(event_type=EventType.ORCHESTRATOR_STEP_COMPLETED, **ctx.metadata_for_event()),
                    payload=OrchestratorStepCompletedPayload(
                        conversation_id=ctx.conversation_id,
                        step=step.value,
                        duration_ms=duration_ms,
                        success=success,
                    ),
                ))
                
                if not success and step == OrchestratorStep.POLICY_EVALUATION:
                    ctx.generated_response = await self._generate_fallback_response(ctx, "policy_denied")
                    break
            
            # 4. Construir output
            output = OrchestratorOutput(
                success=True,
                response=ctx.generated_response,
                executed_tools=ctx.tool_results,
                memory_updated=True,
                processing_time_ms=int((time.time() - start_time) * 1000),
                steps_completed=ctx.completed_steps,
            )
            
            # 5. Publicar evento de completado
            await self.event_bus.publish(DomainEvent(
                metadata=EventMetadata(event_type=EventType.RESPONSE_GENERATED, **ctx.metadata_for_event()),
                payload=output.to_event_payload(),
            ))
            
        except Exception as e:
            output = OrchestratorOutput(
                success=False,
                error=str(e),
                processing_time_ms=int((time.time() - start_time) * 1000),
            )
            # Log de error simulado
