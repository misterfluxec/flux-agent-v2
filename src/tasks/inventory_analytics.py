import logging
from sqlalchemy import text
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.database import async_session_factory

logger = logging.getLogger(__name__)

async def calculate_sales_velocity():
    """
    Analiza las órdenes pagadas de los últimos 30 días para calcular
    la velocidad de ventas (sales_velocity) de cada producto.
    sales_velocity = Unidades vendidas / Semanas evaluadas (4.28 para 30 días)
    """
    logger.info("📊 Iniciando cálculo de Sales Velocity (Inventory Analytics)...")
    try:
        async with async_session_factory() as session:
            # Consulta agregada de artículos vendidos en los últimos 30 días en órdenes confirmadas/pagadas
            # Asumimos que orders.payment_status = 'paid' o orders.status IN ('completed', 'processing')
            # y que están relacionados con quotes y quote_items, u order_items directamente.
            
            # Utilizaremos order_items asumiendo que existen, o quote_items de órdenes pagadas.
            # Veamos si order_items existe, o quote_items de quotes aceptados.
            # Simplificamos: contamos los quote_items de quotes que están en 'accepted' o 'paid'
            # (asumiendo que quote.status refleja si se vendió o generó la orden).
            
            query_stats = text("""
                WITH sales_data AS (
                    SELECT qi.catalog_item_id as offer_id, SUM(qi.quantity) as total_sold
                    FROM quote_items qi
                    JOIN quotes q ON qi.quote_id = q.id
                    WHERE q.status IN ('accepted', 'paid', 'converted')
                    AND q.created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY qi.catalog_item_id
                )
                SELECT offer_id, total_sold FROM sales_data
            """)
            
            result = await session.execute(query_stats)
            sales = result.fetchall()
            
            if not sales:
                logger.info("ℹ️ No hay ventas en los últimos 30 días para calcular velocidad.")
                return

            # Preparar actualizaciones masivas
            # 30 días = ~4.28 semanas
            updates = []
            for row in sales:
                velocity = round(row.total_sold / 4.28, 2)
                updates.append({
                    "id": str(row.offer_id),
                    "velocity": velocity
                })

            if updates:
                # Actualizar business_offers
                update_query = text("""
                    UPDATE business_offers 
                    SET sales_velocity = :velocity, last_velocity_calc_at = NOW()
                    WHERE id = :id
                """)
                # Ejecutar uno por uno o usar execute_many si estuviera soportado. AsyncPG soporta listas en params manuales
                # Por simplicidad iteramos:
                for u in updates:
                    await session.execute(update_query, u)
                
                await session.commit()
                logger.info(f"✅ Sales Velocity actualizado para {len(updates)} productos.")
            
            # (Opcional) Detectar e imprimir productos con stock bajo que son 'Fast Moving'
            
    except Exception as e:
        logger.error(f"Error calculando Sales Velocity: {e}")

def setup_inventory_analytics_scheduler(scheduler: AsyncIOScheduler):
    """
    Registra el trabajo de cálculo analítico diario.
    """
    # Ejecutamos a la 02:00 AM diario
    scheduler.add_job(
        calculate_sales_velocity,
        'cron',
        hour=2,
        minute=0,
        id='inventory_sales_velocity',
        replace_existing=True
    )
    logger.info("📅 Inventory Analytics scheduler registrado (Diario 02:00 AM)")
