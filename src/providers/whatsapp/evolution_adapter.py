from __future__ import annotations
import logging
from typing import Any

import httpx

from providers.base import ChannelProvider
from core.exceptions import ChannelUnavailableError

logger = logging.getLogger("flux.evolution_adapter")

TIMEOUT = httpx.Timeout(connect=5.0, read=15.0,
                        write=10.0, pool=5.0)

class EvolutionProviderAdapter(ChannelProvider):

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._headers = {
            "apikey": api_key,
            "Content-Type": "application/json",
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers,
            timeout=TIMEOUT,
        )

    async def connect(
        self, config: dict[str, Any]
    ) -> dict[str, Any]:
        instance_name = config.get(
            "instance_name",
            f"flux_{config.get('phone_number','default')}"
        )
        body = {
            "instanceName": instance_name,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS",
        }
        async with self._client() as client:
            try:
                r = await client.post(
                    "/instance/create", json=body
                )
                r.raise_for_status()
                data = r.json()
            except httpx.HTTPStatusError as exc:
                raise ChannelUnavailableError(
                    f"Evolution create instance error "
                    f"{exc.response.status_code}: "
                    f"{exc.response.text[:200]}"
                )
            except httpx.RequestError as exc:
                raise ChannelUnavailableError(
                    f"Evolution no disponible: {exc}"
                )

        qr = (data.get("qrcode") or {})
        return {
            "status": "pending_qr",
            "instance_id": data.get(
                "instance", {}).get("instanceName", instance_name
            ),
            "qr_base64": qr.get("base64", ""),
            "qr_code": qr.get("code", ""),
        }

    async def health_check(
        self, session_id: str
    ) -> dict[str, Any]:
        async with self._client() as client:
            try:
                import time
                t0 = time.perf_counter()
                r = await client.get(
                    f"/instance/connectionState/{session_id}"
                )
                latency = round(
                    (time.perf_counter() - t0) * 1000, 1
                )
                if r.status_code == 404:
                    return {"status": "not_found",
                            "latency_ms": latency}
                r.raise_for_status()
                data = r.json()
                state = (data.get("instance") or {}).get(
                    "state", "unknown"
                )
                return {
                    "status": "connected"
                              if state == "open" else state,
                    "latency_ms": latency,
                    "raw_state": state,
                }
            except httpx.RequestError as exc:
                return {"status": "unreachable",
                        "error": str(exc)}

    async def send_message(
        self, session_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        to = payload.get("to", "")
        text = payload.get("text") or payload.get("body", "")
        media_url = payload.get("media_url")
        media_type = payload.get("media_type", "image")

        async with self._client() as client:
            try:
                if media_url:
                    endpoint = (
                        f"/message/sendMedia/{session_id}"
                    )
                    body: dict[str, Any] = {
                        "number": to,
                        "mediatype": media_type,
                        "media": media_url,
                        "caption": text,
                    }
                else:
                    endpoint = (
                        f"/message/sendText/{session_id}"
                    )
                    body = {
                        "number": to,
                        "text": text,
                    }

                r = await client.post(endpoint, json=body)
                r.raise_for_status()
                data = r.json()
                return {
                    "success": True,
                    "message_id": data.get("key", {}).get(
                        "id", ""
                    ),
                    "status": data.get("status", "sent"),
                }
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "evolution_send_error",
                    extra={
                        "status": exc.response.status_code,
                        "body": exc.response.text[:300],
                        "to": to,
                    },
                )
                raise ChannelUnavailableError(
                    f"Error enviando mensaje: "
                    f"{exc.response.status_code}"
                )
            except httpx.RequestError as exc:
                raise ChannelUnavailableError(
                    f"Evolution no disponible: {exc}"
                )

    async def disconnect(self, session_id: str) -> bool:
        async with self._client() as client:
            try:
                r = await client.delete(
                    f"/instance/delete/{session_id}"
                )
                return r.status_code in (200, 204, 404)
            except httpx.RequestError:
                return False

    async def refresh_session(
        self, session_id: str
    ) -> bool:
        async with self._client() as client:
            try:
                r = await client.get(
                    f"/instance/restart/{session_id}"
                )
                return r.status_code == 200
            except httpx.RequestError:
                return False

    async def validate_webhook(
        self, payload: dict[str, Any]
    ) -> bool:
        # Evolution API v2 envía el apikey en header.
        # La validación de header la hace el router 
        # (webhooks_router.py) al comparar el header 
        # 'apikey' con settings.evolution_api_key.
        # Aquí validamos que el payload tenga estructura mínima.
        return (
            "event" in payload
            and "instance" in payload
            and "data" in payload
        )
