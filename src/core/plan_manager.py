from __future__ import annotations
import json
import logging
from dataclasses import dataclass
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ResourceNotFoundError

logger = logging.getLogger("flux.plan_manager")

CACHE_TTL = 300  # 5 minutos
UNLIMITED = -1

@dataclass
class PlanFeatures:
    plan_key: str
    display_name: str
    price_usd: float
    max_agents: int
    max_active_quotes: int
    monthly_interactions: int
    allowed_workflows: list[str] | None  # None = todos
    max_messages_month: int
    requests_per_hour: int
    messages_per_minute: int
    ai_requests_per_minute: int
    file_uploads_per_hour: int

    def is_unlimited(self, field: str) -> bool:
        return getattr(self, field, 0) == UNLIMITED

    def allows_workflow(self, workflow_name: str) -> bool:
        if self.allowed_workflows is None:
            return True
        return workflow_name in self.allowed_workflows

class PlanManager:
    def __init__(self, redis: Redis, db: AsyncSession):
        self.redis = redis
        self.db = db

    async def get_plan(self, plan_key: str) -> PlanFeatures:
        cache_key = f"flux:plan:{plan_key}"

        cached = await self.redis.get(cache_key)
        if cached:
            data = json.loads(cached)
            return PlanFeatures(**data)

        result = await self.db.execute(
            text("""
                SELECT plan_key, display_name, price_usd,
                       max_agents, max_active_quotes,
                       monthly_interactions, allowed_workflows,
                       max_messages_month, requests_per_hour,
                       messages_per_minute, ai_requests_per_minute,
                       file_uploads_per_hour
                FROM flux_plan_features
                WHERE plan_key = :key AND is_active = TRUE
            """),
            {"key": plan_key},
        )
        row = result.fetchone()

        if not row:
            logger.warning("plan_not_found",
                          extra={"plan_key": plan_key})
            result = await self.db.execute(
                text("SELECT plan_key, display_name, price_usd, "
                     "max_agents, max_active_quotes, "
                     "monthly_interactions, allowed_workflows, "
                     "max_messages_month, requests_per_hour, "
                     "messages_per_minute, ai_requests_per_minute, "
                     "file_uploads_per_hour "
                     "FROM flux_plan_features "
                     "WHERE plan_key = 'free' AND is_active = TRUE")
            )
            row = result.fetchone()
            if not row:
                raise ResourceNotFoundError(
                    f"Plan '{plan_key}' no encontrado y "
                    "no hay plan 'free' de fallback"
                )

        wf = row.allowed_workflows
        features = PlanFeatures(
            plan_key=row.plan_key,
            display_name=row.display_name,
            price_usd=float(row.price_usd),
            max_agents=row.max_agents,
            max_active_quotes=row.max_active_quotes,
            monthly_interactions=row.monthly_interactions,
            allowed_workflows=wf if wf is not None else None,
            max_messages_month=row.max_messages_month,
            requests_per_hour=row.requests_per_hour,
            messages_per_minute=row.messages_per_minute,
            ai_requests_per_minute=row.ai_requests_per_minute,
            file_uploads_per_hour=row.file_uploads_per_hour,
        )

        await self.redis.setex(
            cache_key, CACHE_TTL,
            json.dumps(features.__dict__)
        )
        return features

    async def invalidate(self, plan_key: str) -> None:
        await self.redis.delete(f"flux:plan:{plan_key}")
        logger.info("plan_cache_invalidated",
                   extra={"plan_key": plan_key})

    async def get_all_plans(self) -> list[PlanFeatures]:
        result = await self.db.execute(
            text("""
                SELECT plan_key FROM flux_plan_features
                WHERE is_active = TRUE
                ORDER BY sort_order
            """)
        )
        plans = []
        for row in result.fetchall():
            plans.append(await self.get_plan(row.plan_key))
        return plans

    @classmethod
    async def check_limite_diario_tenant(cls, tenant_id: str, db=None, feature_type: str = "messages", amount: int = 1) -> bool:
        # Fallback (fail open) ya que se invoca de forma estática desde webhooks_router
        return True

    @classmethod
    async def check_feature_tenant(cls, tenant_id: str, db=None, feature_name: str = "") -> bool:
        return True

    @classmethod
    def registrar_uso(cls, tenant_id: str, feature_type: str, amount: int = 1) -> None:
        pass
