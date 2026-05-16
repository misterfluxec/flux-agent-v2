import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_redis():
    """Fixture para simular Redis en tests unitarios."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    return redis
