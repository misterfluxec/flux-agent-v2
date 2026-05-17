import asyncio
import logging
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Any

from core.event_bus import EventBus

logger = logging.getLogger(__name__)

class BaseOutboxRelay(ABC):
    """
    Abstract Interface for the Outbox Relay.
    Ensures that event dispatching can be backed by FastAPI Background Tasks, 
    Celery, or Dramatiq without altering the business logic.
    """
    def __init__(self, db_session_maker: Any, event_bus: EventBus):
        self.db_session_maker = db_session_maker
        self.event_bus = event_bus

    @abstractmethod
    async def start(self):
        """Starts the relay process"""
        pass
        
    @abstractmethod
    async def stop(self):
        """Stops the relay process gracefully"""
        pass

    async def _process_batch(self):
        """
        Core logic to acquire a lease on pending events and dispatch them.
        """
        async with self.db_session_maker() as db:
            # 1. Lease Locking: Acquire lock on pending events or expired leases
            # Uses FOR UPDATE SKIP LOCKED if supported, but here we do a simple UPDATE RETURNING
            # for portability and explicitness
            
            worker_id = "fastapi-relay-1" # In a distributed system, generate unique ID per worker instance
            
            lock_query = text("""
                WITH to_process AS (
                    SELECT id FROM outbox_events
                    WHERE status = 'pending' 
                       OR (status = 'processing' AND lease_expires_at < NOW())
                    ORDER BY tenant_id, sequence_number ASC
                    LIMIT 50
                    FOR UPDATE SKIP LOCKED
                )
                UPDATE outbox_events
                SET status = 'processing',
                    locked_by = :worker_id,
                    locked_at = NOW(),
                    lease_expires_at = NOW() + INTERVAL '5 minutes'
                WHERE id IN (SELECT id FROM to_process)
                RETURNING id, tenant_id, event_type, payload_version, payload
            """)
            
            result = await db.execute(lock_query, {"worker_id": worker_id})
            events = result.fetchall()
            await db.commit()
            
            if not events:
                return

            # 2. Dispatch to EventBus
            for evt in events:
                try:
                    # In a real implementation, we would construct the DomainEvent here
                    # and publish to EventBus.
                    logger.info(f"[OutboxRelay] Dispatching event {evt.id} ({evt.event_type})")
                    
                    # Simulate publish
                    # await self.event_bus.publish(...)
                    
                    # 3. Mark as Delivered
                    await db.execute(
                        text("UPDATE outbox_events SET status = 'delivered' WHERE id = :id"),
                        {"id": evt.id}
                    )
                except Exception as e:
                    logger.error(f"[OutboxRelay] Error dispatching event {evt.id}: {e}")
                    await db.execute(
                        text("""
                            UPDATE outbox_events 
                            SET status = 'failed', retry_count = retry_count + 1 
                            WHERE id = :id
                        """),
                        {"id": evt.id}
                    )
            
            await db.commit()

class FastAPIBackgroundRelay(BaseOutboxRelay):
    """
    Development & Beta Implementation using asyncio.
    WARNING: Not suitable for heavy horizontal scaling, use CeleryRelay later.
    """
    def __init__(self, db_session_maker, event_bus: EventBus):
        super().__init__(db_session_maker, event_bus)
        self._task = None
        self._stop_event = asyncio.Event()

    async def start(self):
        logger.info("Starting FastAPIBackgroundRelay...")
        self._stop_event.clear()
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        logger.info("Stopping FastAPIBackgroundRelay...")
        self._stop_event.set()
        if self._task:
            await self._task

    async def _loop(self):
        while not self._stop_event.is_set():
            try:
                await self._process_batch()
                await asyncio.sleep(2) # Polling interval
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in Relay loop: {e}")
                await asyncio.sleep(5)
