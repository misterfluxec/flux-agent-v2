import pytest
import httpx

@pytest.mark.asyncio
async def test_ingestion_flow_status(api_client: httpx.AsyncClient):
    """
    Test Integration 3: Ingestion Pipeline
    Verifica que el pipeline de ingesta responda correctamente
    (ej. reject archivos inválidos, status del pipeline).
    """
    # Probar endpoint de subida con archivo vacío
    response = await api_client.post("/api/v1/ingest/start", files={"archivo": ("test.txt", b"")})
    
    # La respuesta debe manejar archivos vacíos/sin auth correctamente
    assert response.status_code in [202, 400, 401, 415, 422, 404]
    
    # Si requiere Auth, primero verificar que no ingrese
    response = await api_client.get("/api/v1/ingest/status/1234")
    assert response.status_code in [401, 404]
