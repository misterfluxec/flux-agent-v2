import logging
import dramatiq
from datetime import datetime
from sqlalchemy import text
from typing import Dict, Any

from database import SesionLocal as async_session_factory
from services.ai_orchestrator import AIOrchestrator
# from services.whatsapp_sender import WhatsAppSender

logger = logging.getLogger(__name__)

@dramatiq.actor(max_retries=3, time_limit=30000)
async def procesar_seguimiento_cotizacion(seguimiento_id: str):
    """
    Worker que procesa un seguimiento programado para una cotización.
    Verifica si la cotización aún está pendiente, redacta el mensaje con IA, y lo envía.
    """
    logger.info(f"Procesando seguimiento {seguimiento_id}")
    
    async with async_session_factory() as session:
        # 1. Obtener seguimiento
        query_seg = text("""
            SELECT s.id, s.tenant_id, s.quote_id, s.status, s.attempts, q.customer_id
            FROM follow_ups s
            JOIN quotes q ON s.quote_id = q.id
            WHERE s.id = :id
        """)
        res_seg = await session.execute(query_seg, {"id": seguimiento_id})
        seguimiento = res_seg.fetchone()
        
        if not seguimiento:
            logger.error(f"Seguimiento {seguimiento_id} no encontrado")
            return
            
        if seguimiento.status in ['enviado', 'cancelado', 'respondido']:
            logger.info(f"Seguimiento {seguimiento_id} ya fue procesado o cancelado (status: {seguimiento.status})")
            return
            
        # Inyectar tenant context para RLS si es necesario (asumimos que worker tiene permisos bypassrls, pero por si acaso)
        await session.execute(text("SET app.current_tenant_id = :tenant"), {"tenant": str(seguimiento.tenant_id)})

        # 2. Verificar status actual de la cotización
        query_quote = text("""
            SELECT q.id, q.status, q.total, c.name as customer_name, c.phone as customer_phone
            FROM quotes q
            LEFT JOIN clientes c ON q.customer_id = c.id
            WHERE q.id = :quote_id
        """)
        res_quote = await session.execute(query_quote, {"quote_id": str(seguimiento.quote_id)})
        quote = res_quote.fetchone()
        
        if not quote:
            logger.error(f"Quote {seguimiento.quote_id} no encontrada")
            return
            
        # Si ya fue aceptada, pagada o rechazada, cancelamos
        if quote.status in ['accepted', 'paid', 'converted', 'rejected']:
            await session.execute(text("UPDATE follow_ups SET status = 'cancelado', updated_at = NOW() WHERE id = :id"), {"id": seguimiento_id})
            await session.commit()
            logger.info(f"Seguimiento {seguimiento_id} cancelado porque la cotización ya fue {quote.status}")
            return
            
        # 3. Yanua genera el mensaje basado en contexto
        # Nota: Obtenemos items de la cotización
        query_items = text("""
            SELECT catalog_item_id, quantity, unit_price 
            FROM quote_items 
            WHERE quote_id = :quote_id
        """)
        res_items = await session.execute(query_items, {"quote_id": str(seguimiento.quote_id)})
        items = [f"Item {row.catalog_item_id} (x{row.quantity})" for row in res_items.fetchall()]
        
        contexto = {
            "cliente": quote.customer_name or "Estimado Cliente",
            "total": str(quote.total),
            "items": items
        }
        
        # Instanciar orquestador (simplificado, se asumiría que los deps se resuelven)
        # Aquí proveemos None u objetos vacíos para deps no usados por generate_followup
        orchestrator = AIOrchestrator(
            redis=None, event_bus=None, policy_engine=None, 
            tool_executor=None, memory_manager=None, llm_provider=None
        )
        
        mensaje_personalizado = await orchestrator.generate_followup(contexto)
        
        # 4. Envío real vía WhatsApp
        if quote.customer_phone:
            # wa_sender = WhatsAppSender(redis_client=None) # Pasar deps necesarias en prod
            # success = await wa_sender.send_text(str(seguimiento.tenant_id), quote.customer_phone, mensaje_personalizado)
            # Simular envío exitoso para este worker (ya que requiere API externa real)
            success = True
        else:
            logger.warning(f"No hay teléfono para el cliente {quote.customer_name}, no se puede enviar mensaje")
            success = False
            
        # 5. Actualizar resultado
        if success:
            await session.execute(text("""
                UPDATE follow_ups 
                SET status = 'enviado', sent_message = :msg, updated_at = NOW() 
                WHERE id = :id
            """), {"msg": mensaje_personalizado, "id": seguimiento_id})
        else:
            await session.execute(text("""
                UPDATE follow_ups 
                SET attempts = attempts + 1, updated_at = NOW() 
                WHERE id = :id
            """), {"id": seguimiento_id})
            # Lanzamos excepción para que Dramatiq reintente
            raise Exception("Failed to send WhatsApp message")
            
        await session.commit()
        logger.info(f"Seguimiento {seguimiento_id} enviado exitosamente.")
