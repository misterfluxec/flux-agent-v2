import pytest
from unittest.mock import AsyncMock
from services.operations.hitl_engine import HITLEngine

@pytest.fixture
def engine():
    return HITLEngine(
        db=AsyncMock(),
        tenant_id="tenant-test",
        user_id="user-test",
        user_roles=["sysadmin"],
        event_bus=None,
    )

@pytest.mark.asyncio
async def test_sysadmin_can_execute_any_action(engine):
    result = await engine.execute_action(
        "ESCALATE_AGENT",
        {"conversation_id": "conv-123"},
    )
    assert result["status"] == "success"
    assert "conversation_id" in result["result"]

@pytest.mark.asyncio
async def test_unknown_role_denied(engine):
    engine.user_roles = ["viewer"]
    result = await engine.execute_action(
        "EXPORT_CUSTOMER_DATA", {}
    )
    assert result["status"] == "error"
    assert "Gobernanza" in result["message"]

@pytest.mark.asyncio
async def test_requires_approval_returns_pending():
    eng = HITLEngine(
        db=AsyncMock(),
        tenant_id="tenant-test",
        user_id="user-test",
        user_roles=["operations_admin"],
        event_bus=None,
    )
    result = await eng.execute_action(
        "ISSUE_REFUND", {"amount": 100}
    )
    assert result["status"] == "pending_approval"
