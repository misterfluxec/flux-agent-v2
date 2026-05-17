# =============================================================================
# FLUXAGENT V2 — WHATSAPP ROUTER (CON COLA DE TAREAS)
# =============================================================================
# Versión actualizada usando Dramatiq para background tasks
# Respuestas inmediatas, procesamiento asíncrono
# =============================================================================

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel

from auth import PayloadToken, get_usuario_actual
from tasks.async_tasks import enqueue_task, enviar_whatsapp_task, procesar_webhook_whatsapp_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/whatsapp", tags=["WhatsApp"])

# =============================================================================
# SCHEMAS
# =============================================================================

class WhatsAppMessage(BaseModel):
    phone: str
    message: str
    media_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class WhatsAppResponse(BaseModel):
    status: str
    message: str
    task_id: Optional[str] = None
    queue_position: Optional[int] = None

# =============================================================================
# ENDPOINTS CON COLA DE TAREAS
# =============================================================================

@router.post("/send", response_model=WhatsAppResponse)
async def send_whatsapp(
    message_data: WhatsAppMessage,
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Envía WhatsApp en cola (no bloqueante)"""
    try:
        # Validar datos
        if not message_data.phone or not message_data.message:
            raise HTTPException(
                status_code=400,
                detail="Teléfono y mensaje son requeridos"
            )
        
        # Encolar tarea (inmediato)
        message = enqueue_task(
            enviar_whatsapp_task,
            tenant_id=usuario.tenant_id,
            phone=message_data.phone,
            message=message_data.message,
            media_url=message_data.media_url,
            metadata=message_data.metadata
        )
        
        logger.info(f"WhatsApp encolado: {message.message_id} - Usuario: {usuario.tenant_id}")
        
        return WhatsAppResponse(
            status="queued",
            message="Mensaje en cola de envío",
            task_id=message.message_id,
            queue_position=None  # TODO: Implementar posición en cola
        )
        
    except Exception as e:
        logger.error(f"Error encolando WhatsApp: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error encolando mensaje: {str(e)}"
        )

@router.post("/send-bulk")
async def send_bulk_whatsapp(
    messages: list[WhatsAppMessage],
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Envía múltiples WhatsApp en cola"""
    try:
        if len(messages) > 100:  # Límite para evitar sobrecarga
            raise HTTPException(
                status_code=400,
                detail="Máximo 100 mensajes por lote"
            )
        
        task_ids = []
        for msg in messages:
            message = enqueue_task(
                enviar_whatsapp_task,
                tenant_id=usuario.tenant_id,
                phone=msg.phone,
                message=msg.message,
                media_url=msg.media_url,
                metadata=msg.metadata
            )
            task_ids.append(message.message_id)
        
        return {
            "status": "queued_bulk",
            "message": f"{len(messages)} mensajes encolados",
            "task_ids": task_ids
        }
        
    except Exception as e:
        logger.error(f"Error encolando bulk WhatsApp: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error encolando mensajes: {str(e)}"
        )

@router.post("/webhook/{instance_id}")
async def webhook_whatsapp(
    instance_id: str,
    webhook_data: Dict[str, Any],
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Procesa webhook de WhatsApp en cola"""
    try:
        # Encolar procesamiento (inmediato)
        message = enqueue_task(
            procesar_webhook_whatsapp_task,
            tenant_id=usuario.tenant_id,
            webhook_data=webhook_data,
            instance_id=instance_id
        )
        
        logger.info(f"Webhook WhatsApp encolado: {message.message_id} - Instance: {instance_id}")
        
        return {
            "status": "queued",
            "message": "Webhook encolado para procesamiento",
            "task_id": message.message_id
        }
        
    except Exception as e:
        logger.error(f"Error encolando webhook WhatsApp: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando webhook: {str(e)}"
        )

@router.post("/send-media")
async def send_whatsapp_media(
    phone: str,
    message: str,
    file: UploadFile = File(...),
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Envía WhatsApp con media en cola"""
    try:
        # Procesar archivo (rápido, síncrono)
        if not file.content_type.startswith(('image/', 'video/', 'audio/')):
            raise HTTPException(
                status_code=400,
                detail="Solo se permiten archivos de imagen, video o audio"
            )
        
        # Guardar archivo temporal
        import os
        import uuid
        from fastapi import UploadFile
        
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1] if file.filename else 'tmp'
        media_path = f"uploads/temp/{file_id}.{file_extension}"
        
        os.makedirs("uploads/temp", exist_ok=True)
        
        with open(media_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Encolar tarea de envío
        message = enqueue_task(
            enviar_whatsapp_task,
            tenant_id=usuario.tenant_id,
            phone=phone,
            message=message,
            media_url=media_path,
            metadata={"original_filename": file.filename}
        )
        
        return WhatsAppResponse(
            status="queued",
            message="Media encolado para envío",
            task_id=message.message_id
        )
        
    except Exception as e:
        logger.error(f"Error encolando media WhatsApp: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando media: {str(e)}"
        )

@router.get("/task/{task_id}")
async def get_task_status(
    task_id: str,
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Obtiene status de tarea de WhatsApp"""
    try:
        from tasks.async_tasks import get_task_status
        
        status = get_task_status(task_id)
        
        return {
            "task_id": task_id,
            "status": status["status"],
            "timestamp": status["timestamp"],
            "error": status.get("error")
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo status de tarea {task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo status: {str(e)}"
        )

@router.get("/queue/stats")
async def get_queue_stats(
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Obtiene estadísticas de colas (admin)"""
    try:
        # TODO: Implementar estadísticas reales de Dramatiq
        return {
            "queues": {
                "whatsapp": {
                    "pending": 0,
                    "processing": 0,
                    "failed": 0,
                    "completed": 0
                }
            },
            "timestamp": "2024-01-01T00:00:00Z"  # TODO: Timestamp real
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo stats de colas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )

# =============================================================================
# ENDPOINTS LEGACY (MANTENIDOS POR COMPATIBILIDAD)
# =============================================================================

@router.get("/status")
async def get_whatsapp_status(
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Estado del servicio WhatsApp (legacy)"""
    try:
        # Verificar conexión con Evolution API
        from services.whatsapp_guardian import check_whatsapp_health
        
        health = await check_whatsapp_health(usuario.tenant_id)
        
        return {
            "status": "healthy" if health else "unhealthy",
            "tenant_id": usuario.tenant_id,
            "queue_enabled": True,
            "message": "Servicio operativo con cola de tareas"
        }
        
    except Exception as e:
        logger.error(f"Error verificando status WhatsApp: {e}")
        return {
            "status": "error",
            "message": f"Error verificando status: {str(e)}"
        }

# =============================================================================
# COMPARACIÓN: VERSIÓN ANTIGUA VS NUEVA
# =============================================================================

"""
# VERSIÓN ANTIGUA (bloqueante):
@router.post("/send")
async def send_whatsapp(...):
    # ❌ Procesamiento síncrono (lento)
    result = await enviar_whatsapp_async(...)
    return result  # ❌ Cliente espera mucho tiempo

# VERSIÓN NUEVA (con cola):
@router.post("/send")
async def send_whatsapp(...):
    # ✅ Encolar inmediato
    message = enqueue_task(enviar_whatsapp_task, ...)
    return {"status": "queued", "task_id": message.message_id}  # ✅ Respuesta rápida

# BENEFICIOS:
# 1. ✅ Respuesta inmediata al cliente
# 2. ✅ No bloquea el servidor
# 3. ✅ Reintentos automáticos
# 4. ✅ Mejor experiencia de usuario
# 5. ✅ Escalabilidad horizontal
# 6. ✅ Monitoreo de tareas
"""
