import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# TODO: Asegurar que el APScheduler se instancie globalmente
# Asumiremos que se usa de main.py o tasks/rag_scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

# Referencia global al scheduler que se inyectará al iniciar la app
_scheduler: AsyncIOScheduler | None = None

def set_followup_scheduler(scheduler: AsyncIOScheduler):
    global _scheduler
    _scheduler = scheduler

async def send_followup_message(customer_phone: str, template: str, context: Dict[str, Any]):
    """
    Función que el scheduler ejecutará en el futuro.
    """
    logger.info(f"Ejecutando follow-up {template} para {customer_phone}")
    
    messages = {
        "quote_reminder": f"Hola 👋, te recordamos que tu cotización está por vencer. ¿Necesitas ajustar algo?",
        "order_confirmation": f"✅ Tu orden ha sido confirmada. Te enviaremos novedades pronto. ID: {context.get('order_id')}",
        "post_purchase_survey": f"Gracias por tu compra 🙏. ¿Cómo calificarías tu experiencia? (1-5)",
        "payment_pending": f"💳 Tu pago está pendiente. Completa aquí: {context.get('payment_link')}"
    }
    
    text = messages.get(template, "Seguimiento automático")
    
    # Aquí iría la integración real con WhatsApp:
    # from services.channels.whatsapp_service import send_whatsapp_message
    # await send_whatsapp_message(phone=customer_phone, text=text)
    
    logger.info(f"Mensaje enviado a {customer_phone}: {text}")

def schedule_followup(customer_phone: str, template: str, context: Dict[str, Any], delay_hours: int = 0, delay_minutes: int = 0):
    """
    Programa un envío futuro usando APScheduler.
    """
    global _scheduler
    if not _scheduler:
        logger.warning("Scheduler no inicializado para followups. El mensaje no se enviará.")
        return
        
    run_date = datetime.utcnow() + timedelta(hours=delay_hours, minutes=delay_minutes)
    
    _scheduler.add_job(
        send_followup_message,
        'date',
        run_date=run_date,
        kwargs={"customer_phone": customer_phone, "template": template, "context": context},
        id=f"followup_{template}_{customer_phone}_{run_date.timestamp()}",
        replace_existing=True
    )
    logger.info(f"Followup '{template}' programado para {run_date} (tel: {customer_phone})")
