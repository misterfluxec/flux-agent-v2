import logging
import os
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, status, BackgroundTasks
from sqlalchemy import text
import httpx

from routers.chat_router import procesar_mensaje_entrante
from database import sesion_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["Webhooks Públicos"],
)

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://172.19.0.6:8080")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "fluxkey123")


@router.post("/whatsapp")
async def evolution_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Recibe eventos de Evolution API.
    Identifica la instancia y procesa mensajes entrantes de forma segura.
    """
    # 0. Validar Seguridad — leer directamente del header (case-insensitive)
    # FastAPI normaliza "apikey" -> "api-key" en el alias, por eso leemos manualmente
    apikey = (
        request.headers.get("apikey")
        or request.headers.get("api-key")
        or request.headers.get("x-api-key")
    )

    if apikey != EVOLUTION_API_KEY:
        logger.warning(f"Intento de acceso no autorizado con apikey: {apikey}")
        raise HTTPException(status_code=401, detail="Invalid API Key")

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = data.get("event")
    instancia_nombre = data.get("instance")

    if not event or not instancia_nombre:
        return {"status": "ignored", "reason": "Missing event or instance"}

    logger.info(f"Webhook recibido [{event}] para instancia: {instancia_nombre}")

    if event.lower().replace("_", ".") == "messages.upsert":
        # Extraer data del mensaje
        msg_data = data.get("data", {})
        message_info = msg_data.get("message", {})
        key = msg_data.get("key", {})
        
        # Ignorar mensajes enviados por nosotros mismos o grupos
        if key.get("fromMe", False) or "@g.us" in key.get("remoteJid", ""):
            return {"status": "ignored", "reason": "fromMe or group message"}

        telefono_cliente = key.get("remoteJid", "").split("@")[0]
        
        # 1. Detectar type de mensaje y extraer contenido
        mensaje_texto = message_info.get("conversation")
        if not mensaje_texto and "extendedTextMessage" in message_info:
            mensaje_texto = message_info["extendedTextMessage"].get("text")
            
        es_audio = "audioMessage" in message_info
        es_imagen = "imageMessage" in message_info
            
        if not mensaje_texto and not es_audio and not es_imagen:
            return {"status": "ignored", "reason": "No text, audio or image content"}

        # 1. Buscar a qué tenant y agent pertenece esta instancia
        async with sesion_db() as db:
            res_inst = await db.execute(text("""
                SELECT tenant_id, agent_id FROM canales_config
                WHERE canal = 'whatsapp' AND instancia_nombre = :instancia AND estado = 'activo'
            """), {"instancia": instancia_nombre})
            instancia_config = res_inst.fetchone()

        if not instancia_config:
            logger.warning(f"Instancia {instancia_nombre} no encontrada o inactiva en la BD.")
            return {"status": "error", "reason": "Instance not configured or inactive"}

        tenant_id = instancia_config.tenant_id
        agent_id = instancia_config.agent_id

        # Si la instancia no tiene un agent_id específico, usamos el router inteligente
        if not agent_id:
            try:
                from services.agent_router import resolve_agent_for_channel
                # Pasamos el mensaje_texto como intento para enrutamiento
                agent_id = await resolve_agent_for_channel(str(tenant_id), "whatsapp", mensaje_texto)
            except ValueError as e:
                logger.error(f"Tenant {tenant_id} no tiene agentes activos: {e}")
                return {"status": "error", "reason": "No active agents"}

        # 2. Agregar el procesamiento pesado a BackgroundTasks
        background_tasks.add_task(
            procesar_y_responder_whatsapp_bg,
            tenant_id=tenant_id,
            agent_id=agent_id,
            telefono_cliente=telefono_cliente,
            mensaje_texto=mensaje_texto,
            instancia_nombre=instancia_nombre,
            es_audio=es_audio,
            es_imagen=es_imagen,
            msg_data=msg_data
        )

        return {"status": "queued"}

    return {"status": "ignored", "reason": f"Unhandled event {event}"}


async def procesar_y_responder_whatsapp_bg(
    tenant_id, agent_id, telefono_cliente, mensaje_texto, instancia_nombre, es_audio, es_imagen, msg_data
):
    """Procesa RAG, llamadas a LLM y multimedia en segundo plano para no bloquear el Webhook."""
    try:
        from core.plan_manager import PlanManager
        from services.whatsapp_sender import send_presence
        
        # Enviar presencia escribiendo por 15 segundos para dar feedback al usuario
        if not es_audio and not es_imagen:
            await send_presence(instancia_nombre, telefono_cliente, delay=15000, presence="composing")
            
        async with sesion_db(tenant_id) as db:
            try:
                # Si es mensaje de texto normal
                if not es_audio and not es_imagen:
                    await PlanManager.check_limite_diario_tenant(tenant_id, db, "messages", 1)
                
                if es_audio:
                    await PlanManager.check_feature_tenant(tenant_id, db, "stt")
                    
                if es_imagen:
                    await PlanManager.check_feature_tenant(tenant_id, db, "vision")
                    await PlanManager.check_limite_diario_tenant(tenant_id, db, "images", 1)

            except Exception as e:
                logger.warning(f"Tenant {tenant_id} límite/feature falló: {e}")
                msg_error = "Lo sentimos, el asistente ha excedido su límite o el plan no soporta este type de mensaje."
                await enviar_mensaje_whatsapp(instancia_nombre, telefono_cliente, msg_error)
                return

        # 3. Extraer Media y Procesar Multimedia
        if es_audio or es_imagen:
            try:
                from services.multimedia import ServicioMultimedia
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp_media = await client.post(
                        f"{EVOLUTION_API_URL}/chat/getBase64FromMediaMessage/{instancia_nombre}",
                        headers={"apikey": EVOLUTION_API_KEY},
                        json={"message": msg_data}
                    )
                    resp_media.raise_for_status()
                    media_data = resp_media.json()
                    base64_str = media_data.get("base64")

                if not base64_str:
                    raise ValueError("No se pudo obtener el base64 del medio")

                if es_audio:
                    mensaje_texto = await ServicioMultimedia.transcribir_audio(base64_str)
                    if not mensaje_texto:
                        raise ValueError("No se pudo transcribir el audio")
                    PlanManager.registrar_uso(str(tenant_id), "audio_sec", 15)
                elif es_imagen:
                    mensaje_texto = await ServicioMultimedia.analizar_imagen(base64_str)
                    if not mensaje_texto:
                        raise ValueError("No se pudo analizar la imagen")
                    PlanManager.registrar_uso(str(tenant_id), "images", 1)

            except Exception as e:
                logger.error(f"Error procesando multimedia: {e}")
                await enviar_mensaje_whatsapp(instancia_nombre, telefono_cliente, "Ocurrió un error al procesar tu archivo.")
                return

        # 4. Procesar el mensaje (RAG + Ollama)
        respuesta = await procesar_mensaje_entrante(
            tenant_id=tenant_id,
            agent_id=agent_id,
            canal="whatsapp",
            lead_externo_id=telefono_cliente,
            mensaje_texto=mensaje_texto,
            instancia_nombre=instancia_nombre
        )

        # 5 y 6. Enviar la respuesta vía Evolution API
        has_tts = False
        if es_audio:
            async with sesion_db(tenant_id) as db:
                try:
                    await PlanManager.check_feature_tenant(tenant_id, db, "tts")
                    has_tts = True
                except Exception:
                    pass
                    
        if es_audio and has_tts:
            try:
                from services.multimedia import ServicioMultimedia
                from services.whatsapp_sender import send_whatsapp_message
                audio_b64 = await ServicioMultimedia.sintetizar_voz(respuesta)
                await send_whatsapp_message(
                    instancia_nombre, 
                    telefono_cliente, 
                    respuesta, 
                    audio_b64
                )
            except Exception as e:
                logger.error(f"Error enviando TTS: {e}")
                await enviar_mensaje_whatsapp(instancia_nombre, telefono_cliente, respuesta)
        else:
            await enviar_mensaje_whatsapp(instancia_nombre, telefono_cliente, respuesta)
        
        PlanManager.registrar_uso(str(tenant_id), "messages", 1)

    except Exception as e:
        logger.error(f"Error procesando mensaje en background: {e}", exc_info=True)
        try:
            await enviar_mensaje_whatsapp(instancia_nombre, telefono_cliente, "Ha ocurrido un error temporal procesando su mensaje.")
        except:
            pass


async def enviar_mensaje_whatsapp(instancia_nombre: str, numero: str, texto: str):
    """Llama a Evolution API para responder."""
    if not EVOLUTION_API_KEY:
        return
        
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "number": numero,
        "text": texto
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{EVOLUTION_API_URL}/message/sendText/{instancia_nombre}",
                headers=headers,
                json=payload
            )
            if resp.status_code not in (200, 201):
                logger.error(f"Error enviando MSJ en Evolution API: {resp.text}")
    except Exception as e:
        logger.error(f"Error HTTP hacia Evolution API: {e}")
