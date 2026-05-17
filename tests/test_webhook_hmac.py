import sys
import os

# Ajustar ruta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from fastapi.testclient import TestClient
from main import app
import hmac
import hashlib

client = TestClient(app)

def test_webhook_no_signature():
    response = client.post("/api/v1/whatsapp/webhook", json={"event": "messages.upsert"})
    print("Test No Signature:", response.status_code, response.json())
    assert response.status_code == 401
    assert "Missing webhook signature" in response.text

def test_webhook_invalid_signature():
    headers = {"webhook-signature": "bad_signature"}
    response = client.post("/api/v1/whatsapp/webhook", json={"event": "messages.upsert"}, headers=headers)
    print("Test Invalid Signature:", response.status_code, response.json())
    assert response.status_code == 401
    assert "Invalid webhook signature" in response.text

def test_webhook_valid_signature():
    payload = b'{"event": "messages.upsert", "data": {}}'
    secret = b'default-secret-replace-in-prod'
    expected_mac = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    
    headers = {"webhook-signature": expected_mac, "Content-Type": "application/json"}
    
    # Esto pasará la autenticación pero será ignorado por el router al no haber msg
    response = client.post("/api/v1/whatsapp/webhook", content=payload, headers=headers)
    print("Test Valid Signature:", response.status_code, response.json())
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"

if __name__ == "__main__":
    test_webhook_no_signature()
    test_webhook_invalid_signature()
    test_webhook_valid_signature()
    print("✅ Todos los tests de webhook pasaron con éxito.")
