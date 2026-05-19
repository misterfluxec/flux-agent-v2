from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Depends
from uuid import UUID
import httpx
import logging
import hmac
import hashlib

from config import obtener_config
from database import SesionLocal, configurar_rls
from sqlalchemy import text
from agents.base_agent import ContextoAgente
from agents.sales_agent import AgentDeVentas

logger = logging.getLogger(__name__)
config = obtener_config()

router = APIRouter(prefix="/api/v1/whatsapp", tags=["WhatsApp"])

EVOLUTION_INSTANCE = "flux_agent_final"

async def procesar_mensaje_whatsapp(tenant_id: UUID, session_id: str, mensaje: str, instance_name: str, remote_jid: str):
    logger.info(f"[WA] Procesando mensaje | jid={remote_jid} | msg='{mensaje[:60]}'")

    # 1. Typing indicator
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{config.evolution_api_url}/chat/sendPresence/{instance_name}",
                headers={"apikey": config.evolution_api_key},
                json={"number": remote_jid, "presence": "composing", "delay": 8000},
            )
            logger.info("[WA] Typing indicator enviado")
    except Exception as e:
        logger.warning(f"[WA] No se pudo enviar typing: {e}")

    # 2. Procesar con IA usando sesión limpia
    texto_respuesta = "Lo siento, tuve un problema técnico. ¿Puedes repetir tu consulta?"
    try:
        async with SesionLocal() as db:
            await configurar_rls(db, tenant_id)

            res_agent = await db.execute(text("""
                SELECT name, mood, personality, gender, business_type, instructions, model, temperature, max_tokens, sales_script
                FROM agents WHERE tenant_id = :tid LIMIT 1
            """), {"tid": str(tenant_id)})
            agente_db = res_agent.fetchone()

            if agente_db:
                config_agente = {
                    "name": agente_db.name,
                    "mood": agente_db.mood,
                    "personality": agente_db.personality,
                    "gender": agente_db.gender,
                    "business_type": agente_db.business_type,
                    "instructions": agente_db.instructions,
                    "model": agente_db.model,
                    "temperature": agente_db.temperature,
                    "max_tokens": agente_db.max_tokens,
                    "sales_script": agente_db.sales_script
                }
            else:
                config_agente = {
                    "name": "FluxBot",
                    "mood": "profesional",
                    "model": "qwen2.5:3b",
                    "temperature": 0.7,
                    "max_tokens": 512,
                }

            contexto = ContextoAgente(
                tenant_id=tenant_id,
                agent_id=None,
                session_id=session_id,
                mensaje_usuario=mensaje,
                configuracion=config_agente,
            )

            agente = AgentDeVentas()
            try:
                respuesta_ai = await agente.procesar(contexto, sesion=db)
                texto_respuesta = respuesta_ai.contenido
                logger.info(f"[WA] Respuesta generada ({len(texto_respuesta)} chars)")
            except Exception as exc:
                logger.error(f"[WA] Error en agente IA: {exc}", exc_info=True)
            finally:
                await agente.cerrar()

            await db.commit()

    except Exception as exc:
        logger.error(f"[WA] Error crítico en sesión DB: {exc}", exc_info=True)

    # 3. Enviar respuesta a WhatsApp
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{config.evolution_api_url}/message/sendText/{instance_name}",
                headers={"apikey": config.evolution_api_key},
                json={
                    "number": remote_jid,
                    "text": texto_respuesta,
                    "delay": 1000,
                },
            )
            logger.info(f"[WA] Mensaje enviado | status={resp.status_code}")
    except Exception as e:
        logger.error(f"[WA] Error enviando respuesta a Evolution: {e}", exc_info=True)

async def verify_webhook_signature(request: Request):
    """Verifica la firma HMAC-SHA256 enviada por Evolution API"""
    signature = request.headers.get("webhook-signature")
    if not signature:
        logger.warning("[WA] Intento de acceso a webhook sin firma")
        raise HTTPException(status_code=401, detail="Missing webhook signature")
    
    raw_body = await request.body()
    secret = config.evolution_webhook_secret.encode('utf-8')
    expected_mac = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(expected_mac, signature):
        logger.warning("[WA] Firma de webhook inválida")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

from core.security.rate_limiter import limiter

@router.post("/webhook", summary="Recibe mensajes desde Evolution API", dependencies=[Depends(verify_webhook_signature)])
@limiter.limit("10/second")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    payload = await request.json()
    
    if payload.get("event") != "messages.upsert":
        return {"status": "ignored", "reason": "not a message event"}

    data = payload.get("data", {})
    message = data.get("message", {})
    key = data.get("key", {})

    if key.get("fromMe") or not message:
        return {"status": "ignored", "reason": "fromMe or empty message"}

    instance_name = payload.get("instance")
    remote_jid = key.get("remoteJid")
    
    texto_usuario = message.get("conversation") or message.get("extendedTextMessage", {}).get("text")
    if not texto_usuario:
        return {"status": "ignored", "reason": "no text content"}

    numero_telefono = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid

    # Para pruebas, usamos un tenant default. 
    tenant_default = UUID("11111111-1111-1111-1111-111111111111")
    session_id = f"wa-{numero_telefono}"

    background_tasks.add_task(
        procesar_mensaje_whatsapp,
        tenant_default,
        session_id,
        texto_usuario,
        instance_name,
        remote_jid
    )

    return {"status": "received"}

@router.get("/qr", summary="Obtiene el QR code de la instancia para escanear")
async def whatsapp_get_qr():
    """Retorna la imagen QR en base64 para conectar WhatsApp."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(
                f"{config.evolution_api_url}/instance/connect/{EVOLUTION_INSTANCE}",
                headers={"apikey": config.evolution_api_key},
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Evolution API error: {resp.text}")
            data = resp.json()
            return data
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"No se pudo conectar a Evolution API: {exc}")

@router.get("/instance-status", summary="Estado de conexión de la instancia de WhatsApp")
async def whatsapp_instance_status():
    """Retorna el status actual de conexión (open, connecting, close)."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                f"{config.evolution_api_url}/instance/fetchInstances",
                headers={"apikey": config.evolution_api_key},
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail="Error al consultar Evolution API")
            instances = resp.json()
            target = next((i for i in instances if i.get("name") == EVOLUTION_INSTANCE), None)
            if not target:
                raise HTTPException(status_code=404, detail=f"Instancia '{EVOLUTION_INSTANCE}' no encontrada")
            return {
                "instance": EVOLUTION_INSTANCE,
                "connectionStatus": target.get("connectionStatus"),
                "ownerJid": target.get("ownerJid"),
                "profileName": target.get("profileName"),
            }
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"No se pudo conectar a Evolution API: {exc}")

@router.delete("/logout", summary="Cierra sesión en la instancia de WhatsApp")
async def whatsapp_logout():
    """Cierra sesión de WhatsApp en la instancia actual."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.delete(
                f"{config.evolution_api_url}/instance/logout/{EVOLUTION_INSTANCE}",
                headers={"apikey": config.evolution_api_key},
            )
            if resp.status_code not in (200, 201):
                logger.warning(f"Error al hacer logout en Evolution API: {resp.text}")
            return {"status": "success", "message": "Sesión cerrada correctamente"}
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"No se pudo conectar a Evolution API: {exc}")
