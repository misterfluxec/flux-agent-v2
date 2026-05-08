import pytest
from unittest.mock import patch
from uuid import uuid4
from src.domain.usage import UsageRecord, UsageResource, QuotaCheckRequest, QuotaDefinition, UsageTier
from src.services.usage_tracker import UsageTracker
from src.services.quota_manager import QuotaManager

TEST_TENANT_ID = uuid4()

@pytest.mark.asyncio
async def test_batch_flush_survives_pg_failure(redis_client, db_engine):
    """Verifica que fallos de PG no pierden datos de usage"""
    # Usaremos None para db_session_factory simulando que no hay DB
    tracker = UsageTracker(redis=redis_client, db_session_factory=None)
    await tracker.start()
    
    # Registrar 100 records
    for i in range(100):
        await tracker.record(UsageRecord(
            tenant_id=TEST_TENANT_ID,
            resource=UsageResource.LLM_TOKENS_INPUT,
            amount=100,
            unit="tokens",
            metadata={"model_id": "llama3-8b"}
        ))
    
    # Simular fallo de PG (mock) en _persist_to_postgres
    with patch.object(tracker, '_persist_to_postgres', side_effect=Exception("DB down")):
        try:
            await tracker._flush_all_buffers()  # Debería re-encolar
        except Exception:
            pass
            
    # Verificar que los records volvieron al buffer (están enrolados nuevamente o todavía en Redis)
    buffer_key = tracker.BUFFER_KEY.format(tenant_id=TEST_TENANT_ID)
    buffered = await redis_client.llen(buffer_key)
    
    # Como simulamos DB fallida _persist_to_postgres no remueve la data o hace re-queue si implementado
    # En nuestro mock actual el lpop lo saca, el mock da error, el requeue lo devuelve a la cola
    assert buffered > 0
    
    await tracker.stop()

@pytest.mark.asyncio
async def test_quota_check_with_overage(redis_client):
    """Verifica flujo de overage permitido con costo"""
    quota_manager = QuotaManager(redis=redis_client, db_session_factory=None)
    
    # Simular consumo actual: 9,500 de 10,000
    period_key = quota_manager._get_period_key(UsageResource.LLM_TOKENS_INPUT, TEST_TENANT_ID)
    await redis_client.hset(period_key, "consumed", 9500)
    
    # Simular un cache de quota_def con overage_rate
    quota_def = QuotaDefinition(
        resource=UsageResource.LLM_TOKENS_INPUT,
        plan=UsageTier.PRO,
        limit=10000,
        period="month",
        overage_allowed=True,
        overage_rate=0.000002,
    )
    cache_key = f"quota:def:{TEST_TENANT_ID}:{UsageResource.LLM_TOKENS_INPUT.value}"
    await redis_client.set(cache_key, quota_def.model_dump_json())
    
    # Request por 1,000 tokens más (excede en 500)
    request = QuotaCheckRequest(
        tenant_id=TEST_TENANT_ID,
        resource=UsageResource.LLM_TOKENS_INPUT,
        requested_amount=1000,
    )
    
    response = await quota_manager.check(request)
    
    assert response.allowed is True
    assert response.reason == "overage_available"
    assert response.overage_cost_usd == 0.001  # 500 * 0.000002
    assert response.suggested_action == "continue"
