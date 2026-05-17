from __future__ import annotations
import asyncio, logging, random
from datetime import datetime, time
from zoneinfo import ZoneInfo

logger = logging.getLogger("flux.whatsapp_throttle")

ECUADOR_TZ = ZoneInfo("America/Guayaquil")
WINDOW_START = time(9, 0)
WINDOW_END   = time(19, 0)

class WhatsAppThrottle:
    """
    Anti-bloqueo para Evolution API (Baileys/no oficial).
    Simula comportamiento humano para evitar detección.
    """
    def __init__(self, redis, max_per_hour: int = 30):
        self.redis = redis
        self.max_per_hour = max_per_hour
        self._last_send: dict[str, float] = {}

    def _in_window(self) -> bool:
        now = datetime.now(ECUADOR_TZ).time()
        return WINDOW_START <= now <= WINDOW_END

    async def _check_hourly_limit(
        self, tenant_id: str
    ) -> bool:
        key = f"wa_throttle:{tenant_id}:{datetime.now(ECUADOR_TZ).strftime('%Y%m%d%H')}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, 3600)
        return count <= self.max_per_hour

    async def wait_before_send(
        self,
        tenant_id: str,
        to_number: str,
        is_bulk: bool = False,
    ) -> bool:
        if not self._in_window():
            logger.warning(
                "wa_throttle_outside_window",
                extra={"tenant_id": tenant_id,
                       "hour": datetime.now(ECUADOR_TZ).hour}
            )
            return False

        if not await self._check_hourly_limit(tenant_id):
            logger.warning(
                "wa_throttle_hourly_limit",
                extra={"tenant_id": tenant_id,
                       "limit": self.max_per_hour}
            )
            return False

        last = self._last_send.get(to_number, 0)
        import time as _time
        elapsed = _time.monotonic() - last

        if is_bulk:
            min_delay = random.uniform(8.0, 15.0)
        else:
            min_delay = random.uniform(3.0, 6.0)

        if elapsed < min_delay:
            wait = min_delay - elapsed + random.uniform(0.5, 1.5)
            logger.debug("wa_throttle_waiting",
                        extra={"wait_s": round(wait, 1),
                               "to": to_number[-4:]})
            await asyncio.sleep(wait)

        self._last_send[to_number] = _time.monotonic()
        return True

    async def send_with_throttle(
        self,
        evolution_adapter,
        session_id: str,
        tenant_id: str,
        to: str,
        text: str,
        is_bulk: bool = False,
    ) -> dict:
        allowed = await self.wait_before_send(
            tenant_id, to, is_bulk
        )
        if not allowed:
            return {"success": False,
                    "reason": "throttle_blocked"}
        return await evolution_adapter.send_message(
            session_id=session_id,
            payload={"to": to, "text": text}
        )
