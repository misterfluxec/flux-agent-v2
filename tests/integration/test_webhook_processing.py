import pytest
import hmac
import hashlib
import httpx
from config import obtener_config

@pytest.mark.asyncio
async def test_webhook_hmac_validation(api_client: httpx.AsyncClient):
    """
    Test Integration 2: Webhook Processing
    Verifica que los webhooks con firmas HMAC inválidas sean rechazados
    en la capa de dependencias antes de procesar payloads.
    """
    config = obtener_config()
    secret = config.evolution_webhook_secret
    
    # Solo ejecutar si el secret está configurado
    if secret:
        payload = '{"event": "messages.upsert", "data": {}}'
        
        # 1. Sin firma
        response = await api_client.post("/api/v1/whatsapp/webhook", json=payload)
        assert response.status_code == 401
        
        # 2. Firma inválida
        headers = {"webhook-signature": "invalid_signature"}
        response = await api_client.post("/api/v1/whatsapp/webhook", json=payload, headers=headers)
        assert response.status_code == 401
        
        # 3. Firma válida
        signature = hmac.new(
            secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        headers = {"webhook-signature": signature}
        
        # El endpoint exacto dependerá del path (e.g. /webhook/evolution o similar)
        # La validación real checará el HMAC. Aquí simulamos el rechazo esperado.
