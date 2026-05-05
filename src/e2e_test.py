import asyncio
import httpx
from jose import jwt
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"
JWT_SECRET = "cambiar_en_produccion_jwt_secret"
TENANT_ID = "11111111-1111-1111-1111-111111111111"

def generate_test_token():
    payload = {
        "sub": "test@example.com",
        "tenant_id": TENANT_ID,
        "exp": datetime.utcnow() + timedelta(minutes=60),
        "rol": "admin",
        "nombre": "Test User"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

async def run_tests():
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        # 1. Health check
        print("Testing /health...")
        r = await client.get("http://localhost:8000/health")
        print("Health Status:", r.status_code, r.json())
        
        # 2. Get quota config
        print("\nTesting /quota/my-config...")
        r = await client.get(f"{BASE_URL}/quota/my-config", headers=headers)
        print("Config Status:", r.status_code, r.json())
        
        # 3. Update BYOA
        print("\nTesting PUT /quota/byoa...")
        data = {
            "cloud_token": "sk-abc123def456ghi789jkl012mno345",
            "phone_number_id": "123456789",
            "waba_id": "987654321",
            "admin_whatsapp_number": "1234567890"
        }
        r = await client.put(f"{BASE_URL}/quota/byoa", json=data, headers=headers)
        print("BYOA Update Status:", r.status_code, r.json())

        # 4. Get quota config again to verify update
        print("\nTesting /quota/my-config after update...")
        r = await client.get(f"{BASE_URL}/quota/my-config", headers=headers)
        print("Config Status:", r.status_code, r.json())

        # 5. Test send low quota alert
        print("\nTesting POST /quota/send-low-quota-alert...")
        r = await client.post(f"{BASE_URL}/quota/send-low-quota-alert", headers=headers)
        print("Alert Status:", r.status_code, r.json())

asyncio.run(run_tests())
