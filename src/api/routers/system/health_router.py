from __future__ import annotations
import time
import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_usuario_actual, PayloadToken
from database import get_db

logger = logging.getLogger("flux.health")
router = APIRouter(tags=["Health"])


# ── Liveness (sin auth — para Docker/K8s) ─────────────
@router.get("/health/live", include_in_schema=False)
async def liveness():
    """El proceso está vivo. Docker usa este endpoint."""
    return {"status": "alive"}


# ── Readiness (sin auth — para Docker/K8s) ────────────
@router.get("/health/ready", include_in_schema=False)
async def readiness(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Todas las dependencias críticas están disponibles.
    Retorna 200 solo si DB + Redis están operativos.
    """
    checks: dict[str, Any] = {}
    all_ok = True

    # ── PostgreSQL ─────────────────────────────────────
    t0 = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        checks["postgres"] = {
            "status": "ok",
            "latency_ms": round(
                (time.perf_counter() - t0) * 1000, 1
            ),
        }
    except Exception as exc:
        checks["postgres"] = {
            "status": "error", "error": str(exc)
        }
        all_ok = False

    # ── Redis ──────────────────────────────────────────
    t0 = time.perf_counter()
    try:
        redis = request.app.state.redis
        await redis.ping()
        checks["redis"] = {
            "status": "ok",
            "latency_ms": round(
                (time.perf_counter() - t0) * 1000, 1
            ),
        }
    except Exception as exc:
        checks["redis"] = {
            "status": "error", "error": str(exc)
        }
        all_ok = False

    # ── Ollama (no bloqueante — degraded si falla) ─────
    t0 = time.perf_counter()
    try:
        from config import obtener_config
        cfg = obtener_config()
        base = getattr(
            cfg, "ollama_base_url", "http://localhost:11434"
        )
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{base}/api/tags")
            ollama_ok = r.status_code == 200
        checks["ollama"] = {
            "status": "ok" if ollama_ok else "degraded",
            "latency_ms": round(
                (time.perf_counter() - t0) * 1000, 1
            ),
        }
    except Exception as exc:
        checks["ollama"] = {
            "status": "degraded", "error": str(exc)
        }

    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={
            "status": "ready" if all_ok else "not_ready",
            "checks": checks,
        },
    )


# ── Operational (con auth — para el dashboard) ────────
@router.get(
    "/api/v1/health/operational",
    tags=["Health"],
)
async def operational_health(
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario: PayloadToken = Depends(get_usuario_actual),
):
    """Salud operacional del negocio. Requiere auth."""
    from services.health.operational_health import (
        OperationalHealthEngine,
    )
    # Firma real: __init__(redis_client) + get_health_report(db, tenant_id)
    engine = OperationalHealthEngine(
        redis_client=request.app.state.redis,
    )
    try:
        report = await engine.get_health_report(
            db=db,
            tenant_id=str(usuario.tenant_id),
        )
        return report
    except Exception as exc:
        logger.warning(
            "operational_health_failed",
            extra={"error": str(exc)},
        )
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "error": str(exc)},
        )
