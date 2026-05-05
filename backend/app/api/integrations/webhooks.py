from fastapi import APIRouter, Request, HTTPException, Header
import hmac
import hashlib
import logging

router = APIRouter(prefix="/integrations", tags=["Conectores"])
logger = logging.getLogger(__name__)

def verify_shopify_hmac(payload: bytes, hmac_header: str, secret: str) -> bool:
    if not hmac_header: return False
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, hmac_header)

def verify_woo_signature(payload: bytes, signature: str, secret: str) -> bool:
    if not signature: return False
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

@router.post("/shopify/webhook/{tenant_id}")
async def shopify_webhook(tenant_id: str, request: Request, x_shopify_hmac: str = Header(None)):
    body = await request.body()
    # Verificar HMAC (en prod: obtener secret desde tenant config en BD)
    # if not verify_shopify_hmac(body, x_shopify_hmac, "SHOPIFY_WEBHOOK_SECRET"):
    #     raise HTTPException(401, "Invalid HMAC")
    
    data = await request.json()
    topic = request.headers.get("X-Shopify-Topic")
    logger.info(f"📦 Shopify webhook received for tenant {tenant_id}: {topic}")
    return {"status": "received", "topic": topic}

@router.post("/woocommerce/webhook/{tenant_id}")
async def woo_webhook(tenant_id: str, request: Request, x_woo_signature: str = Header(None)):
    body = await request.body()
    # if not verify_woo_signature(body, x_woo_signature, "WOO_WEBHOOK_SECRET"):
    #     raise HTTPException(401, "Invalid signature")
    
    data = await request.json()
    event = request.headers.get("X-WC-Webhook-Topic")
    logger.info(f"🛒 WooCommerce webhook received for tenant {tenant_id}: {event}")
    return {"status": "received", "event": event}
