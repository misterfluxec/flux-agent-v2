import logging
from fastapi import FastAPI
from domain.events import EventType
from tasks.followups import schedule_followup
from core.event_listeners import persist_event_to_timeline
from database import obtener_sesion

logger = logging.getLogger(__name__)

async def register_event_handlers(app: FastAPI):
    event_bus = app.state.event_bus

    async def handle_payment_completed(event):
        ctx = event.payload.dict() if hasattr(event.payload, "dict") else event.payload
        customer_phone = ctx.get("customer_phone") or "desconocido"
        order_id = ctx.get("order_id")
        schedule_followup(customer_phone, "post_purchase_survey", {"order_id": order_id}, delay_hours=72)
        schedule_followup(customer_phone, "order_confirmation", {"order_id": order_id}, delay_minutes=1)

    async def handle_payment_failed(event):
        ctx = event.payload.dict() if hasattr(event.payload, "dict") else event.payload
        customer_phone = ctx.get("customer_phone") or "desconocido"
        order_id = ctx.get("order_id")
        schedule_followup(customer_phone, "payment_pending", {"order_id": order_id}, delay_minutes=5)

    await event_bus.subscribe([EventType.PAYMENT_COMPLETED], handle_payment_completed, "followups_worker")
    await event_bus.subscribe([EventType.PAYMENT_FAILED], handle_payment_failed, "followups_worker")

    # Timeline persistence
    async def timeline_wrapper(event):
        async with obtener_sesion() as db:
            await persist_event_to_timeline(event, db, app.state.redis)

    timeline_events = [
        EventType.MESSAGE_RECEIVED, EventType.MESSAGE_SENT,
        EventType.QUOTE_GENERATED, EventType.QUOTE_ACCEPTED,
        EventType.ORDER_CREATED, EventType.PAYMENT_COMPLETED,
        EventType.PAYMENT_FAILED, EventType.BOOKING_CONFIRMED,
        EventType.HANDOFF_REQUESTED, EventType.FOLLOWUP_SCHEDULED
    ]
    await event_bus.subscribe(timeline_events, timeline_wrapper, "timeline_worker")
    logger.info("✅ EventBus handlers registrados")
