import pytest
import asyncio
from httpx import AsyncClient
from connectors.v2.sync_engine import SyncEngine
from connectors.v2.schema_mapper import CanonicalEntity
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_integration_lifecycle_flow(async_client: AsyncClient, auth_headers: dict):
    """
    Test E2E: Flujo completo del Ciclo de Vida de Integración
    1. Seleccionar Provider (Crear Sesión)
    2. Probar conexión y credenciales (SecretsVault mockeado)
    3. Iniciar Discovery (Worker en Background)
    4. Hacer Polling hasta que el estado sea 'mapping'
    """
    
    # 1. Crear Sesión
    payload_session = {
        "tenant_id": "22222222-2222-2222-2222-222222222222",
        "provider": "sqlserver"
    }
    
    res_session = await async_client.post(
        "/api/v1/integrations/sessions",
        json=payload_session,
        headers=auth_headers
    )
    
    assert res_session.status_code == 200
    data_session = res_session.json()
    assert "session_id" in data_session
    assert data_session["status"] == "configuring"
    
    session_id = data_session["session_id"]
    
    # 2. Test Connection
    payload_test = {
        "tenant_id": "22222222-2222-2222-2222-222222222222",
        "credentials": {"host": "localhost", "user": "test", "pass": "test"}
    }
    
    res_test = await async_client.post(
        f"/api/v1/integrations/sessions/{session_id}/test",
        json=payload_test,
        headers=auth_headers
    )
    
    assert res_test.status_code == 200
    # The integration router currently transitions the session to DISCOVERING in test automatically
    # Or in discover automatically.
    
    # 3. Iniciar Discovery
    res_discover = await async_client.post(
        f"/api/v1/integrations/sessions/{session_id}/discover",
        headers=auth_headers
    )
    
    assert res_discover.status_code == 200
    
    # 4. Polling (hasta 5 intentos)
    max_attempts = 5
    mapping_reached = False
    
    for _ in range(max_attempts):
        await asyncio.sleep(1) # El worker tarda ~2 segundos en el mock
        
        res_poll = await async_client.get(
            f"/api/v1/integrations/sessions/{session_id}",
            headers=auth_headers
        )
        
        assert res_poll.status_code == 200
        poll_data = res_poll.json()
        
        if poll_data["status"] == "mapping":
            mapping_reached = True
            assert "discovered_schema" in poll_data
            assert "tables" in poll_data["discovered_schema"]
            break
            
    assert mapping_reached, "El estado de la sesión nunca cambió a 'mapping'"

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_sync_engine_dry_run(db_session: AsyncSession):
    """
    Test E2E: Validar comportamiento del modo Dry-Run en el SyncEngine.
    """
    engine = SyncEngine(db=db_session, event_bus=None)
    
    # Entidad de prueba
    class MockEntity(CanonicalEntity):
        def __init__(self, ext_id, value):
            self.external_id = ext_id
            self.value = value
            
        def get_checksum(self):
            return f"chk_{self.value}"
            
        def to_dict(self):
            return {"ext": self.external_id, "val": self.value}
            
    entities = [
        MockEntity("ext_100", "A"),
        MockEntity("ext_101", "B")
    ]
    
    # Ejecutar sync en modo dry-run mockeando execute para evitar el query a tablas que no existen en el test db
    import unittest.mock as mock
    with mock.patch.object(db_session, 'execute', new_callable=mock.AsyncMock) as mock_exec:
        mock_result = mock.MagicMock()
        mock_result.fetchone.return_value = None
        mock_exec.return_value = mock_result
        
        stats = await engine.execute_sync(
            tenant_id="22222222-2222-2222-2222-222222222222",
            session_id="session_test",
            correlation_id="corr_test",
            canonical_type="customers",
            entities=entities,
            is_dry_run=True
        )
    
    # Verificar estadísticas devueltas
    assert stats["read"] == 2
    assert stats["inserted"] == 2
    assert stats["failed"] == 0

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_schema_drift_detection():
    """
    Test E2E: Validar detección de Schema Drift
    """
    engine = SyncEngine(db=None, event_bus=None)
    
    # Esquema mapeado que ESPERA la columna "FinalPrice"
    mapping_rules = {
        "fields": [
            {"source_field": "ProductId", "canonical_field": "sku"},
            {"source_field": "FinalPrice", "canonical_field": "price"}
        ]
    }
    
    # Esquema que LLEGA del discovery (le falta FinalPrice, pero tiene ProductName)
    discovered_schema_drifted = {
        "tables": [
            {
                "columns": [
                    {"name": "ProductId"},
                    {"name": "ProductName"}
                ]
            }
        ]
    }
    
    # Esquema correcto
    discovered_schema_valid = {
        "tables": [
            {
                "columns": [
                    {"name": "ProductId"},
                    {"name": "FinalPrice"}
                ]
            }
        ]
    }
    
    # Probar esquema con drift
    drifts = await engine.detect_schema_drift(discovered_schema_drifted, mapping_rules)
    assert len(drifts) == 1
    assert "FinalPrice" in drifts[0]
    
    # Probar esquema sin drift
    valid = await engine.detect_schema_drift(discovered_schema_valid, mapping_rules)
    assert len(valid) == 0
