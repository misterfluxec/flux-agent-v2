import time
from uuid import uuid4
from domain.orchestrator import OrchestratorContext, OrchestratorOutput, OrchestratorStep
from domain.events import DomainEvent, EventMetadata, EventType, OrchestratorStartedPayload, OrchestratorStepCompletedPayload
from core.event_bus import EventBus
from services.policy_engine import PolicyEngine
from services.tool_executor import ToolExecutor
from services.ai_memory import AIMemoryManager

from services.professional_actor_loop import ProfessionalActorLoop, ActorLoopContext
from src.runtime.graph import ExecutionGraph
from src.runtime.graph_node import GraphNode
from src.runtime.state_machine import AgentExecutionState

class AIOrchestrator:
    def __init__(self, redis, event_bus: EventBus, policy_engine: PolicyEngine, tool_executor: ToolExecutor, memory_manager: AIMemoryManager, llm_provider, professional_actor_loop: ProfessionalActorLoop = None):
        self.redis = redis
        self.event_bus = event_bus
        self.policy_engine = policy_engine
        self.tool_executor = tool_executor
        self.memory_manager = memory_manager
        self.llm_provider = llm_provider
        self.pal = professional_actor_loop
        self.graph = self._build_orchestrator_graph()
        
    def _build_orchestrator_graph(self) -> ExecutionGraph:
        graph = ExecutionGraph()
        
        # Nodos lineales
        node_memory = GraphNode(id="step_memory", handler_name="handle_memory")
        node_intent = GraphNode(id="step_intent", handler_name="handle_intent")
        node_policy = GraphNode(id="step_policy", handler_name="handle_policy")
        node_persist = GraphNode(id="step_memory_persist", handler_name="handle_memory_persist")
        node_emit = GraphNode(id="step_event_emit", handler_name="handle_event_emit")

        graph.add_node(node_memory, handler=self._handle_memory)
        graph.add_node(node_intent, handler=self._handle_intent)
        graph.add_node(node_policy, handler=self._handle_policy)
        graph.add_node(node_persist, handler=self._handle_memory_persist)
        graph.add_node(node_emit, handler=self._handle_event_emit)

        # Transiciones explícitas usando GraphEdge
        from src.runtime.graph_edge import GraphEdge
        graph.add_edge(GraphEdge(source="step_memory", target="step_intent"))
        graph.add_edge(GraphEdge(source="step_intent", target="step_policy"))
        graph.add_edge(GraphEdge(source="step_policy", target="step_memory_persist"))
        graph.add_edge(GraphEdge(source="step_memory_persist", target="step_event_emit"))
        
        return graph

    async def _handle_memory(self, ctx: OrchestratorContext) -> str:
        ctx.retrieved_memory = {"history": "loaded"}
        return None
        
    async def _handle_intent(self, ctx: OrchestratorContext) -> str:
        ctx.detected_intent = "purchase"
        ctx.intent_confidence = 0.9
        return None
        
    async def _handle_policy(self, ctx: OrchestratorContext) -> str:
        if self.pal:
            pal_ctx = ActorLoopContext(
                session_id=str(ctx.correlation_id),
                tenant_id=str(ctx.tenant_id),
                customer_id=str(ctx.customer_id) if ctx.customer_id else "",
                role_id="role-sales-latam",
                input_text=ctx.raw_input,
                business_context=ctx.input_metadata
            )
            pal_result = await self.pal.execute(pal_ctx)
            
            if pal_result.success or pal_result.final_verdict == "escalated":
                ctx.generated_response = pal_result.response
                # Al simular success, retornamos None para seguir al próximo nodo "step_memory_persist"
                return None
            else:
                ctx.generated_response = await self._generate_fallback_response(ctx, "policy_denied")
                raise Exception("Policy Denied")
        return None

    async def _handle_memory_persist(self, ctx: OrchestratorContext) -> str:
        return None

    async def _handle_event_emit(self, ctx: OrchestratorContext) -> str:
        return None
    
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
            import json
            state_key = f"orchestrator:state:{ctx.correlation_id}"
            
            # Recuperar estado si existe (Graph Runner Checkpointing)
            saved_state_json = await self.redis.get(state_key) if hasattr(self.redis, "get") else None
            start_node_id = "step_memory"
            if saved_state_json:
                saved_state = json.loads(saved_state_json)
                start_node_id = saved_state.get("next_node_id", "step_memory")
                print(f"[GraphRunner] Recuperando estado: retomando desde {start_node_id}.")

            # 3. Ejecutar grafo
            try:
                # El grafo requiere que el input de handler sea Dict o un objeto. Aquí inyectamos ctx
                # Hacemos trampa pasando ctx directamente en lugar de dict, Graph lo soporta pues es tipado libre en runtime
                ctx.state = AgentExecutionState.SOP_RUNNING
                last_node = await self.graph.execute(start_node_id, ctx)
                
                if ctx.state == AgentExecutionState.WAITING_APPROVAL:
                    # Guardar checkpoint para reanudar luego
                    if hasattr(self.redis, "set"):
                        await self.redis.set(state_key, json.dumps({
                            "next_node_id": last_node
                        }), ex=3600)
                    return # Suspende la orquestación hasta aprobación asíncrona
                
            except Exception as e:
                ctx.generated_response = str(e)
                success = False
            
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
            
            # Limpiar checkpoint al finalizar
            if hasattr(self.redis, "delete"):
                await self.redis.delete(state_key)
            
        except Exception as e:
            output = OrchestratorOutput(
                success=False,
                error=str(e),
                processing_time_ms=int((time.time() - start_time) * 1000),
            )
            # Log de error simulado
