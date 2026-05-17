"""
Core EventBus — FluxAgent V2
Async event publishing with optional Redis pub/sub backend.
"""
import logging
from typing import Any, Dict, Optional, Callable, List
import asyncio
import json

from .types import Event, EventType

logger = logging.getLogger(__name__)


class EventBus:
    """In-process async event bus for FluxAgent V2."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._redis = None

    async def setup(self, redis_url: Optional[str] = None):
        """Initialize with optional Redis backend."""
        if redis_url:
            try:
                import aioredis
                self._redis = await aioredis.from_url(redis_url)
                logger.info("EventBus: Redis backend connected")
            except Exception as e:
                logger.warning(f"EventBus: Redis unavailable, using in-memory: {e}")

    async def publish(self, event: Event):
        """Publish an event to all registered handlers."""
        event_key = event.type.value if isinstance(event.type, EventType) else str(event.type)
        handlers = self._handlers.get(event_key, []) + self._handlers.get("*", [])

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"EventBus handler error [{event_key}]: {e}")

        # Optionally push to Redis for multi-process consumers
        if self._redis and event.tenant_id:
            try:
                channel = event.channel or f"tenant:{event.tenant_id}"
                await self._redis.publish(channel, json.dumps(event.to_dict()))
            except Exception as e:
                logger.debug(f"EventBus: Redis publish failed: {e}")

    def subscribe(self, event_type: str, handler: Callable):
        """Register a handler for an event type."""
        self._handlers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: str, handler: Callable):
        """Remove a registered handler."""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]

    async def close(self):
        if self._redis:
            await self._redis.close()
            logger.info("EventBus: Redis connection closed")


# Singleton instance for the application
event_bus = EventBus()
