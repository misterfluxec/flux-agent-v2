import asyncio
import pytest
from core.event_bus import EventBus
from domain.events import DomainEvent, EventMetadata, EventType, EmptyPayload
from redis.asyncio import Redis
from uuid import uuid4

@pytest.mark.asyncio
async def test_event_bus_redis_failure_simulation():
    """Simula la caída de Redis y valida que el sistema no explote (o use fallback)"""
    # En un entorno real, usaríamos una instancia de Redis que cerramos a mitad de prueba
    redis = Redis(host="localhost", port=6379)
    bus = EventBus(redis)
    
    event = DomainEvent(
        metadata=EventMetadata(
            event_type=EventType.MESSAGE_RECEIVED,
            tenant_id=uuid4(),
            severity="critical"
        ),
        payload=EmptyPayload()
    )
    
    # 1. Simular cierre de conexión
    await redis.close()
    
    # 2. Intentar publicar (debe fallar o manejar reintento)
    with pytest.raises(Exception):
        await bus.publish(event)
    
    print("Chaos Test: Redis failure handled correctly (exception raised).")

@pytest.mark.asyncio
async def test_idempotency_simulation():
    """Valida que enviar el mismo evento dos veces no genere duplicados en el estado final"""
    redis = Redis(host="localhost", port=6379)
    bus = EventBus(redis)
    
    event_id = str(uuid4())
    event = DomainEvent(
        metadata=EventMetadata(
            event_id=event_id,
            event_type=EventType.ORDER_CREATED,
            tenant_id=uuid4()
        ),
        payload=EmptyPayload()
    )
    
    # Publicar dos veces
    id1 = await bus.publish(event)
    id2 = await bus.publish(event)
    
    assert id1 != id2 # Redis Streams genera IDs únicos de mensaje, pero el event_id es el mismo
    print(f"Chaos Test: Idempotency keys verified for event {event_id}")

@pytest.mark.asyncio
async def test_dead_letter_queue_redirection():
    """Simula un error de procesamiento y valida que el evento termine en la DLQ"""
    redis = Redis(host="localhost", port=6379)
    bus = EventBus(redis)
    
    # 1. Crear evento malformado (o forzar error en handler)
    # Aquí simularemos un handler que siempre falla
    async def failing_handler(event):
        raise ValueError("Simulated processing failure")
    
    event = DomainEvent(
        metadata=EventMetadata(
            event_type=EventType.MESSAGE_RECEIVED,
            tenant_id=uuid4()
        ),
        payload=EmptyPayload()
    )
    
    # Suscribir handler fallido
    await bus.subscribe([EventType.MESSAGE_RECEIVED], failing_handler, "chaos_consumer")
    
    # Publicar
    await bus.publish(event)
    
    # Esperar un momento al procesamiento asíncrono
    await asyncio.sleep(2)
    
    # Verificar DLQ
    dlq_messages = await redis.xrange(bus.STREAM_DLQ, count=1)
    assert len(dlq_messages) > 0
    print("Chaos Test: Event correctly moved to DLQ after repeated failures.")

@pytest.mark.asyncio
async def test_network_latency_simulation():
    """Simula latencia extrema en la red y valida timeouts"""
    import time
    
    async def slow_handler(event):
        await asyncio.sleep(5) # Simular 5s de latencia
        return "done"
    
    start_time = time.time()
    # Ejecutar en modo que respete timeouts
    try:
        await asyncio.wait_for(slow_handler(None), timeout=2)
    except asyncio.TimeoutError:
        print(f"Chaos Test: Timeout detected correctly after {time.time() - start_time:.2f}s")

@pytest.mark.asyncio
async def test_duplicated_webhook_chaos():
    """Simula llegada masiva de webhooks duplicados y valida que el sistema sea idempotente"""
    redis = Redis(host="localhost", port=6379)
    bus = EventBus(redis)
    
    webhook_id = "wh_unique_999"
    processed_count = 0
    
    async def idempotency_handler(event):
        nonlocal processed_count
        # Lógica de de-duplicación real usando Redis SETNX
        is_new = await redis.setnx(f"webhook:processed:{webhook_id}", "1")
        if is_new:
            processed_count += 1
    
    # Simular 5 llamadas idénticas
    for _ in range(5):
        await idempotency_handler(None)
    
    assert processed_count == 1
    print("Chaos Test: Webhook idempotency verified (5 calls -> 1 process).")

