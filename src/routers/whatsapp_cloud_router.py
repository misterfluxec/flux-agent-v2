import logging
import hashlib
import hmac
import json
from fastapi import APIRouter, Request, Response, HTTPException, status, Depends
from pydantic import BaseModel
import httpx
from typing import Optional

from config import obtener_config
from database import obtener_sesion
from auth import get_tenant_actual
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

logger = logging.getLogger(__name__)
config = obtener_config()

router = APIRouter(prefix="/api/v1/channels/whatsapp_cloud", tags=["WhatsApp Cloud API"])

# =============================================================================
# WEBHOOKS (META OFFICIAL)
# =============================================================================

from fastapi import APIRouter, Request, Response, HTTPException, status, Depends, Query

@router.get("/webhook")
async def verify_webhook(
    request: Request,
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """
    Verificación del Webhook por parte de Meta.
    Meta enviará GET con hub.mode, hub.challenge y hub.verify_token.
    """
    # El verify_token configurado en el panel de Meta. Debería venir de config o BD.
    # Por ahora usamos una variable de entorno o un string estático para el MVP
    EXPECTED_TOKEN = config.whatsapp_verify_token if hasattr(config, "whatsapp_verify_token") else "fluxagent_secret_token"

    if hub_mode == "subscribe" and hub_verify_token == EXPECTED_TOKEN:
        logger.info("Webhook verificado exitosamente por Meta.")
        return Response(content=hub_challenge, status_code=status.HTTP_200_OK)
    
    logger.warning("Fallo en la verificación del Webhook de Meta.")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token de verificación inválido")


@router.post("/webhook")
async def receive_webhook(request: Request):
    """
    Recepción de mensajes y eventos desde Meta.
    """
    body_bytes = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    # Opcional: Verificación de firma (Recomendado en Producción)
    app_secret = getattr(config, "whatsapp_app_secret", None)
    if app_secret and signature:
        expected_sig = "sha256=" + hmac.new(
            app_secret.encode(), body_bytes, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, signature):
            logger.error("Firma de Meta inválida.")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Firma inválida")

    try:
        body = json.loads(body_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload inválido")

    # Aquí se procesaría el payload (identificar tenant, mensaje, etc.)
    # Para el MVP, simplemente aceptamos el evento.
    if body.get("object") == "whatsapp_business_account":
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                if "messages" in value:
                    for message in value["messages"]:
                        logger.info(f"Nuevo mensaje recibido de Meta: {message}")
                        # TODO: Integrar con el procesador del agente
                        
    return Response(content="EVENT_RECEIVED", status_code=status.HTTP_200_OK)


# =============================================================================
# ONBOARDING WIZARD ENDPOINTS
# =============================================================================

class VerifyRequest(BaseModel):
    waba_id: str
    system_user_token: str

@router.post("/verify")
async def verify_meta_account(
    req: VerifyRequest,
    tenant_id: UUID = Depends(get_tenant_actual),
    db: AsyncSession = Depends(obtener_sesion)
):
    """
    Valida el WABA ID y Token ingresados por el usuario llamando a la Graph API de Meta.
    """
    url = f"https://graph.facebook.com/v19.0/{req.waba_id}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params={"access_token": req.system_user_token})
        
        if response.status_code == 200:
            data = response.json()
            # Guardar en BD si es necesario
            return {"status": "success", "message": "Cuenta verificada exitosamente", "data": data}
        else:
            logger.error(f"Error verificando cuenta Meta: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token o WABA ID inválido. Por favor, verifica en Meta Business Suite."
            )

class TestMessageRequest(BaseModel):
    waba_id: str
    phone_number_id: str
    system_user_token: str
    recipient_phone: str

@router.post("/test")
async def send_test_message(
    req: TestMessageRequest,
    tenant_id: UUID = Depends(get_tenant_actual),
    db: AsyncSession = Depends(obtener_sesion)
):
    """
    Envía un mensaje de plantilla "hello_world" de prueba.
    """
    url = f"https://graph.facebook.com/v19.0/{req.phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {req.system_user_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": req.recipient_phone,
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {
                "code": "en_US"
            }
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return {"status": "success", "message": "Mensaje de prueba enviado"}
        else:
            logger.error(f"Error enviando mensaje de prueba: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error enviando mensaje de prueba: {response.text}"
            )
