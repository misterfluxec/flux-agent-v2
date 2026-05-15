from __future__ import annotations
import logging
from functools import wraps
from typing import Callable

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from core.plan_manager import PlanManager

logger = logging.getLogger("flux.plan_limits")

# PLAN_LIMITS conservado como fallback offline únicamente
PLAN_LIMITS_FALLBACK = {
    "free":       {"max_agents": 1,  "max_active_quotes": 5,
                   "monthly_interactions": 100,
                   "allowed_workflows": ["cart_recovery"]},
    "starter":    {"max_agents": 1,  "max_active_quotes": 5,
                   "monthly_interactions": 100,
                   "allowed_workflows": ["cart_recovery"]},
    "pro":        {"max_agents": 3,  "max_active_quotes": 50,
                   "monthly_interactions": 1000,
                   "allowed_workflows": [
                       "cart_recovery",
                       "appointment_reminder_24h",
                       "quote_followup_48h"
                   ]},
    "enterprise": {"max_agents": -1, "max_active_quotes": -1,
                   "monthly_interactions": -1,
                   "allowed_workflows": None},
}

async def get_plan_limits(
    plan_key: str,
    redis: Redis | None = None,
    db: AsyncSession | None = None,
) -> dict:
    if redis and db:
        try:
            manager = PlanManager(redis=redis, db=db)
            features = await manager.get_plan(plan_key)
            return features.__dict__
        except Exception as exc:
            logger.warning("plan_manager_fallback",
                          extra={"plan": plan_key,
                                 "error": str(exc)})
    return PLAN_LIMITS_FALLBACK.get(
        plan_key, PLAN_LIMITS_FALLBACK["free"]
    )

async def get_current_agents_count(
    tenant_id: str, db: AsyncSession
) -> int:
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT COUNT(*) FROM agents "
             "WHERE tenant_id = :tid AND status != 'deleted'"),
        {"tid": tenant_id},
    )
    return result.scalar() or 0

def check_plan_limits(
    plan_key_extractor: Callable[..., str] = lambda kw: "free"
):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            plan = plan_key_extractor(kwargs)
            redis = kwargs.get("redis")
            db = kwargs.get("db")
            limits = await get_plan_limits(plan, redis, db)

            tenant_id = None
            if "usuario" in kwargs:
                tenant_id = kwargs["usuario"].tenant_id
            elif "tenant_id" in kwargs:
                tenant_id = kwargs["tenant_id"]

            if ("create_agent" in func.__name__
                    and limits.get("max_agents", 1) != -1):
                if tenant_id and db:
                    count = await get_current_agents_count(
                        tenant_id, db
                    )
                    if count >= limits["max_agents"]:
                        raise HTTPException(
                            403,
                            f"Límite de {limits['max_agents']} "
                            "agentes alcanzado. Mejora tu plan."
                        )

            if ("create_workflow" in func.__name__
                    or "enable_workflow" in func.__name__):
                wf = limits.get("allowed_workflows")
                if wf is not None:
                    wf_name = kwargs.get("workflow_name")
                    if wf_name and wf_name not in wf:
                        raise HTTPException(
                            403,
                            f"El workflow '{wf_name}' "
                            "requiere plan Pro o Enterprise."
                        )

            return await func(*args, **kwargs)
        return wrapper
    return decorator
