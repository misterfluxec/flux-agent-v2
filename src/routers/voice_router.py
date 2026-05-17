# =============================================================================
# FLUXAGENT V2 — VOICE ROUTER (CON COLA DE TAREAS)
# =============================================================================
# Versión actualizada usando Dramatiq para procesamiento de voz
# STT/TTS asíncrono con cola de procesamiento
# =============================================================================

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel

from auth import PayloadToken, get_usuario_actual
from tasks.async_tasks import enqueue_task, procesar_audio_task, generar_respuesta_voz_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/voice", tags=["Voice"])

# =============================================================================
# SCHEMAS
# =============================================================================

class VoiceProcessRequest(BaseModel):
    conversation_id: str
    audio_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TTSRequest(BaseModel):
    text: str
    conversation_id: str
    voice_model: str = "es"
    metadata: Optional[Dict[str, Any]] = None

class VoiceResponse(BaseModel):
    status: str
    message: str
    task_id: Optional[str] = None
    processing_time: Optional[float] = None

# =============================================================================
# ENDPOINTS CON COLA DE TAREAS
# =============================================================================

@router.post("/process-audio", response_model=VoiceResponse)
async def process_audio(
    request: VoiceProcessRequest,
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Procesa audio (STT + análisis) en cola"""
    try:
        if not request.audio_url:
            raise HTTPException(
                status_code=400,
                detail="URL de audio es requerida"
            )
        
        # Encolar procesamiento (inmediato)
        message = enqueue_task(
            procesar_audio_task,
            audio_path=request.audio_url,
            tenant_id=usuario.tenant_id,
            conversation_id=request.conversation_id,
            metadata=request.metadata
        )
        
        logger.info(f"Audio encolado: {message.message_id} - Conv: {request.conversation_id}")
        
        return VoiceResponse(
            status="queued",
            message="Audio encolado para procesamiento",
            task_id=message.message_id
        )
        
    except Exception as e:
        logger.error(f"Error encolando audio: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error encolando audio: {str(e)}"
        )

@router.post("/upload-audio", response_model=VoiceResponse)
async def upload_audio(
    conversation_id: str,
    file: UploadFile = File(...),
    metadata: Optional[str] = None,
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Sube y procesa audio en cola"""
    try:
        # Validar type de archivo
        if not file.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=400,
                detail="Solo se permiten archivos de audio"
            )
        
        # Guardar archivo temporal
        import os
        import uuid
        import json
        
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1] if file.filename else 'wav'
        audio_path = f"uploads/audio/{file_id}.{file_extension}"
        
        os.makedirs("uploads/audio", exist_ok=True)
        
        with open(audio_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Parsear metadata
        parsed_metadata = {}
        if metadata:
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                parsed_metadata = {"raw": metadata}
        
        # Encolar procesamiento
        message = enqueue_task(
            procesar_audio_task,
            audio_path=audio_path,
            tenant_id=usuario.tenant_id,
            conversation_id=conversation_id,
            metadata=parsed_metadata
        )
        
        logger.info(f"Audio subido y encolado: {message.message_id} - Conv: {conversation_id}")
        
        return VoiceResponse(
            status="uploaded_queued",
            message="Audio subido y encolado para procesamiento",
            task_id=message.message_id
        )
        
    except Exception as e:
        logger.error(f"Error subiendo audio: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando audio: {str(e)}"
        )

@router.post("/generate-tts", response_model=VoiceResponse)
async def generate_tts(
    request: TTSRequest,
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Genera respuesta de voz (TTS) en cola"""
    try:
        if not request.text or len(request.text.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Texto es requerido"
            )
        
        if len(request.text) > 5000:  # Límite para evitar sobrecarga
            raise HTTPException(
                status_code=400,
                detail="Texto demasiado largo (máximo 5000 caracteres)"
            )
        
        # Encolar generación TTS
        message = enqueue_task(
            generar_respuesta_voz_task,
            text=request.text,
            tenant_id=usuario.tenant_id,
            conversation_id=request.conversation_id,
            voice_model=request.voice_model,
            metadata=request.metadata
        )
        
        logger.info(f"TTS encolado: {message.message_id} - Conv: {request.conversation_id}")
        
        return VoiceResponse(
            status="queued",
            message="TTS encolado para generación",
            task_id=message.message_id
        )
        
    except Exception as e:
        logger.error(f"Error encolando TTS: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generando TTS: {str(e)}"
        )

@router.post("/generate-tts-batch")
async def generate_tts_batch(
    requests: list[TTSRequest],
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Genera múltiples TTS en cola"""
    try:
        if len(requests) > 50:  # Límite para evitar sobrecarga
            raise HTTPException(
                status_code=400,
                detail="Máximo 50 textos por lote"
            )
        
        task_ids = []
        for req in requests:
            if len(req.text) > 5000:
                continue  # Saltar textos muy largos
            
            message = enqueue_task(
                generar_respuesta_voz_task,
                text=req.text,
                tenant_id=usuario.tenant_id,
                conversation_id=req.conversation_id,
                voice_model=req.voice_model,
                metadata=req.metadata
            )
            task_ids.append(message.message_id)
        
        return {
            "status": "queued_batch",
            "message": f"{len(task_ids)} TTS encolados",
            "task_ids": task_ids,
            "skipped": len(requests) - len(task_ids)
        }
        
    except Exception as e:
        logger.error(f"Error encolando batch TTS: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando lote: {str(e)}"
        )

@router.get("/task/{task_id}")
async def get_voice_task_status(
    task_id: str,
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Obtiene status de tarea de voz"""
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
        logger.error(f"Error obteniendo status de tarea voz {task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo status: {str(e)}"
        )

@router.get("/queue/stats")
async def get_voice_queue_stats(
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Obtiene estadísticas de colas de voz"""
    try:
        # TODO: Implementar estadísticas reales de Dramatiq
        return {
            "queues": {
                "voice": {
                    "pending": 0,
                    "processing": 0,
                    "failed": 0,
                    "completed": 0
                }
            },
            "timestamp": "2024-01-01T00:00:00Z"  # TODO: Timestamp real
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo stats de colas voz: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )

# =============================================================================
# ENDPOINTS LEGACY (MANTENIDOS POR COMPATIBILIDAD)
# =============================================================================

@router.get("/status")
async def get_voice_status(
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Estado del servicio de voz (legacy)"""
    try:
        # Verificar servicios de voz
        from services.voice_status import check_voice_services
        
        status = await check_voice_services(usuario.tenant_id)
        
        return {
            "status": "healthy" if status else "unhealthy",
            "tenant_id": usuario.tenant_id,
            "queue_enabled": True,
            "services": {
                "stt": status.get("stt", False),
                "tts": status.get("tts", False),
                "pipeline": status.get("pipeline", False)
            },
            "message": "Servicio de voz operativo con cola de tareas"
        }
        
    except Exception as e:
        logger.error(f"Error verificando status voz: {e}")
        return {
            "status": "error",
            "message": f"Error verificando status: {str(e)}"
        }

@router.get("/voices")
async def get_available_voices(
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Lista voces disponibles para TTS"""
    try:
        # TODO: Obtener desde configuración o servicio de TTS
        return {
            "voices": [
                {"id": "es", "name": "Español", "language": "es-ES"},
                {"id": "en", "name": "English", "language": "en-US"},
                {"id": "pt", "name": "Português", "language": "pt-BR"}
            ],
            "default": "es",
            "tenant_id": usuario.tenant_id
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo voces: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo voces: {str(e)}"
        )

# =============================================================================
# COMPARACIÓN: VERSIÓN ANTIGUA VS NUEVA
# =============================================================================

"""
# VERSIÓN ANTIGUA (bloqueante):
@router.post("/process-audio")
async def process_audio(...):
    # ❌ Procesamiento síncrono (muy lento)
    result = await procesar_audio_pipeline(...)
    return result  # ❌ Cliente espera minutos

# VERSIÓN NUEVA (con cola):
@router.post("/process-audio")
async def process_audio(...):
    # ✅ Encolar inmediato
    message = enqueue_task(procesar_audio_task, ...)
    return {"status": "queued", "task_id": message.message_id}  # ✅ Respuesta rápida

# BENEFICIOS:
# 1. ✅ Respuesta inmediata (segundos vs minutos)
# 2. ✅ No bloquea el servidor
# 3. ✅ Reintentos automáticos si falla
# 4. ✅ Escalabilidad horizontal
# 5. ✅ Monitoreo de progreso
# 6. ✅ Mejor experiencia de usuario
# 7. ✅ Manejo de picos de carga
"""
