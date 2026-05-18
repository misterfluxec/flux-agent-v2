import pytest
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_auth_flow_security(api_client: httpx.AsyncClient):
    """
    Test Integration 1: Auth Flow
    Verifica que el sistema rechace credenciales inválidas y que los 
    endpoints protegidos requieran un JWT válido.
    """
    # 1. Intento de login con email/password inválido (JSON payload para auth_router.py)
    response = await api_client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "pass"})
    assert response.status_code in [422, 401]
    
    # 2. Intento de acceso a ruta protegida sin token
    response = await api_client.get("/api/v1/auth/me")
    assert response.status_code == 401
    
    # Nota: El login exitoso depende de datos semilla en DB,
    # que se pueden crear aquí usando `db_session` antes del TestClient.
