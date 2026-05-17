import time
import logging
import re
import json
from uuid import uuid4
from domain.orchestrator import OrchestratorContext, OrchestratorOutput, OrchestratorStep
from domain.events import DomainEvent, EventMetadata, EventType, OrchestratorStartedPayload, OrchestratorStepCompletedPayload
from core.event_bus import EventBus
from services.policy_engine import PolicyEngine
from services.tool_executor import ToolExecutor
from services.ai_memory import AIMemoryManager

from services.professional_actor_loop import ProfessionalActorLoop, ActorLoopContext
from runtime.graph import ExecutionGraph
from runtime.graph_node import GraphNode
from runtime.state_machine import AgentExecutionState

logger = logging.getLogger("flux.ai_orchestrator")

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
        from runtime.graph_edge import GraphEdge
        graph.add_edge(GraphEdge(source="step_memory", target="step_intent"))
        graph.add_edge(GraphEdge(source="step_intent", target="step_policy"))
        graph.add_edge(GraphEdge(source="step_policy", target="step_memory_persist"))
        graph.add_edge(GraphEdge(source="step_memory_persist", target="step_event_emit"))
        
        return graph

    async def _handle_memory(self, ctx: OrchestratorContext) -> None:
        try:
            # Nota: get_full_context en ai_memory.py no acepta tenant_id actualmente,
            # pero lo incluimos según la especificación Enterprise para futura compatibilidad.
            full_context = await self.memory_manager.get_full_context(
                customer_id=str(ctx.customer_id),
                agent_id=str(ctx.agent_id)
            )
            ctx.retrieved_memory = full_context
        except Exception as exc:
            logger.warning(
                "memory_retrieval_failed",
                extra={
                    "error": str(exc),
                    "conversation_id": str(ctx.conversation_id),
                },
            )
            ctx.retrieved_memory = {
                "episodic": [], "semantic": {}, "instructions": ""
            }

    async def _handle_intent(self, ctx: OrchestratorContext) -> None:
        import json, re

        system_prompt = (
            "Eres un clasificador de intenciones para un agente "
            "de ventas LATAM. Analiza el mensaje y responde "
            "ÚNICAMENTE con JSON válido, sin texto adicional:\n"
            '{"intent": "<type>", "confidence": <0.0-1.0>}\n\n'
            "Tipos: purchase, inquiry, complaint, booking, "
            "greeting, farewell, support, price_check, out_of_scope"
        )

        messages = [{"role": "system", "content": system_prompt}]

        # Agregar últimas 3 interacciones como contexto
        memory = ctx.retrieved_memory or {}
        for turn in (memory.get("episodic") or [])[-3:]:
            messages.append({
                "role": turn.get("role", "user"),
                "content": turn.get("content", ""),
            })

        messages.append({
            "role": "user",
            "content": ctx.raw_input or "",
        })

        try:
            raw = await self.llm_provider.generate(
                messages=messages,
                temperature=0.1,
                max_tokens=60,
            )
            content = raw.get("content", "") if isinstance(raw, dict) else str(raw)
            match = re.search(r"\{[^}]+\}", content, re.DOTALL)
            data = json.loads(match.group() if match else content)
            ctx.detected_intent = data.get("intent", "inquiry")
            ctx.intent_confidence = float(data.get("confidence", 0.5))
        except Exception as exc:
            logger.warning(
                "intent_detection_failed",
                extra={"error": str(exc)},
            )
            ctx.detected_intent = "inquiry"
            ctx.intent_confidence = 0.5
        
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

    async def _handle_response(self, ctx: OrchestratorContext) -> None:
        memory = ctx.retrieved_memory or {}
        system_content = (
            memory.get("instructions")
            or "Eres un agente de ventas profesional. "
               "Responde en el language del cliente, "
               "de forma concisa, amable y útil."
        )

        messages = [{"role": "system", "content": system_content}]

        # Historial reciente (últimas 5 interacciones)
        for turn in (memory.get("episodic") or [])[-5:]:
            messages.append({
                "role": turn.get("role", "user"),
                "content": turn.get("content", ""),
            })

        # Contexto de herramientas si hay resultados previos
        if ctx.tool_results:
            tool_ctx = "\n".join(
                f"- {r.get('tool','tool')}: {r.get('result','')}"
                for r in ctx.tool_results
            )
            messages.append({
                "role": "system",
                "content": f"Información disponible:\n{tool_ctx}",
            })

        messages.append({
            "role": "user",
            "content": ctx.raw_input or "",
        })

        raw = await self.llm_provider.generate(
            messages=messages,
            temperature=0.7,
            max_tokens=500,
        )

        # Manejo de tool_calls
        if isinstance(raw, dict) and raw.get("tool_calls"):
            tool_results = []
            for tc in raw["tool_calls"]:
                fn = tc.get("function", {})
                try:
                    result = await self.tool_executor.execute(
                        tool_name=fn.get("name", ""),
                        arguments=fn.get("arguments", {}),
                        tenant_id=str(ctx.tenant_id),
                    )
                    tool_results.append({
                        "tool": fn.get("name"),
                        "result": result,
                    })
                except Exception as exc:
                    logger.warning(
                        "tool_call_failed",
                        extra={"tool": fn.get("name"), "error": str(exc)},
                    )
            ctx.tool_results = (ctx.tool_results or []) + tool_results
            # Segunda llamada con resultados de herramientas
            await self._handle_response(ctx)
            return

        content = (
            raw.get("content", "") if isinstance(raw, dict) else str(raw)
        )
        ctx.generated_response = content or "No pude generar una respuesta."

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

    async def _execute_step(
        self, step: OrchestratorStep, ctx: OrchestratorContext
    ) -> None:
        if step == OrchestratorStep.MEMORY_RETRIEVAL:
            await self._handle_memory(ctx)

        elif step == OrchestratorStep.INTENT_DETECTION:
            await self._handle_intent(ctx)

        elif step == OrchestratorStep.RESPONSE_GENERATION:
            await self._handle_response(ctx)

        else:
            logger.warning(
                "orchestrator_unknown_step",
                extra={"step": str(step)},
            )

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
            
            # Recuperar status si existe (Graph Runner Checkpointing)
            saved_state_json = await self.redis.get(state_key) if hasattr(self.redis, "get") else None
            start_node_id = "step_memory"
            if saved_state_json:
                saved_state = json.loads(saved_state_json)
                start_node_id = saved_state.get("next_node_id", "step_memory")
                print(f"[GraphRunner] Recuperando status: retomando desde {start_node_id}.")

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
