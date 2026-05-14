import asyncio
import logging
from typing import Set

logger = logging.getLogger(__name__)

class DLQRetryWorker:
    def __init__(self, interval_seconds: int = 15):
        self.interval = interval_seconds
        self._running = False
        
    async def start(self):
        self._running = True
        logger.info("[Background] Started DLQRetryWorker")
        while self._running:
            try:
                await self._process_dlq()
            except Exception as e:
                logger.error(f"[DLQ] Worker error: {e}")
            await asyncio.sleep(self.interval)

    def stop(self):
        self._running = False
        
    async def _process_dlq(self):
        """
        Poll channel_dead_letters where status='pending' and next_retry_at <= NOW().
        For each message, attempt to process. If fail -> increment retry + backoff.
        If success -> mark 'processed'.
        If retry_count >= max_retries -> mark 'failed'.
        """
        from database import sesion_db
        from sqlalchemy import text
        import json
        
        async with sesion_db() as db:
            # Seleccionar dead letters pendientes que ya pueden reintentarse
            # Bloqueamos las filas con FOR UPDATE SKIP LOCKED para no pisarnos con otros workers
            query = text("""
                SELECT id, channel_id, event_type, payload, retry_count, max_retries 
                FROM channel_dead_letters
                WHERE status = 'pending' AND next_retry_at <= NOW()
                FOR UPDATE SKIP LOCKED
                LIMIT 50
            """)
            result = await db.execute(query)
            dead_letters = result.fetchall()
            
            if not dead_letters:
                return

            for dl in dead_letters:
                success = False
                new_error = None
                
                try:
                    # TODO: Implement actual provider retry logic here based on event_type.
                    # MOCK: for now, we assume success or handle it safely.
                    if dl.event_type == "send_message":
                        logger.info(f"[DLQ] Retrying send_message for channel {dl.channel_id}")
                        # Example: await provider.send_message(...)
                        success = True
                    else:
                        logger.warning(f"[DLQ] Unknown event_type {dl.event_type} in DLQ {dl.id}")
                        success = True # or handle differently
                except Exception as e:
                    success = False
                    new_error = str(e)
                
                if success:
                    update_q = text("""
                        UPDATE channel_dead_letters 
                        SET status = 'processed', updated_at = NOW()
                        WHERE id = :id
                    """)
                    await db.execute(update_q, {"id": dl.id})
                else:
                    new_retry_count = dl.retry_count + 1
                    if new_retry_count >= dl.max_retries:
                        update_q = text("""
                            UPDATE channel_dead_letters 
                            SET status = 'failed', error_reason = :err, updated_at = NOW()
                            WHERE id = :id
                        """)
                        await db.execute(update_q, {"id": dl.id, "err": new_error})
                    else:
                        # Exponential backoff: base * 2^retry
                        # base = 5 seconds
                        backoff_seconds = 5 * (2 ** dl.retry_count)
                        update_q = text(f"""
                            UPDATE channel_dead_letters 
                            SET retry_count = :rc, 
                                next_retry_at = NOW() + INTERVAL '{backoff_seconds} seconds',
                                error_reason = :err, 
                                updated_at = NOW()
                            WHERE id = :id
                        """)
                        await db.execute(update_q, {"id": dl.id, "rc": new_retry_count, "err": new_error})
                        
            await db.commit()

    def is_retryable(self, error_code: str) -> bool:
        """Determines if the failure should be retried based on policy."""
        no_retry_codes = {"401", "403", "invalid_payload", "forbidden"}
        if error_code in no_retry_codes:
            return False
        return True


class HeartbeatMonitor:
    def __init__(self, interval_seconds: int = 30):
        self.interval = interval_seconds
        self._running = False
        self.event_bus = None
        
    async def start(self, event_bus):
        self.event_bus = event_bus
        self._running = True
        logger.info("[Background] Started HeartbeatMonitor")
        while self._running:
            try:
                await self._monitor_channels()
            except Exception as e:
                logger.error(f"[Heartbeat] Monitor error: {e}")
            await asyncio.sleep(self.interval)

    def stop(self):
        self._running = False
        
    async def _monitor_channels(self):
        """
        Query connected_channels where status IN ('connected', 'degraded').
        If now - last_heartbeat > threshold -> update status.
        Emit channel.status_changed event.
        """
        from database import sesion_db
        import uuid
        
        # Prevent runtime issues if event_bus is not ready
        if not self.event_bus:
            return

        async with sesion_db() as db:
            from sqlalchemy import text
            
            # Encontramos canales desconectados o degradados
            # Threshold: 90 seconds (3 missed heartbeats) -> degraded
            query = text("""
                SELECT id, tenant_id, channel_type, status, last_heartbeat
                FROM connected_channels
                WHERE status IN ('connected', 'degraded')
                  AND last_heartbeat < NOW() - INTERVAL '90 seconds'
            """)
            result = await db.execute(query)
            channels = result.fetchall()
            
            for channel in channels:
                new_status = 'degraded' if channel.status == 'connected' else 'error'
                
                # Update en DB
                update_q = text("""
                    UPDATE connected_channels 
                    SET status = :new_status 
                    WHERE id = :id
                """)
                await db.execute(update_q, {"new_status": new_status, "id": channel.id})
                
                logger.warning(f"[Heartbeat] Channel {channel.id} transition {channel.status} -> {new_status}")
                
                # Emit event
                # Usar formato DomainEvent de dict a mano si no se importa fácilmente
                evt_payload = {
                    "event_id": str(uuid.uuid4()),
                    "tenant_id": str(channel.tenant_id),
                    "event_type": "channel.status_changed",
                    "payload": {
                        "channel_id": str(channel.id),
                        "channel_type": channel.channel_type,
                        "status": new_status,
                        "reason": "heartbeat_timeout"
                    }
                }
                # Se asume que publish acepta dict o objeto según la implementación del bus
                await self.event_bus.publish(evt_payload)
                    
            await db.commit()


class MetricsFlusher:
    def __init__(self, interval_seconds: int = 60):
        self.interval = interval_seconds
        self._running = False
        
    async def start(self):
        self._running = True
        logger.info("[Background] Started MetricsFlusher")
        while self._running:
            try:
                await self._flush_metrics()
            except Exception as e:
                logger.error(f"[Metrics] Flusher error: {e}")
            await asyncio.sleep(self.interval)

    def stop(self):
        self._running = False
        
    async def _flush_metrics(self):
        """
        Read redis counters and flush them into PostgreSQL channel_metrics_hourly.
        """
        pass


class BackgroundRuntime:
    """
    Orchestrates all background workers (Asyncio + Redis) for Operational Stability.
    Prevents large scattered loops in the FastAPI startup event.
    """
    def __init__(self):
        self.dlq_worker = DLQRetryWorker(interval_seconds=15)
        self.heartbeat_monitor = HeartbeatMonitor(interval_seconds=30)
        self.metrics_flusher = MetricsFlusher(interval_seconds=60)
        self._tasks: Set[asyncio.Task] = set()
        
    async def start(self, event_bus):
        logger.info("Initializing Background Operational Runtime...")
        
        # Start background workers as isolated tasks
        self._tasks.add(asyncio.create_task(self.dlq_worker.start()))
        self._tasks.add(asyncio.create_task(self.heartbeat_monitor.start(event_bus)))
        self._tasks.add(asyncio.create_task(self.metrics_flusher.start()))
        
        logger.info(f"BackgroundRuntime started {len(self._tasks)} workers.")

    async def stop(self):
        logger.info("Stopping Background Operational Runtime...")
        self.dlq_worker.stop()
        self.heartbeat_monitor.stop()
        self.metrics_flusher.stop()
        
        # Wait for graceful shutdown of tasks
        for task in self._tasks:
            task.cancel()
            
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("Background Operational Runtime stopped.")

# Global instance
background_runtime = BackgroundRuntime()
