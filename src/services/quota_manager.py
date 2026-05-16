from uuid import UUID
from datetime import datetime, timedelta
from redis.asyncio import Redis
from domain.usage import QuotaCheckRequest, QuotaCheckResponse, UsageResource, QuotaDefinition, UsageTier

class QuotaManager:
    """
    Verificador de quotas con cache en Redis.
    """
    
    def __init__(self, redis: Redis, db_session_factory):
        self.redis = redis
        self.db_session_factory = db_session_factory
        self.CACHE_TTL_SECONDS = 60
    
    async def check(self, request: QuotaCheckRequest) -> QuotaCheckResponse:
        quota_def = await self._get_quota_definition(request.tenant_id, request.resource)
        
        period_key = self._get_period_key(request.resource, request.tenant_id)
        consumed = float(await self.redis.hget(period_key, "consumed") or 0)
        
        remaining = quota_def.remaining(consumed)
        reset_at = self._calculate_reset_at(quota_def.period)
        
        if request.requested_amount <= remaining:
            return QuotaCheckResponse(
                allowed=True,
                remaining=remaining - request.requested_amount,
                reset_at=reset_at,
                suggested_action="continue"
            )
        
        if quota_def.overage_allowed and quota_def.overage_rate:
            overage_amount = request.requested_amount - remaining
            overage_cost = overage_amount * quota_def.overage_rate
            
            return QuotaCheckResponse(
                allowed=True,
                reason="overage_available",
                remaining=0,
                reset_at=reset_at,
                overage_cost_usd=round(overage_cost, 4),
                suggested_action="continue"
            )
        
        return QuotaCheckResponse(
            allowed=False,
            reason="quota_exceeded",
            remaining=0,
            reset_at=reset_at,
            suggested_action="upgrade_plan"
        )
    
    async def _get_quota_definition(self, tenant_id: UUID, resource: UsageResource) -> QuotaDefinition:
        cache_key = f"quota:def:{tenant_id}:{resource.value}"
        
        cached = await self.redis.get(cache_key)
        if cached:
            return QuotaDefinition.model_validate_json(cached)
        
        # Fallback a un default si no hay DB real por ahora
        quota_def = QuotaDefinition(
            resource=resource,
            plan=UsageTier.PRO,
            limit=1000000, # 1M default limit
            period="month",
            overage_allowed=True,
            overage_rate=0.000002
        )
        
        await self.redis.setex(cache_key, self.CACHE_TTL_SECONDS, quota_def.model_dump_json())
        return quota_def
    
    def _get_period_key(self, resource: UsageResource, tenant_id: UUID) -> str:
        now = datetime.utcnow()
        if resource.period == "month":
            suffix = now.strftime("%Y%m")
        elif resource.period == "day":
            suffix = now.strftime("%Y%m%d")
        else:
            suffix = now.strftime("%Y%m%d%H")
        return f"quota:{tenant_id}:{resource.value}:{suffix}"
    
    def _calculate_reset_at(self, period: str) -> datetime:
        now = datetime.utcnow()
        if period == "hour":
            return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        elif period == "day":
            return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        else:  # month
            if now.month == 12:
                return now.replace(year=now.year+1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            return now.replace(month=now.month+1, day=1, hour=0, minute=0, second=0, microsecond=0)

    async def get_summary(self, tenant_id: str) -> dict:
        from domain.usage import UsageResource
        from datetime import datetime, timezone

        resources_to_check = [
            UsageResource.LLM_TOKENS_INPUT,
            UsageResource.LLM_TOKENS_OUTPUT,
            UsageResource.LLM_REQUESTS,
            UsageResource.TOOL_EXECUTIONS,
            UsageResource.EVENT_BUS_MESSAGES,
        ]

        raw: dict = {}
        for resource in resources_to_check:
            period_key = self._get_period_key(
                resource, tenant_id
            )
            val = await self.redis.get(period_key)
            raw[resource] = float(val) if val else 0.0

        tokens_consumed = (
            raw[UsageResource.LLM_TOKENS_INPUT]
            + raw[UsageResource.LLM_TOKENS_OUTPUT]
        )

        quota_def = await self._get_quota_definition(
            tenant_id, UsageResource.LLM_TOKENS_INPUT
        )
        token_limit = (
            quota_def.limit if quota_def else 1_000_000
        )

        pct = (
            round((tokens_consumed / token_limit) * 100, 1)
            if token_limit > 0
            else 0.0
        )

        now = datetime.now(timezone.utc)
        reset_at = now.replace(
            day=1, hour=0, minute=0,
            second=0, microsecond=0,
        )
        if reset_at.month == 12:
            reset_at = reset_at.replace(
                year=reset_at.year + 1, month=1
            )
        else:
            reset_at = reset_at.replace(
                month=reset_at.month + 1
            )

        return {
            "tokens": {
                "consumed": tokens_consumed,
                "limit": token_limit,
                "percentage": pct,
                "unlimited": token_limit == -1,
            },
            "requests": {
                "llm": raw[UsageResource.LLM_REQUESTS],
                "tools": raw[UsageResource.TOOL_EXECUTIONS],
                "eventbus": raw[
                    UsageResource.EVENT_BUS_MESSAGES
                ],
            },
            "reset_at": reset_at.isoformat(),
            "period": "month",
        }
