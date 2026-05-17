import asyncio
import time
import json
from uuid import uuid4
from datetime import datetime
from src.integrations.canonical import CanonicalEnvelope, ProcessingState
from src.integrations.meta.normalizer import MetaNormalizer, MetaAdapter
from src.integrations.meta.version_resolver import MetaVersionResolver
from src.integrations.idempotency_utils import generate_dedup_hash
from src.domain.integration_raw import IncomingProviderPayload
from src.integrations.quarantine import QuarantinedEvent, QuarantineReason

# Mock Services for Simulation
class MockIdentityResolver:
    async def resolve(self, sender_id: str, tenant_id: uuid4):
        return str(uuid4())

class MockDB:
    def __init__(self):
        self.payloads = {}
        self.quarantine = {}
    
    def add(self, obj):
        if isinstance(obj, IncomingProviderPayload):
            self.payloads[obj.id] = obj
        elif isinstance(obj, QuarantinedEvent):
            self.quarantine[obj.id] = obj

async def run_fortress_pipeline_simulation():
    print("🚀 Iniciando Simulación de Runtime E2E (Fortress Path v2.5)")
    db = MockDB()
    identity_resolver = MockIdentityResolver()
    tenant_id = uuid4()
    correlation_id = str(uuid4())
    
    # 1. RAW PAYLOAD (WhatsApp Ecuador)
    raw_json = {
        "entry": [{
            "changes": [{
                "value": {
                    "metadata": {"display_phone_number": "12345", "version": "v16"},
                    "messages": [{
                        "id": "wa_sim_001",
                        "from": "593987654321",
                        "text": {"body": "Hola, necesito un pedido para Guayaquil"},
                        "timestamp": str(time.time())
                    }]
                }
            }]
        }]
    }
    
    # Simulate RAW storage (Sprint B.1)
    raw_payload = IncomingProviderPayload(
        tenant_id=tenant_id,
        provider="meta",
        provider_event_id="wa_sim_001",
        payload=raw_json,
        checksum="sha256_mock_123",
        schema_fingerprint="fingerprint_mock_abc"
    )
    db.add(raw_payload)
    print(f"  [RAW] Payload guardado: {raw_payload.id}")

    # 2. DEDUP CHECK
    dedup_hash = generate_dedup_hash("meta", "wa_sim_001", raw_json)
    print(f"  [DEDUP] Hash generado: {dedup_hash[:16]}...")

    # 3. VERSION ROUTER
    version = MetaVersionResolver.resolve_version(raw_json)
    normalizer_cls = MetaVersionResolver.get_normalizer(version)
    
    if not normalizer_cls:
        print("  [ERROR] Versión no soportada. Enviando a QUARANTINE.")
        return

    print(f"  [VERSION] Router seleccionó: {version}")

    # 4. NORMALIZATION (ACL)
    start_norm = time.time()
    canonical_msg = normalizer_cls.to_canonical(raw_json)
    norm_duration = (time.time() - start_norm) * 1000
    
    envelope = CanonicalEnvelope(
        provider="meta",
        provider_event_id="wa_sim_001",
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        received_at=time.time(),
        country_code="EC",
        raw_reference_id=str(raw_payload.id),
        dedup_hash=dedup_hash,
        processing_state=ProcessingState.NORMALIZED,
        normalized_at=time.time()
    )
    print(f"  [ACL] Normalización exitosa en {norm_duration:.2f}ms")

    # 5. IDENTITY RESOLUTION (Sprint C Preview)
    print(f"  [IDENTITY] Resolviendo identidad para: {canonical_msg.sender_id}")
    customer_id = await identity_resolver.resolve(canonical_msg.sender_id, tenant_id)
    print(f"  [IDENTITY] Cliente resuelto: {customer_id}")

    # 6. EVENTBUS SIMULATION
    envelope.processing_state = ProcessingState.PUBLISHED
    envelope.published_at = time.time()
    
    # 7. SLO AUDIT
    total_latency = (envelope.published_at - envelope.received_at) * 1000
    print(f"✅ Simulación Finalizada con Éxito")
    print(f"📊 Métricas SLO (ACL):")
    print(f"   - Latencia Normalización: {norm_duration:.2f}ms (Target < 100ms)")
    print(f"   - Latencia Total Pipeline: {total_latency:.2f}ms (Target < 500ms)")
    print(f"   - Estado Final: {envelope.processing_state.value}")

if __name__ == "__main__":
    asyncio.run(run_fortress_pipeline_simulation())
