import uuid
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database import SesionLocal

class CustomerTimelineAggregator:
    """
    Agregador del Customer Operational Graph (Fase 3E).
    Traduce eventos técnicos de dominio (ej. payment.failed.v1) en 
    eventos semánticos unificados para la memoria operacional (AI + Humanos).
    """

    async def ingest_domain_event(self, event_type: str, payload: Dict[str, Any], tenant_id: str):
        """
        Recibe un evento del EventBus o del Outbox y lo convierte 
        en una entrada de la línea de tiempo si es relevante.
        """
        # Extraer información base dependiendo del type de evento
        customer_id = None
        order_id = None
        category = 'commerce'
        severity = 'info'
        title = ""
        desc = ""

        # ==========================================
        # EVENT ROUTING & TRANSLATION
        # ==========================================
        
        # 1. ÓRDENES Y COTIZACIONES
        if event_type == 'order.created.v1':
            order_id = payload.get('order_id')
            customer_id = await self._get_customer_from_order(tenant_id, order_id)
            title = f"Nueva Orden Creada"
            desc = f"Orden {order_id[:8]} generada por ${payload.get('total', 0)}."
            
        elif event_type == 'quote.converted.v1':
            order_id = payload.get('order_id')
            customer_id = await self._get_customer_from_order(tenant_id, order_id)
            title = "Cotización Aceptada"
            desc = "El cliente convirtió la cotización en una sort_order firme."
            severity = 'success'

        # 2. PAGOS
        elif event_type == 'payment.paid.v1':
            order_id = payload.get('order_id')
            customer_id = await self._get_customer_from_order(tenant_id, order_id)
            category = 'payment'
            title = "Pago Exitoso"
            desc = f"Pago confirmado vía {payload.get('provider')}. Monto: ${payload.get('amount')}"
            severity = 'success'

        elif event_type == 'payment.failed.v1':
            order_id = payload.get('order_id')
            customer_id = await self._get_customer_from_order(tenant_id, order_id)
            category = 'payment'
            title = "Fallo en el Pago"
            desc = f"Intento de pago rechazado por {payload.get('provider')}."
            severity = 'warning'

        # 3. INVENTARIO (Solo eventos que impactan directamente al cliente)
        elif event_type == 'inventory.released.v1':
            # Por ejemplo, carrito abandonado
            reason = payload.get('reason_code')
            if reason == 'abandoned_cart_cleanup':
                # Requerimos el correlation_id para saber de qué sort_order/carrito vino
                # Omitido para simplicidad en este MVP
                pass

        if not customer_id or not title:
            return # El evento no es relevante para el timeline del cliente

        # Inserción del evento semántico
        async with SesionLocal() as db:
            await db.execute(text("""
                INSERT INTO customer_timeline_events 
                (tenant_id, customer_id, event_category, event_type, order_id, title, description, severity, metadata)
                VALUES (:tenant_id, :customer_id, :category, :type, :order_id, :title, :desc, :severity, :meta)
            """), {
                "tenant_id": tenant_id,
                "customer_id": customer_id,
                "category": category,
                "type": event_type,
                "order_id": order_id,
                "title": title,
                "desc": desc,
                "severity": severity,
                "meta": "{}"
            })
            await db.commit()

    async def _get_customer_from_order(self, tenant_id: str, order_id: str) -> str:
        """Helper para resolver a qué cliente pertenece un evento atado a una sort_order."""
        if not order_id:
            return None
        async with SesionLocal() as db:
            res_exec = await db.execute(text("SELECT customer_id FROM orders WHERE id = :id AND tenant_id = :t"), 
                             {"id": order_id, "t": tenant_id})
            res = res_exec.fetchone()
            return str(res.customer_id) if res else None

    async def get_customer_timeline(self, tenant_id: str, customer_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retorna la vista unificada para el dashboard operacional o el AI Copilot.
        """
        async with SesionLocal() as db:
            events_res = await db.execute(text("""
                SELECT id, event_category, event_type, title, description, severity, occurred_at 
                FROM customer_timeline_events 
                WHERE tenant_id = :t AND customer_id = :c
                ORDER BY occurred_at DESC
                LIMIT :limit
            """), {"t": tenant_id, "c": customer_id, "limit": limit})
            events = events_res.fetchall()
            
            return [dict(e._mapping) for e in events]
