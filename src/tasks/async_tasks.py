# =============================================================================
# FLUXAGENT V2 — ASYNC TASKS (DRAMATIQ)
# =============================================================================
# Tareas en background con reintentos y logging
# WhatsApp, Voz, Analytics, etc.
# =============================================================================

import dramatiq
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from core.queue.broker import get_queue_config
from services.whatsapp_sender import enviar_whatsapp_async
from services.voice_pipeline_service import procesar_audio_pipeline
from services.analytics import actualizar_analytics_async

logger = logging.getLogger(__name__)

# =============================================================================
# TAREAS DE WHATSAPP
# =============================================================================

@dramatiq.actor(
    queue_name="whatsapp",
    max_retries=3,
    retry_delay=30,
    time_limit=300  # 5 minutos timeout
)
def enviar_whatsapp_task(
    tenant_id: str,
    phone: str,
    message: str,
    media_url: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Envía WhatsApp en background con reintentos"""
    
    task_id = dramatiq.get_current_message().message_id
    logger.info(f"[{task_id}] Iniciando envío WhatsApp: {phone} - Tenant: {tenant_id}")
    
    try:
        # Ejecutar función async en contexto sync
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            enviar_whatsapp_async(
                tenant_id=tenant_id,
                phone=phone,
                message=message,
                media_url=media_url,
                metadata=metadata or {}
            )
        )
        
        loop.close()
        
        logger.info(f"[{task_id}] ✅ WhatsApp enviado exitosamente: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[{task_id}] ❌ Falló envío WhatsApp: {e}", exc_info=True)
        # Relanzar para que Dramatiq reintente
        raise

@dramatiq.actor(
    queue_name="whatsapp",
    max_retries=2,
    retry_delay=60,
    time_limit=180
)
def procesar_webhook_whatsapp_task(
    tenant_id: str,
    webhook_data: Dict[str, Any],
    instance_id: str
):
    """Procesa webhook de WhatsApp en background"""
    
    task_id = dramatiq.get_current_message().message_id
    logger.info(f"[{task_id}] Procesando webhook WhatsApp: {instance_id}")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Procesar webhook async
        from services.webhook_processor import procesar_webhook_whatsapp
        result = loop.run_until_complete(
            procesar_webhook_whatsapp(
                tenant_id=tenant_id,
                webhook_data=webhook_data,
                instance_id=instance_id
            )
        )
        
        loop.close()
        
        logger.info(f"[{task_id}] ✅ Webhook procesado: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[{task_id}] ❌ Error procesando webhook: {e}", exc_info=True)
        raise

# =============================================================================
# TAREAS DE VOZ
# =============================================================================

@dramatiq.actor(
    queue_name="voice",
    max_retries=2,
    retry_delay=60,
    time_limit=600  # 10 minutos para procesamiento de audio
)
def procesar_audio_task(
    audio_path: str,
    tenant_id: str,
    conversation_id: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """Procesa pipeline de voz en background"""
    
    task_id = dramatiq.get_current_message().message_id
    logger.info(f"[{task_id}] Procesando audio: {audio_path} - Conv: {conversation_id}")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            procesar_audio_pipeline(
                audio_path=audio_path,
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                metadata=metadata or {}
            )
        )
        
        loop.close()
        
        logger.info(f"[{task_id}] ✅ Audio procesado: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[{task_id}] ❌ Error procesando audio: {e}", exc_info=True)
        raise

@dramatiq.actor(
    queue_name="voice",
    max_retries=1,
    retry_delay=120,
    time_limit=300
)
def generar_respuesta_voz_task(
    text: str,
    tenant_id: str,
    conversation_id: str,
    voice_model: str = "es"
):
    """Genera respuesta de voz (TTS) en background"""
    
    task_id = dramatiq.get_current_message().message_id
    logger.info(f"[{task_id}] Generando TTS: {len(text)} chars - Conv: {conversation_id}")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        from services.tts_service import generar_tts_async
        result = loop.run_until_complete(
            generar_tts_async(
                text=text,
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                voice_model=voice_model
            )
        )
        
        loop.close()
        
        logger.info(f"[{task_id}] ✅ TTS generado: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[{task_id}] ❌ Error generando TTS: {e}", exc_info=True)
        raise

# =============================================================================
# TAREAS DE ANALYTICS
# =============================================================================

@dramatiq.actor(
    queue_name="analytics",
    max_retries=1,
    retry_delay=300,  # 5 minutos
    time_limit=120
)
def actualizar_analytics_task(
    tenant_id: str,
    event_type: str,
    event_data: Dict[str, Any]
):
    """Actualiza analytics en background"""
    
    task_id = dramatiq.get_current_message().message_id
    logger.info(f"[{task_id}] Actualizando analytics: {event_type} - Tenant: {tenant_id}")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            actualizar_analytics_async(
                tenant_id=tenant_id,
                event_type=event_type,
                event_data=event_data
            )
        )
        
        loop.close()
        
        logger.info(f"[{task_id}] ✅ Analytics actualizados: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[{task_id}] ❌ Error actualizando analytics: {e}", exc_info=True)
        # No reintentar analytics para evitar duplicados
        logger.warning(f"[{task_id}] ⚠️ Analytics fallido pero no se reintentará")

# =============================================================================
# TAREAS DE MANTENIMIENTO
# =============================================================================

@dramatiq.actor(
    queue_name="analytics",
    max_retries=1,
    retry_delay=600,  # 10 minutos
    time_limit=1800  # 30 minutos
)
def limpiar_cache_task(tenant_id: Optional[str] = None):
    """Limpia caché de Redis periódicamente"""
    
    task_id = dramatiq.get_current_message().message_id
    logger.info(f"[{task_id}] Iniciando limpieza de caché: {tenant_id or 'global'}")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        from services.cache_service import limpiar_cache_async
        result = loop.run_until_complete(
            limpiar_cache_async(tenant_id=tenant_id)
        )
        
        loop.close()
        
        logger.info(f"[{task_id}] ✅ Caché limpiado: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[{task_id}] ❌ Error limpiando caché: {e}", exc_info=True)
        raise

@dramatiq.actor(
    queue_name="analytics",
    max_retries=1,
    retry_delay=3600,  # 1 hora
    time_limit=3600  # 1 hora
)
def generar_reporte_diario_task(tenant_id: str):
    """Genera reporte diario de analytics"""
    
    task_id = dramatiq.get_current_message().message_id
    logger.info(f"[{task_id}] Generando reporte diario: {tenant_id}")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        from services.report_service import generar_reporte_diario_async
        result = loop.run_until_complete(
            generar_reporte_diario_async(tenant_id=tenant_id)
        )
        
        loop.close()
        
        logger.info(f"[{task_id}] ✅ Reporte generado: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[{task_id}] ❌ Error generando reporte: {e}", exc_info=True)
        # No reintentar reportes diarios

# =============================================================================
# TAREAS DE INTEGRACIÓN
# =============================================================================

@dramatiq.actor(
    queue_name="default",
    max_retries=3,
    retry_delay=60,
    time_limit=300
)
def sincronizar_oauth_task(
    tenant_id: str,
    provider: str,
    sync_type: str
):
    """Sincroniza datos de OAuth en background"""
    
    task_id = dramatiq.get_current_message().message_id
    logger.info(f"[{task_id}] Sincronizando OAuth: {provider} - {sync_type} - Tenant: {tenant_id}")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        from services.oauth_sync import sincronizar_oauth_async
        result = loop.run_until_complete(
            sincronizar_oauth_async(
                tenant_id=tenant_id,
                provider=provider,
                sync_type=sync_type
            )
        )
        
        loop.close()
        
        logger.info(f"[{task_id}] ✅ OAuth sincronizado: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[{task_id}] ❌ Error sincronizando OAuth: {e}", exc_info=True)
        raise

# =============================================================================
# UTILIDADES
# =============================================================================

def enqueue_task(task_func, *args, **kwargs):
    """Helper para encolar tareas con logging"""
    try:
        message = task_func.send(*args, **kwargs)
        logger.info(f"✅ Tarea encolada: {task_func.actor_name} - ID: {message.message_id}")
        return message
    except Exception as e:
        logger.error(f"❌ Error encolando tarea {task_func.actor_name}: {e}")
        raise

def get_task_status(message_id: str) -> Dict[str, Any]:
    """Obtiene estado de tarea (si el broker lo soporta)"""
    try:
        broker = get_broker()
        # Implementar según broker específico
        return {
            "message_id": message_id,
            "status": "queued",  # Simplificado
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error obteniendo estado de tarea {message_id}: {e}")
        return {
            "message_id": message_id,
            "status": "unknown",
            "error": str(e)
        }
