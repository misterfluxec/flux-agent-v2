"""
Test E2E del Graph Runner y Tool Executor
=========================================
Prueba la integración de:
1. ToolExecutor con herramientas reales mockeadas (simulando DB).
2. ProfessionalActorLoop ejecutando herramientas.
3. AIOrchestrator manejando Checkpointing (Graph Runner) y PAL.
"""
import asyncio
import json
import time
import sys
import os
from uuid import uuid4

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from domain.events import DomainEvent, EventMetadata, EventType, MessageReceivedPayload
from domain.meta_agent import SOP, SOPStep, BaseRole
from domain.tools import ToolDefinition
from services.ai_orchestrator import AIOrchestrator
from services.professional_actor_loop import ProfessionalActorLoop
from services.sop_manager import SOPManager
from services.agent_debate import AgentDebateOrchestrator
from services.tool_executor import ToolExecutor


# --- Mocks ---
class MockRedis:
    def __init__(self):
        self.data = {}
    async def get(self, key):
        return self.data.get(key)
    async def set(self, key, value, ex=None):
        self.data[key] = value
    async def delete(self, key):
        if key in self.data:
            del self.data[key]

class MockEventBus:
    def __init__(self):
        self.published = []
    async def publish(self, event: DomainEvent):
        self.published.append(event)
        # print(f"  [EventBus] -> {event.metadata.event_type.value}")

class MockPolicyEngine:
    pass

class MockMemoryManager:
    pass


# --- Herramientas de Prueba ---
from pydantic import BaseModel, Field

class GetCatalogItemInput(BaseModel):
    query: str = Field(..., description="Término de búsqueda")

async def mock_get_catalog_item(params: GetCatalogItemInput, tenant_id: str, db=None):
    if "gel" in params.query.lower():
        # Simulamos stock bajo
        return {"name": "Gel UV Pro", "stock": 5, "price": 15.0}
    return {"name": "Kit Manicura Pro", "stock": 50, "price": 45.0}

class ValidateOrderInput(BaseModel):
    query: str

async def mock_validate_order_amount(params: ValidateOrderInput, tenant_id: str, db=None):
    return {"valid": True, "discount_applied": False}

class CreateDraftOrderInput(BaseModel):
    query: str

async def mock_create_draft_order(params: CreateDraftOrderInput, tenant_id: str, db=None):
    return {"order_id": "ORD-12345", "status": "draft"}


# --- Setup Global ---
def setup_environment():
    # 1. Tools
    tool_executor = ToolExecutor()
    tool_executor.register(ToolDefinition(
        name="get_catalog_item",
        description="Busca un ítem en el catálogo",
        input_schema=GetCatalogItemInput,
        handler=mock_get_catalog_item,
        category="commerce"
    ))
    tool_executor.register(ToolDefinition(
        name="validate_order_amount",
        description="Valida monto mínimo",
        input_schema=ValidateOrderInput,
        handler=mock_validate_order_amount,
        category="commerce"
    ))
    tool_executor.register(ToolDefinition(
        name="create_draft_order",
        description="Crea orden borrador",
        input_schema=CreateDraftOrderInput,
        handler=mock_create_draft_order,
        category="commerce"
    ))

    # 2. SOPs y Roles
    sop = SOP(
        id="sop-sales-latam-v1",
        name="Cierre de Venta LATAM",
        version="1.0",
        description="Proceso de ventas",
        trigger_conditions=["comprar", "pedido"],
        steps=[
            SOPStep(order=1, instruction="Verificar identidad", validation_criteria="Ok", failure_protocol="Fail"),
            SOPStep(order=2, instruction="Consultar stock", required_action="get_catalog_item", validation_criteria="Ok", failure_protocol="Fail"),
            SOPStep(order=3, instruction="Validar orden", required_action="validate_order_amount", validation_criteria="Ok", failure_protocol="Fail"),
            SOPStep(order=4, instruction="Crear draft", required_action="create_draft_order", validation_criteria="Ok", failure_protocol="Fail"),
        ]
    )
    role = BaseRole(
        id="role-sales-latam",
        name="Sales Specialist",
        profile="Ventas",
        goals=["Vender"],
        constraints=["Nada"],
        allowed_actions=["get_catalog_item", "validate_order_amount", "create_draft_order"],
        assigned_sops=[sop.id]
    )
    sop_manager = SOPManager(storage_path="/tmp/test_sops2")
    sop_manager.register_sop(sop)
    sop_manager.register_role(role)

    debate = AgentDebateOrchestrator()
    pal = ProfessionalActorLoop(
        sop_manager=sop_manager,
        debate_orchestrator=debate,
        tool_executor=tool_executor
    )

    redis = MockRedis()
    event_bus = MockEventBus()

    orchestrator = AIOrchestrator(
        redis=redis,
        event_bus=event_bus,
        policy_engine=MockPolicyEngine(),
        tool_executor=tool_executor,
        memory_manager=MockMemoryManager(),
        llm_provider=None,
        professional_actor_loop=pal
    )

    return orchestrator, redis, event_bus


async def test_graph_runner():
    orchestrator, redis, event_bus = setup_environment()
    
    # ─── Evento 1: Happy Path ───
    print("\n--- EJECUTANDO GRAPH RUNNER (Happy Path) ---")
    correlation_id = uuid4()
    event1 = DomainEvent(
        metadata=EventMetadata(
            event_type=EventType.MESSAGE_RECEIVED,
            tenant_id=uuid4(),
            correlation_id=correlation_id,
            agent_id=uuid4()
        ),
        payload=MessageReceivedPayload(
            channel="whatsapp",
            from_number="593999",
            message_id="msg1",
            content="Quiero comprar el Kit de Manicura",
            metadata={"simulated_failures": []} # Sin fallos
        )
    )
    
    await orchestrator.process_event(event1)
    
    responses = [e for e in event_bus.published if e.metadata.event_type == EventType.RESPONSE_GENERATED]
    response_payload = responses[-1].payload
    
    print("\n✅ ORCHESTRATION COMPLETADA")
    print(f"Respuesta generada: {response_payload.response_preview}")
    
    # Verificamos que el Graph Runner limpió el estado al terminar
    state_key = f"orchestrator:state:{correlation_id}"
    assert await redis.get(state_key) is None, "El Graph Runner no limpió el checkpoint"
    print("✅ Checkpointing validado (estado efímero limpiado)")

    # ─── Evento 2: Fallo de Herramienta simulado (Falta Stock de Gel) ───
    print("\n--- EJECUTANDO GRAPH RUNNER (Debate Activado por Tool) ---")
    correlation_id2 = uuid4()
    event2 = DomainEvent(
        metadata=EventMetadata(
            event_type=EventType.MESSAGE_RECEIVED,
            tenant_id=uuid4(),
            correlation_id=correlation_id2,
            agent_id=uuid4()
        ),
        payload=MessageReceivedPayload(
            channel="whatsapp",
            from_number="593999",
            message_id="msg2",
            content="Quiero gel uv", # "gel" causa que la tool mock retorne stock=5
            # Simular que stock bajo genera un error validable por PAL:
            metadata={"simulated_failures": [2]} # Forzamos fallo en el paso 2
        )
    )

    await orchestrator.process_event(event2)
    responses2 = [e for e in event_bus.published if e.metadata.event_type == EventType.RESPONSE_GENERATED]
    
    print("\n✅ ORCHESTRATION CON EXCEPCIÓN COMPLETADA")
    print(f"Respuesta generada: {responses2[-1].payload.response_preview}")
    print("\n¡Graph Runner y Tool Executor funcionan juntos correctamente!")

if __name__ == "__main__":
    asyncio.run(test_graph_runner())
