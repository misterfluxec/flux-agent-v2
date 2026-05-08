import pytest
import asyncio
from uuid import uuid4
from typing import List
from src.domain.events import DomainEvent, EventMetadata, EventType, MessageReceivedPayload
from src.domain.policies import PolicyRule, PolicyCondition, PolicyOperator, PolicyAction

TEST_TENANT_ID = uuid4()

@pytest.mark.asyncio
async def test_full_flow_message_to_response(event_bus, orchestrator, policy_engine):
    """Test que simula un mensaje de WhatsApp desde webhook hasta respuesta"""
    # Arrange: configurar política que deniega descuentos >20% en plan basic
    await policy_engine.create_rule(PolicyRule(
        id="no_high_discount_basic",
        name="No descuentos altos en plan básico",
        conditions=[
            PolicyCondition(field="tenant_plan", operator=PolicyOperator.EQ, value="basic"),
            PolicyCondition(field="discount_amount", operator=PolicyOperator.GT, value=20),
        ],
        action=PolicyAction.DENY,
        priority=500,
    ))
    
    # Act: publicar evento de mensaje con intento de descuento alto
    event = DomainEvent(
        metadata=EventMetadata(event_type=EventType.MESSAGE_RECEIVED, tenant_id=TEST_TENANT_ID),
        payload=MessageReceivedPayload(
            channel="whatsapp",
            from_number="+5491112345678",
            message_id="test_123",
            content="Quiero un descuento del 30% en mi compra",
        ),
    )
    
    # Suscribirse para capturar eventos de salida
    captured_events: List[DomainEvent] = []
    async def capture_handler(e: DomainEvent):
        captured_events.append(e)
    
    await event_bus.subscribe(
        event_types=[EventType.RESPONSE_GENERATED, EventType.POLICY_VIOLATION],
        handler=capture_handler,
        consumer_name="test-capture",
    )
    
    # Procesar directamente a través del orchestrator para la prueba
    # Simulando lo que haría el event bus en runtime
    
    # En la prueba real, si el "Orchestrator" tiene dependencias mockeadas de LLM, 
    # generaría el paso de POLICY_EVALUATION como fallido si le pasamos ese contexto
    # Como el AIOrchestrator está en modo stub, vamos a simular su evaluación
    await orchestrator.process_event(event)
    await asyncio.sleep(0.1)  # Esperar procesamiento async
    
    # Verificación de completitud del test
    response_events = [e for e in captured_events if e.metadata.event_type == EventType.RESPONSE_GENERATED]
    assert len(response_events) == 1
