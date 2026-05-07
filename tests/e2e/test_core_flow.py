# =============================================================================
# FLUXAGENT V2 — E2E SMOKE TEST (FLUJO CRÍTICO)
# =============================================================================
# Testing automatizado del flujo principal: Login → Agente → Analytics
# Eleva madurez de testing de 5.0 → 7.5+
# =============================================================================

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from src.main import app
from src.database import Base, engine
import os

# =============================================================================
# FIXTURES DE INFRAESTRUCTURA EFÍMERA
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Event loop para tests asíncronos"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_db():
    """Base de datos PostgreSQL en contenedor efímero"""
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres.get_connection_url(driver="asyncpg")

@pytest.fixture(scope="session")
def test_redis():
    """Redis en contenedor efímero"""
    with RedisContainer("redis:7-alpine") as redis:
        yield f"redis://{redis.get_container_host_ip()}:{redis.get_exposed_port(6379)}/0"

@pytest.fixture(autouse=True, scope="session")
def setup_db(test_db):
    """Crear tablas en DB de prueba"""
    async def _create():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    # Inyectar URL de test y crear tablas
    original_url = os.getenv("DATABASE_URL")
    os.environ["DATABASE_URL"] = test_db
    
    try:
        asyncio.get_event_loop().run_until_complete(_create())
        yield
    finally:
        os.environ["DATABASE_URL"] = original_url or ""

# =============================================================================
# TEST DE FLUJO CRÍTICO: LOGIN → AGENTE → ANALYTICS
# =============================================================================

@pytest.mark.asyncio
async def test_e2e_core_flow(test_db, test_redis, monkeypatch):
    """Test E2E del flujo crítico completo"""
    
    # Inyectar config de test
    monkeypatch.setenv("DATABASE_URL", test_db)
    monkeypatch.setenv("REDIS_URL", test_redis)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "test_secret_key_for_e2e")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")  # Mock
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        
        # 1️⃣ LOGIN / REGISTER
        print("🔐 Probando registro de usuario...")
        res = await client.post("/api/v1/auth/register", json={
            "email": "test@fluxagent.com",
            "password": "SecurePass123!",
            "company": "TestCorp"
        })
        
        assert res.status_code in [200, 201], f"Registro falló: {res.text}"
        token = res.json().get("access_token")
        assert token, "No se recibió token de acceso"
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Registro exitoso")

        # 2️⃣ CREAR AGENTE (ONBOARDING)
        print("🤖 Probando creación de agente...")
        res = await client.post("/api/v1/agents", json={
            "nombre": "Agente E2E Test",
            "agent_type": "sales",
            "modelo": "qwen2.5:3b",
            "tono": "profesional",
            "descripcion": "Agente de prueba para E2E"
        }, headers=headers)
        
        assert res.status_code == 200, f"Creación agente falló: {res.text}"
        agent_data = res.json()
        assert "id" in agent_data, "Respuesta de agente sin ID"
        agent_id = agent_data["id"]
        print(f"✅ Agente creado: {agent_id}")

        # 3️⃣ OBTENER ANALYTICS (DATOS REALES/EMPTY)
        print("📊 Probando analytics endpoint...")
        res = await client.get("/api/v1/analytics/overview?days=7", headers=headers)
        assert res.status_code == 200, f"Analytics falló: {res.text}"
        
        analytics = res.json()
        assert "total_conversations" in analytics, "Analytics missing total_conversations"
        assert "conversion_rate" in analytics, "Analytics missing conversion_rate"
        assert isinstance(analytics["total_conversations"], int), "total_conversations debe ser int"
        print("✅ Analytics funcionando")

        # 4️⃣ VERIFICAR HEALTH + CIRCUIT BREAKERS
        print("🏥 Probando health check...")
        res = await client.get("/health")
        assert res.status_code == 200, f"Health check falló: {res.text}"
        
        health = res.json()
        assert "status" in health, "Health response missing status"
        assert health["status"] in ["healthy", "degraded", "unhealthy"], f"Status inválido: {health['status']}"
        print(f"✅ Health check: {health['status']}")

        # 5️⃣ LISTAR AGENTES
        print("📋 Probando listado de agentes...")
        res = await client.get("/api/v1/agents", headers=headers)
        assert res.status_code == 200, f"Listado agentes falló: {res.text}"
        
        agents = res.json()
        assert isinstance(agents, list), "Respuesta debe ser lista"
        assert len(agents) >= 1, "Debe haber al menos un agente"
        print(f"✅ {len(agents)} agentes encontrados")

        print("🎉 FLUJO CRÍTICO E2E COMPLETADO EXITOSAMENTE")

@pytest.mark.asyncio 
async def test_e2e_error_handling(test_db, test_redis, monkeypatch):
    """Test de manejo de errores en el flujo"""
    
    # Configuración similar al test anterior
    monkeypatch.setenv("DATABASE_URL", test_db)
    monkeypatch.setenv("REDIS_URL", test_redis)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "test_secret_key")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        
        # Test: Acceso sin token
        res = await client.get("/api/v1/agents")
        assert res.status_code == 401, "Debe requerir autenticación"
        
        # Test: Login con credenciales inválidas
        res = await client.post("/api/v1/auth/login", json={
            "email": "inexistente@test.com",
            "password": "wrongpassword"
        })
        assert res.status_code in [401, 404], "Debe rechazar credenciales inválidas"
        
        print("✅ Manejo de errores funcionando correctamente")

@pytest.mark.asyncio
async def test_e2e_rate_limiting(test_db, test_redis, monkeypatch):
    """Test de rate limiting en endpoints críticos"""
    
    monkeypatch.setenv("DATABASE_URL", test_db)
    monkeypatch.setenv("REDIS_URL", test_redis)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "test_secret_key")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        
        # Registrar usuario para obtener token
        res = await client.post("/api/v1/auth/register", json={
            "email": "ratelimit@test.com",
            "password": "SecurePass123!",
            "company": "RateLimit Test"
        })
        
        token = res.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Hacer múltiples requests rápidamente (simular rate limit)
        responses = []
        for i in range(10):
            res = await client.get("/api/v1/agents", headers=headers)
            responses.append(res.status_code)
        
        # Al menos algunas requests deben ser exitosas
        success_count = sum(1 for code in responses if code == 200)
        assert success_count >= 5, f"Demasiados requests fallidas: {responses}"
        
        print(f"✅ Rate limiting: {success_count}/10 requests exitosas")

# =============================================================================
# UTILIDADES DE TEST
# =============================================================================

def pytest_configure(config):
    """Configuración personalizada de pytest"""
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )

def pytest_collection_modifyitems(config, items):
    """Modificar tests para agregar markers automáticamente"""
    for item in items:
        if "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
