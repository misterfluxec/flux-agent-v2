from typing import Dict
from redis.asyncio import Redis
from domain.events import DomainEvent, EventType
from core.event_bus import EventBus

class LeadScorer:
    """
    Scoring Engine + Cola de Prioridad.
    Motor event-driven que calcula priority en tiempo real y empuja
    a Redis Sorted Sets para alimentar la UI y las Notificaciones.
    """
    PRIORITY_QUEUE = "lead:priority:{tenant}"
    
    # Reglas base por industria (en Fase 4 pueden venir dinámicamente desde BD)
    WEIGHTS = {
        "sentiment": {"positive": 10, "neutral": 0, "negative": -15},
        "intent": {"purchase": 40, "inquiry": 10, "support": 5, "complaint": -20},
        "channel": {"whatsapp": 5, "voice": 10, "webchat": 3},
        "recency_decay": 0.95  # Factor de penalización por inactividad (cron)
    }

    def __init__(self, redis: Redis, event_bus: EventBus):
        self.redis = redis
        self.event_bus = event_bus

    async def on_event(self, event: DomainEvent):
        """Handler asíncrono para calcular scoring en cada interacción del lead"""
        # Verificación por seguridad aunque el EventBus filtre
        if event.metadata.event_type not in [EventType.MESSAGE_RECEIVED, EventType.INTENT_DETECTED]:
            return
            
        # Extraer datos de la carga útil del evento (payload)
        # Soportamos acceso dinámico usando model_dump() si es Pydantic BaseModel
        payload_dict = event.payload.model_dump() if hasattr(event.payload, "model_dump") else event.payload
        
        # Fallback de lead_id en event payload vs metadata
        lead_id = payload_dict.get("from_number") or event.metadata.customer_id
        if not lead_id:
            return  # No se puede calificar sin ID
            
        tenant_id = str(event.metadata.tenant_id)
        sentiment = payload_dict.get("sentiment", "neutral")
        intent = payload_dict.get("intent", "inquiry")
        channel = payload_dict.get("channel", "webchat")
        
        score = self._calculate(sentiment, intent, channel)
        
        # Push a Redis Sorted Set (score determina priority)
        await self.redis.zadd(self.PRIORITY_QUEUE.format(tenant=tenant_id), {str(lead_id): score})
        
        # Si es un lead caliente/crítico, forzar notificación al Event Bus
        if score >= 80:
            # Re-emitimos como LEAD_QUALIFIED para que el WS Bridge lo detecte y envíe a la UI
            from domain.events import EventMetadata, LeadQualifiedPayload
            
            hot_event = DomainEvent(
                metadata=EventMetadata(
                    event_type=EventType.LEAD_QUALIFIED,
                    tenant_id=event.metadata.tenant_id,
                    agent_id=event.metadata.agent_id,
                    conversation_id=event.metadata.conversation_id,
                    customer_id=event.metadata.customer_id,
                    correlation_id=event.metadata.correlation_id,
                ),
                payload=LeadQualifiedPayload(
                    lead_id=event.metadata.customer_id or event.metadata.conversation_id, # Fallback seguro
                    score=score,
                    intent=intent,
                    sentiment=sentiment,
                    urgency="high" if score >= 90 else "medium",
                    recommended_action="Contact immediately via Voice/WhatsApp",
                    context_summary=f"Automated scoring reached {score}."
                )
            )
            await self.event_bus.publish(hot_event)

    def _calculate(self, sentiment: str, intent: str, channel: str) -> float:
        base = self.WEIGHTS["sentiment"].get(sentiment, 0)
        base += self.WEIGHTS["intent"].get(intent, 0)
        base += self.WEIGHTS["channel"].get(channel, 0)
        return float(max(0, min(100, base)))  # Clamp entre 0-100

    def register(self) -> None:
        """Registra el scorer en el Event Bus global"""
        import asyncio
        asyncio.create_task(
            self.event_bus.subscribe(
                event_types=[EventType.MESSAGE_RECEIVED, EventType.INTENT_DETECTED],
                handler=self.on_event,
                consumer_name="lead-scorer",
            )
        )
