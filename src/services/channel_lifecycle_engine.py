import logging
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import text
from database import sesion_db
from domain.channels import ChannelStatus, ChannelConfig
from core.ws_event_bridge import WSRealtimeBridge

logger = logging.getLogger(__name__)

class ChannelLifecycleEngine:
    """
    Motor B2B para gobernar el estado de la conexión de todos los canales.
    - Maneja la base de datos `connected_channels`.
    - Genera QRs o Inicia validaciones de Webhooks.
    - Emite eventos al EventBus.
    """

    @classmethod
    async def get_channels(cls, tenant_id: UUID) -> List[ChannelConfig]:
        """Obtiene la lista de canales y sus estados para un tenant."""
        async with sesion_db(tenant_id) as db:
            result = await db.execute(text(
                "SELECT * FROM connected_channels WHERE tenant_id = :tid"
            ), {"tid": str(tenant_id)})
            
            channels = []
            for row in result.fetchall():
                channels.append(ChannelConfig(
                    id=row.id,
                    tenant_id=row.tenant_id,
                    channel_type=row.channel_type,
                    status=ChannelStatus(row.status),
                    external_session_id=row.external_session_id,
                    config=row.config or {},
                    health_score=row.health_score,
                    last_heartbeat=row.last_heartbeat,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                ))
            return channels

    @classmethod
    async def get_channel(cls, tenant_id: UUID, channel_type: str) -> Optional[ChannelConfig]:
        """Busca un canal específico."""
        async with sesion_db(tenant_id) as db:
            result = await db.execute(text(
                "SELECT * FROM connected_channels WHERE tenant_id = :tid AND channel_type = :ctype LIMIT 1"
            ), {"tid": str(tenant_id), "ctype": channel_type})
            row = result.fetchone()
            if row:
                return ChannelConfig(
                    id=row.id,
                    tenant_id=row.tenant_id,
                    channel_type=row.channel_type,
                    status=ChannelStatus(row.status),
                    external_session_id=row.external_session_id,
                    config=row.config or {},
                    health_score=row.health_score,
                    last_heartbeat=row.last_heartbeat,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
            return None

    @classmethod
    async def generate_qr(cls, tenant_id: UUID, phone_number: str) -> Dict[str, Any]:
        """Inicia el ciclo de vida mock de WhatsApp solicitando un QR."""
        existing = await cls.get_channel(tenant_id, "whatsapp")
        channel_id = existing.id if existing else uuid4()
        
        status = ChannelStatus.AWAITING_QR_SCAN
        
        async with sesion_db(tenant_id) as db:
            if existing:
                await db.execute(text("""
                    UPDATE connected_channels 
                    SET status = :st, updated_at = NOW(), config = config || :cfg
                    WHERE id = :cid
                """), {"st": status.value, "cid": str(channel_id), "cfg": '{"phone": "' + phone_number + '"}'})
            else:
                await db.execute(text("""
                    INSERT INTO connected_channels (id, tenant_id, channel_type, status, config)
                    VALUES (:id, :tid, 'whatsapp', :st, :cfg)
                """), {
                    "id": str(channel_id),
                    "tid": str(tenant_id),
                    "st": status.value,
                    "cfg": '{"phone": "' + phone_number + '"}'
                })
        
        # Emitir cambio de estado
        await WSRealtimeBridge.broadcast_to_tenant(str(tenant_id), {
            "event_type": "channel.status_changed",
            "channel": "whatsapp",
            "payload": {
                "status": status.value,
                "health_score": 100
            }
        })
        
        # MOCK BASE64 (A real app would cache this in Redis and return a URL)
        # Using a tiny dummy base64 pixel to not break memory
        dummy_qr_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        
        return {
            "channel_id": str(channel_id),
            "qr_code_base64": dummy_qr_base64,
            "status": status.value
        }

    @classmethod
    async def connect_channel(cls, tenant_id: UUID, channel_type: str, config: Dict[str, Any]) -> ChannelConfig:
        """Confirma la conexión de un canal (ej. Telegram Token o Escaneo QR simulado)."""
        existing = await cls.get_channel(tenant_id, channel_type)
        channel_id = existing.id if existing else uuid4()
        status = ChannelStatus.CONNECTED
        
        async with sesion_db(tenant_id) as db:
            if existing:
                await db.execute(text("""
                    UPDATE connected_channels 
                    SET status = :st, updated_at = NOW(), last_heartbeat = NOW(), health_score = 100
                    WHERE id = :cid
                """), {"st": status.value, "cid": str(channel_id)})
            else:
                await db.execute(text("""
                    INSERT INTO connected_channels (id, tenant_id, channel_type, status, last_heartbeat)
                    VALUES (:id, :tid, :ctype, :st, NOW())
                """), {
                    "id": str(channel_id),
                    "tid": str(tenant_id),
                    "ctype": channel_type,
                    "st": status.value
                })
        
        # Obtenemos el registro fresco
        updated = await cls.get_channel(tenant_id, channel_type)
        
        await WSRealtimeBridge.broadcast_to_tenant(str(tenant_id), {
            "event_type": "channel.status_changed",
            "channel": channel_type,
            "payload": {
                "status": status.value,
                "health_score": 100
            }
        })
        
        return updated

    @classmethod
    async def disconnect_channel(cls, tenant_id: UUID, channel_id: UUID) -> None:
        """Desconecta manualmente un canal."""
        async with sesion_db(tenant_id) as db:
            res = await db.execute(text("""
                UPDATE connected_channels 
                SET status = :st, updated_at = NOW()
                WHERE id = :cid AND tenant_id = :tid
                RETURNING channel_type
            """), {"st": ChannelStatus.DISCONNECTED.value, "cid": str(channel_id), "tid": str(tenant_id)})
            
            row = res.fetchone()
            if row:
                await WSRealtimeBridge.broadcast_to_tenant(str(tenant_id), {
                    "event_type": "channel.status_changed",
                    "channel": row.channel_type,
                    "payload": {
                        "status": ChannelStatus.DISCONNECTED.value,
                        "health_score": 0
                    }
                })

    @classmethod
    async def test_connection(cls, tenant_id: UUID, channel_type: str) -> Dict[str, Any]:
        """Realiza un Round-Trip Test disparando un evento al WebSocket."""
        # Simulated Latency & Verification
        import asyncio
        start_time = datetime.now()
        
        # Simulamos verificación interna del webhook/token
        await asyncio.sleep(0.4) 
        latency = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Confirmamos enviando un ACK asíncrono
        await WSRealtimeBridge.broadcast_to_tenant(str(tenant_id), {
            "event_type": "channel.test_ack",
            "channel": channel_type,
            "payload": {
                "latency_ms": latency,
                "status": "ok"
            }
        })
        
        return {
            "status": "success",
            "latency_ms": latency,
            "message": "Round-trip ping initialized."
        }
