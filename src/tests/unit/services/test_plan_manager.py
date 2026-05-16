import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from core.plan_manager import PlanManager, PlanFeatures

@pytest.fixture
def manager(mock_redis):
    db = AsyncMock()
    return PlanManager(redis=mock_redis, db=db)

@pytest.mark.asyncio
async def test_get_plan_from_cache(manager, mock_redis):
    features = PlanFeatures(
        plan_key="starter", display_name="Starter",
        price_usd=29.0, max_agents=1,
        max_active_quotes=5, monthly_interactions=100,
        allowed_workflows=["cart_recovery"],
        max_messages_month=2000,
        requests_per_hour=500, messages_per_minute=50,
        ai_requests_per_minute=25, file_uploads_per_hour=20,
    )
    mock_redis.get = AsyncMock(
        return_value=json.dumps(features.__dict__)
    )
    result = await manager.get_plan("starter")
    assert result.plan_key == "starter"
    assert result.max_agents == 1

@pytest.mark.asyncio
async def test_unlimited_plan(manager, mock_redis):
    mock_redis.get = AsyncMock(return_value=None)
    row = MagicMock()
    row.plan_key = "enterprise"
    row.display_name = "Enterprise"
    row.price_usd = 299
    row.max_agents = -1
    row.max_active_quotes = -1
    row.monthly_interactions = -1
    row.allowed_workflows = None
    row.max_messages_month = 100000
    row.requests_per_hour = 10000
    row.messages_per_minute = 1000
    row.ai_requests_per_minute = 500
    row.file_uploads_per_hour = 500
    result_mock = MagicMock()
    result_mock.fetchone = MagicMock(return_value=row)
    manager.db.execute = AsyncMock(return_value=result_mock)
    mock_redis.setex = AsyncMock()

    plan = await manager.get_plan("enterprise")
    assert plan.is_unlimited("max_agents") is True
    assert plan.allows_workflow("cualquier_workflow") is True
