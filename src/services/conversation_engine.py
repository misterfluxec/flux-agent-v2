import redis.asyncio as redis
import json
from datetime import datetime
from uuid import UUID
from contextlib import asynccontextmanager
from typing import Optional

from domain.conversation_state import ConversationState, ConversationContext, VALID_TRANSITIONS
from domain.events import DomainEvent, EventMetadata, EventType, HandoffRequestedPayload, MessageReceivedPayload
from core.event_bus import EventBus

class ConversationEngine:
    def __init__(self, redis_client: redis.Redis, event_bus: EventBus):
        self.redis = redis_client
        self.event_bus = event_bus
        self.STATE_KEY = "conv:state:{id}"
        self.LOCK_KEY = "conv:lock:{id}"
        self.LOCK_TTL = 30  # segundos

    @asynccontextmanager
    async def acquire_lock(self, conversation_id: UUID, owner: str):
        key = self.LOCK_KEY.format(id=conversation_id)
        acquired = await self.redis.set(key, owner, nx=True, ex=self.LOCK_TTL)
        if not acquired:
            raise PermissionError(f"Conversación {conversation_id} ya está controlada por otro agente/usuario")
        try:
            yield
        finally:
            # Solo liberar si el owner sigue siendo el mismo
            current = await self.redis.get(key)
            if current and current.decode() == owner:
                await self.redis.delete(key)

    async def get_context(self, conversation_id: UUID) -> ConversationContext:
        key = self.STATE_KEY.format(id=conversation_id)
        data = await self.redis.hgetall(key)
        if not data:
            # Estado por defecto
            return ConversationContext(
                conversation_id=conversation_id, 
                tenant_id=UUID("00000000-0000-0000-0000-000000000000"),
                agent_id=UUID("00000000-0000-0000-0000-000000000000")
            )
        
        # Parse data from redis hash
        parsed_data = {
            "conversation_id": UUID(data[b"conversation_id"].decode()),
            "tenant_id": UUID(data[b"tenant_id"].decode()),
            "agent_id": UUID(data[b"agent_id"].decode()),
            "current_state": ConversationState(data[b"current_state"].decode()),
            "owner_id": data.get(b"owner_id", b"").decode() or None,
            "last_activity": datetime.fromisoformat(data[b"last_activity"].decode()),
        }
        return ConversationContext.model_validate(parsed_data)

    async def transition(
        self, 
        conv_id: UUID, 
        new_state: ConversationState, 
        triggered_by: str, 
        tenant_id: UUID, 
        agent_id: UUID, 
        reason: Optional[str] = None, 
        metadata: Optional[dict] = None
    ) -> ConversationContext:
        async with self.redis.pipeline() as pipe:
            key = self.STATE_KEY.format(id=conv_id)
            current_data = await self.redis.hgetall(key)
            old_state_val = current_data.get(b"current_state", b"idle").decode()
            old_state = ConversationState(old_state_val)
            
            if new_state not in VALID_TRANSITIONS.get(old_state, []):
                raise ValueError(f"Transición inválida: {old_state} → {new_state}")
            
            # Prepare updates
            now_iso = datetime.utcnow().isoformat()
            updates = {
                "conversation_id": str(conv_id),
                "tenant_id": str(tenant_id),
                "agent_id": str(agent_id),
                "current_state": new_state.value,
                "last_activity": now_iso,
            }
            
            if new_state == ConversationState.HUMAN_TAKEOVER:
                updates["owner_id"] = "human_pending"
            else:
                updates["owner_id"] = "ai"

            pipe.hset(key, mapping=updates)
            await pipe.execute()
            
            ctx = await self.get_context(conv_id)
            
            # Event Payload based on transition
            if new_state == ConversationState.HUMAN_TAKEOVER:
                event_type = EventType.HANDOFF_REQUESTED
                payload = HandoffRequestedPayload(
                    from_agent="ai",
                    to_agent="human",
                    reason=reason or "Transitioned to HUMAN_TAKEOVER",
                    context_snapshot=metadata or {},
                    priority="high"
                )
            else:
                # Usa MessageReceivedPayload como fallback o crearías uno específico
                event_type = EventType.MESSAGE_SENT
                payload = MessageReceivedPayload(
                    channel="system",
                    from_number="system",
                    message_id="transition",
                    content=f"Transitioned to {new_state.value}",
                    metadata=metadata or {}
                )
            
            await self.event_bus.publish(DomainEvent(
                metadata=EventMetadata(
                    event_type=event_type,
                    tenant_id=tenant_id,
                    agent_id=agent_id,
                    conversation_id=conv_id,
                ),
                payload=payload
            ))
            
            return ctx
