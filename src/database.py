# =============================================================================
# FLUXAGENT V2 — CONEXIÓN Y SESIÓN DE BASE DE DATOS
# =============================================================================
# Gestiona el pool de conexiones con SQLAlchemy async.
# Implementa el patrón de sesión por request con soporte para RLS multi-tenant.
# =============================================================================

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from uuid import UUID

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import obtener_config

logger = logging.getLogger(__name__)
config = obtener_config()


# =============================================================================
# MODELOS BASE
# =============================================================================

class BaseModelo(DeclarativeBase):
    """
    Clase base para todos los modelos SQLAlchemy.
    Todos los modelos deben heredar de esta clase.
    """
    pass


# =============================================================================
# ENGINE ASÍNCRONO
# =============================================================================

# Convertir URL de postgres:// a postgresql+asyncpg:// para soporte async
_url_async = config.database_url.replace(
    "postgresql://", "postgresql+asyncpg://"
).replace(
    "postgres://", "postgresql+asyncpg://"
)

engine = create_async_engine(
    _url_async,
    pool_size=config.db_pool_size,
    max_overflow=config.db_max_overflow,
    pool_pre_ping=config.db_pool_pre_ping,
    # Mostrar queries SQL solo en modo desarrollo
    echo=config.es_desarrollo,
)

# Fábrica de sesiones asíncronas
SesionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# =============================================================================
# GESTIÓN DE RLS (Row Level Security)
# =============================================================================

async def configurar_rls(sesion: AsyncSession, tenant_id: UUID) -> None:
    """
    Configura la variable de sesión de PostgreSQL para RLS.

    Debe llamarse al inicio de cada request autenticado.
    Las políticas RLS en init-db.sql leen 'app.current_tenant_id'.

    Args:
        sesion     : Sesión activa de SQLAlchemy
        tenant_id  : UUID del tenant autenticado
    """
    await sesion.execute(
        text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
        {"tenant_id": str(tenant_id)},
    )
    logger.debug(f"RLS configurado para tenant: {tenant_id}")


# =============================================================================
# DEPENDENCY INJECTION (FastAPI)
# =============================================================================

async def obtener_sesion() -> AsyncGenerator[AsyncSession, None]:
    """
    Generador de sesión de base de datos para FastAPI Depends.

    Ciclo de vida:
      1. Abre la sesión y la transacción
      2. Cede el control al endpoint
      3. Hace commit si no hubo error
      4. Hace rollback si ocurrió una excepción
      5. Cierra la sesión al finalizar

    Uso:
        @router.get("/ejemplo")
        async def mi_endpoint(db: AsyncSession = Depends(obtener_sesion)):
            ...
    """
    async with SesionLocal() as sesion:
        try:
            yield sesion
            await sesion.commit()
        except Exception as exc:
            await sesion.rollback()
            logger.error(f"Error en sesión DB, rollback ejecutado: {exc}")
            raise
        finally:
            await sesion.close()


async def obtener_sesion_con_rls(
    tenant_id: UUID,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Variante de obtener_sesion que además configura RLS para el tenant.

    Uso típico en endpoints protegidos donde ya tenemos el tenant_id
    extraído del JWT.

    Args:
        tenant_id : UUID del tenant del usuario autenticado
    """
    async with SesionLocal() as sesion:
        try:
            await configurar_rls(sesion, tenant_id)
            yield sesion
            await sesion.commit()
        except Exception as exc:
            await sesion.rollback()
            logger.error(f"Error en sesión RLS para tenant {tenant_id}: {exc}")
            raise
        finally:
            await sesion.close()


# =============================================================================
# CONTEXT MANAGER ALTERNATIVO (para uso fuera de FastAPI)
# =============================================================================

@asynccontextmanager
async def sesion_db(tenant_id: UUID | None = None) -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager para usar la base de datos fuera del ciclo de FastAPI.
    Útil en scripts de mantenimiento, workers y tareas programadas.

    Ejemplo:
        async with sesion_db(tenant_id=uuid) as db:
            resultado = await db.execute(select(Agent))
    """
    async with SesionLocal() as sesion:
        async with sesion.begin():
            if tenant_id:
                await configurar_rls(sesion, tenant_id)
            try:
                yield sesion
            except Exception:
                await sesion.rollback()
                raise


# =============================================================================
# INICIALIZACIÓN Y SALUD DE LA BASE DE DATOS
# =============================================================================

async def inicializar_db() -> None:
    """
    Verifica la conexión a la base de datos al arrancar la aplicación.
    No crea tablas — eso lo hace init-db.sql en el contenedor de Postgres.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Conexión a PostgreSQL establecida correctamente")
    except Exception as exc:
        logger.critical(f"❌ No se pudo conectar a PostgreSQL: {exc}")
        raise


async def cerrar_db() -> None:
    """Cierra el pool de conexiones. Llamar en el shutdown de la app."""
    await engine.dispose()
    logger.info("🔌 Pool de conexiones PostgreSQL cerrado")
