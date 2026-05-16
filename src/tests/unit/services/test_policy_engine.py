import pytest
from unittest.mock import AsyncMock, MagicMock
from services.policy_engine import PolicyEngine, PolicyRule
from domain.policies import PolicyAction

@pytest.fixture
def engine(mock_redis):
    db = AsyncMock()
    return PolicyEngine(redis=mock_redis, db=db)

@pytest.mark.asyncio
async def test_evaluate_default_allow_when_no_rules(engine):
    engine._cache = {}
    db_mock = AsyncMock()
    result_mock = MagicMock()
    result_mock.fetchall.return_value = []
    db_mock.execute = AsyncMock(return_value=result_mock)
    engine.db = db_mock

    from domain.policies import (
        PolicyEvaluationRequest, PolicyAction
    )
    import uuid
    req = PolicyEvaluationRequest(
        tenant_id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        tool_name="send_message",
        input_payload={"msg": "hello"},
        context={},
    )
    output = await engine.evaluate_tool_execution(req)
    assert output.allowed is True
    assert output.final_decision in ("allowed", "modified")

@pytest.mark.asyncio
async def test_cache_populated_after_first_call(engine):
    engine._cache = {}
    db_mock = AsyncMock()
    result_mock = MagicMock()
    result_mock.fetchall.return_value = []
    db_mock.execute = AsyncMock(return_value=result_mock)
    engine.db = db_mock

    key = "tenant-123:send_message"
    result_mock.fetchall.return_value = [
        MagicMock(priority=1, action=PolicyAction.ALLOW)
    ]
    await engine._get_applicable_rules("tenant-123", "send_message")
    assert key in engine._cache
