import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tasks.rag_scheduler import start_scheduler as start_rag_scheduler, stop_scheduler as stop_rag_scheduler
from tasks.quota_reset import start_quota_scheduler, stop_quota_scheduler
from tasks.followups import set_followup_scheduler

logger = logging.getLogger(__name__)
_scheduler: AsyncIOScheduler | None = None

async def start_schedulers():
    global _scheduler
    _scheduler = AsyncIOScheduler()
    
    try:
        await start_quota_scheduler()
        start_rag_scheduler()
        set_followup_scheduler(_scheduler)
        _scheduler.start()
        logger.info("✅ Schedulers iniciados (Quota, RAG, Followups)")
    except Exception as e:
        logger.warning(f"⚠️ Error iniciando schedulers: {e}")

async def stop_schedulers():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    try:
        await stop_quota_scheduler()
        stop_rag_scheduler()
    except Exception: pass
    logger.info("🔴 Schedulers detenidos")
