import os
import sys

# 1. Levantar y configurar Testcontainers antes de importar la app
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

pg_container = PostgresContainer("pgvector/pgvector:pg16")
pg_container.start()
pg_url = pg_container.get_connection_url().replace("postgresql+psycopg2://", "postgresql+asyncpg://").replace("postgresql://", "postgresql+asyncpg://")
os.environ["DATABASE_URL"] = pg_url

rd_container = RedisContainer("redis:7-alpine")
rd_container.start()
rd_host = rd_container.get_container_host_ip()
rd_port = rd_container.get_exposed_port(6379)
rd_url = f"redis://{rd_host}:{rd_port}/0"
os.environ["REDIS_URL"] = rd_url
os.environ["REDIS_HOST"] = rd_host
os.environ["REDIS_PORT"] = str(rd_port)
os.environ["REDIS_PASSWORD"] = ""
os.environ["EVOLUTION_WEBHOOK_SECRET"] = "test_webhook_secret"

# 2. Importaciones de testing estándar
import pytest
import pytest_asyncio
import asyncio
import httpx
from typing import AsyncGenerator, Generator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from main import app
from database import BaseModelo as Base, obtener_sesion
from core.dependencies import get_redis

@pytest.fixture(scope="session")
def event_loop():
    """Crea una instancia única del event loop para toda la sesión de pruebas."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# Los fixtures simplemente retornan los contenedores ya iniciados
@pytest.fixture(scope="session")
def postgres_container():
    yield pg_container

@pytest.fixture(scope="session")
def redis_container():
    yield rd_container

@pytest_asyncio.fixture
async def db_engine(postgres_container):
    engine = create_async_engine(pg_url, echo=False)
    
    # Leer init-db.sql para crear tablas, tipos y triggers
    init_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "init-db.sql")
    if os.path.exists(init_db_path):
        with open(init_db_path, "r", encoding="utf-8") as f:
            sql_content = f.read()
            db_name = engine.url.database
            sql_content = sql_content.replace("DATABASE fluxagent_v2", f"DATABASE {db_name}")
    else:
        sql_content = ""

    # Definición de fn_login_usuario
    fn_login_sql = """
CREATE OR REPLACE FUNCTION fn_login_usuario(p_email VARCHAR)
RETURNS TABLE(
    id UUID,
    tenant_id UUID,
    password_hash VARCHAR,
    name VARCHAR,
    role VARCHAR,
    plan VARCHAR,
    company_name VARCHAR,
    estado_tenant VARCHAR
) SECURITY DEFINER AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id, 
        u.tenant_id, 
        u.password_hash, 
        u.nombre::VARCHAR AS name, 
        u.rol::VARCHAR AS role, 
        t.plan::VARCHAR AS plan, 
        t.nombre_empresa::VARCHAR AS company_name, 
        t.estado::VARCHAR AS estado_tenant
    FROM usuarios u
    JOIN tenants t ON u.tenant_id = t.id
    WHERE LOWER(u.email) = LOWER(p_email) AND u.estado = 'activo';
END;
$$ LANGUAGE plpgsql;
"""

    async with engine.begin() as conn:
        raw_conn = await conn.get_raw_connection()
        driver_conn = raw_conn.driver_connection
        await driver_conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO public;")
        if sql_content:
            await driver_conn.execute(sql_content)
        else:
            await conn.run_sync(Base.metadata.create_all)
        
        await driver_conn.execute(fn_login_sql)

    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture
async def redis_client(redis_container):
    import redis.asyncio as redis
    client = redis.Redis(host=rd_host, port=rd_port, decode_responses=True)
    yield client
    await client.aclose()

@pytest_asyncio.fixture
async def api_client(db_engine, redis_client):
    # Override app dependencies for testing
    async def override_obtener_sesion():
        async_session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[obtener_sesion] = override_obtener_sesion
    app.dependency_overrides[get_redis] = lambda: redis_client
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

# Limpieza final al terminar la sesión de pruebas
def pytest_sessionfinish(session, exitstatus):
    pg_container.stop()
    rd_container.stop()
