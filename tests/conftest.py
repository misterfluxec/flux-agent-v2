# =============================================================================
# FLUXAGENT V2 — PYTEST CONFIGURATION WITH TESTCONTAINERS
# =============================================================================
# Fixtures globales para testing con containers Docker aislados
# Base de datos PostgreSQL y Redis temporales para cada sesión
# =============================================================================

import pytest
import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock

from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

from database import Base
from main import app

# =============================================================================
# FIXTURES GLOBALES DE CONTAINERS
# =============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Crea un event loop para测试 asíncronas"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Container PostgreSQL para testing"""
    with PostgresContainer("postgres:15-alpine") as postgres:
        # Esperar a que esté listo
        postgres.get_connection_url()
        yield postgres

@pytest.fixture(scope="session")
def redis_container() -> Generator[RedisContainer, None, None]:
    """Container Redis para testing"""
    with RedisContainer("redis:7-alpine") as redis:
        # Esperar a que esté listo
        redis.get_container_host_ip()
        yield redis

@pytest.fixture(scope="session")
async def db_url(postgres_container: PostgresContainer) -> str:
    """URL de base de datos para testing"""
    return postgres_container.get_connection_url(driver="asyncpg")

@pytest.fixture(scope="session")
async def redis_url(redis_container: RedisContainer) -> str:
    """URL de Redis para testing"""
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    return f"redis://{host}:{port}"

# =============================================================================
# FIXTURES DE BASE DE DATOS
# =============================================================================

@pytest.fixture(scope="session")
async def setup_database(db_url: str) -> AsyncGenerator[str, None]:
    """Configura base de datos para testing"""
    engine = create_async_engine(db_url, echo=False)
    
    # Crear todas las tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield db_url
    
    # Limpiar después de las pruebas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(setup_database: str):
    """Sesión de base de datos para cada test"""
    engine = create_async_engine(setup_database, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_factory() as session:
        yield session
    
    await engine.dispose()

# =============================================================================
# FIXTURES DE CLIENTE HTTP
# =============================================================================

@pytest.fixture(scope="function")
async def async_client(setup_database: str, redis_url: str):
    """Cliente HTTP asíncrono para testing"""
    # Sobreescribir variables de entorno para modo test
    os.environ["DATABASE_URL"] = setup_database
    os.environ["REDIS_URL"] = redis_url
    os.environ["APP_ENV"] = "testing"
    os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"
    
    # Crear cliente con transporte ASGI
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as client:
        yield client

@pytest.fixture(scope="function")
async def auth_headers(async_client: AsyncClient, db_session):
    """Headers de autenticación para testing"""
    # Crear usuario de prueba en la base de datos
    test_user_data = {
        "id": "test-user-id",
        "email": "test@fluxagent.com",
        "password": "$2b$12$hashedpassword",  # En producción usar hash real
        "rol": "admin",
        "tenant_id": "test-tenant-id",
        "estado": "activo"
    }
    
    # Insertar usuario de prueba
    insert_query = text("""
        INSERT INTO usuarios (id, email, password, rol, tenant_id, estado, creado_en)
        VALUES (:id, :email, :password, :rol, :tenant_id, :estado, NOW())
        ON CONFLICT (id) DO UPDATE SET
        email = EXCLUDED.email,
        rol = EXCLUDED.rol,
        tenant_id = EXCLUDED.tenant_id,
        estado = EXCLUDED.estado,
        actualizado_en = NOW()
    """)
    
    await db_session.execute(insert_query, test_user_data)
    await db_session.commit()
    
    # Crear tenant de prueba
    test_tenant_data = {
        "id": "test-tenant-id",
        "nombre": "Test Tenant",
        "plan": "pro",
        "estado": "activo"
    }
    
    insert_tenant_query = text("""
        INSERT INTO tenants (id, nombre, plan, estado, creado_en)
        VALUES (:id, :nombre, :plan, :estado, NOW())
        ON CONFLICT (id) DO UPDATE SET
        nombre = EXCLUDED.nombre,
        plan = EXCLUDED.plan,
        estado = EXCLUDED.estado,
        actualizado_en = NOW()
    """)
    
    await db_session.execute(insert_tenant_query, test_tenant_data)
    await db_session.commit()
    
    # Generar token JWT (simulado)
    import jwt
    from datetime import datetime, timedelta
    
    token_payload = {
        "sub": test_user_data["id"],
        "email": test_user_data["email"],
        "rol": test_user_data["rol"],
        "tenant_id": test_user_data["tenant_id"],
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(token_payload, "test-secret-key-for-testing-only", algorithm="HS256")
    
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
async def test_tenant(async_client: AsyncClient, db_session):
    """Tenant de prueba para testing"""
    tenant_data = {
        "id": "test-tenant-2",
        "nombre": "Another Test Tenant",
        "plan": "basic",
        "estado": "activo"
    }
    
    insert_query = text("""
        INSERT INTO tenants (id, nombre, plan, estado, creado_en)
        VALUES (:id, :nombre, :plan, :estado, NOW())
        ON CONFLICT (id) DO UPDATE SET
        nombre = EXCLUDED.nombre,
        plan = EXCLUDED.plan,
        estado = EXCLUDED.estado,
        actualizado_en = NOW()
    """)
    
    await db_session.execute(insert_query, tenant_data)
    await db_session.commit()
    
    return tenant_data

# =============================================================================
# FIXTURES DE MOCKS Y UTILIDADES
# =============================================================================

@pytest.fixture(scope="function")
def mock_ollama():
    """Mock para servicio Ollama"""
    from unittest.mock import AsyncMock
    
    mock = AsyncMock()
    mock.return_value = {
        "response": "Test response from Ollama",
        "done": True,
        "context": []
    }
    
    return mock

@pytest.fixture(scope="function")
def mock_redis():
    """Mock para cliente Redis"""
    from unittest.mock import AsyncMock
    
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.ping.return_value = True
    
    return mock

@pytest.fixture(scope="function")
def mock_whatsapp():
    """Mock para servicio WhatsApp"""
    from unittest.mock import AsyncMock
    
    mock = AsyncMock()
    mock.return_value = {
        "message_id": "test-message-id",
        "status": "sent"
    }
    
    return mock

@pytest.fixture(scope="function")
async def sample_agent_data():
    """Datos de agente de prueba"""
    return {
        "nombre": "Agente de Prueba",
        "area": "Ventas",
        "descripcion": "Agente para testing automatizado",
        "genero": "neutro",
        "humor": "profesional",
        "personalidad": "Amigable y servicial",
        "idioma": "español",
        "tono": "profesional",
        "canales": ["web_chat"],
        "tipo_negocio": "Ventas online",
        "objetivo": "Asistir clientes en compras",
        "instrucciones": "Sé amable pero profesional",
        "modelo": "qwen2.5:3b",
        "temperatura": 0.7,
        "max_tokens": 1000,
        "agent_type": "sales",
        "especialidad": "Ventas de productos",
        "system_prompt": "Eres un asistente de ventas experto",
        "script_ventas": "¡Hola! Bienvenido a nuestra tienda. ¿En qué puedo ayudarte hoy?",
        "estado": "activo"
    }

@pytest.fixture(scope="function")
async def sample_conversation_data(test_tenant):
    """Datos de conversación de prueba"""
    return {
        "id": "test-conversation-id",
        "tenant_id": test_tenant["id"],
        "cliente_id": "test-client-id",
        "canal": "web_chat",
        "estado": "activa",
        "agente_id": "test-agent-id",
        "iniciada_en": "2024-01-01T00:00:00Z"
    }

# =============================================================================
# UTILIDADES DE TESTING
# =============================================================================

@pytest.fixture(scope="function")
def override_env_vars():
    """Context manager para sobreescribir variables de entorno"""
    original_env = {}
    
    def set_env(key: str, value: str):
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    def restore_env():
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    
    return set_env, restore_env

@pytest.fixture(scope="function")
async def clean_redis(redis_url: str):
    """Limpia Redis antes y después de cada test"""
    import redis.asyncio as aioredis
    
    redis_client = aioredis.from_url(redis_url)
    await redis_client.flushall()
    yield redis_client
    await redis_client.aclose()

# =============================================================================
# CONFIGURACIÓN DE PYTEST
# =============================================================================

def pytest_configure(config):
    """Configuración personalizada de pytest"""
    config.addinivalue_line(
        "markers", 
        "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", 
        "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", 
        "e2e: mark test as end-to-end test"
    )

def pytest_collection_modifyitems(config, items):
    """Modifica la colección de tests"""
    for item in items:
        # Agregar marker asyncio a todas las funciones asíncronas
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
