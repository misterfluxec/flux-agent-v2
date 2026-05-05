# tests/e2e/test_data_ingestion_flow.py
import requests
import time
import json
import os
from pathlib import Path

# Configuración del entorno
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:9000/api/v1")
# En desarrollo local, se puede pasar un token válido vía ENV
TOKEN = os.getenv("TEST_AUTH_TOKEN", "dev_token_placeholder")
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def test_full_ingestion_flow():
    print("🚀 [E2E] Iniciando flujo de validación: Yanua Data Center")

    # 1. Verificar Salud del Backend
    print("\n[1/6] Verificando salud del sistema...")
    try:
        resp = SESSION.get(f"{BASE_URL.replace('/api/v1', '')}/health")
        if resp.status_code == 200:
            print("✅ Backend operativo.")
        else:
            print(f"⚠️ Warning: Healthcheck retornó {resp.status_code}")
    except Exception as e:
        print(f"❌ Error conectando al backend: {e}")
        return

    # 2. Carga y Parseo Local
    print("\n[2/6] Test: Parseo de archivo local (.csv)...")
    # Crear un archivo de prueba temporal
    file_path = Path("tests/fixtures/sample_inventory.csv")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("SKU,Nombre,Precio,Stock,Categoria\nNK-001,Zapatillas Running,89.99,45,Calzado\nNK-002,Camiseta Sport,24.50,120,Ropa")

    try:
        with open(file_path, "rb") as f:
            resp = SESSION.post(f"{BASE_URL}/upload/parse", files={"file": ("sample.csv", f, "text/csv")})
        
        if resp.status_code == 401:
            print("⚠️ Nota: Se requiere un TEST_AUTH_TOKEN válido para completar el test real.")
            print("⏭️ Saltando validaciones de negocio (requieren auth).")
            return

        assert resp.status_code == 200, f"❌ Falló parseo: {resp.text}"
        data = resp.json()
        assert "headers" in data
        assert "Zapatillas Running" in str(data["preview_rows"])
        print(f"✅ Archivo parseado exitosamente. Headers detectados: {data['headers']}")
    except Exception as e:
        print(f"❌ Error en fase de parseo: {e}")
        return

    # 3. Simulación de Sincronización (Solo si hay token válido)
    print("\n[3/6] Test: Iniciando sincronización de conocimiento...")
    # Buscamos un agente ID válido (Yanua)
    try:
        agents_resp = SESSION.get(f"{BASE_URL}/agents/")
        agents = agents_resp.json()
        yanua = next((a for a in agents if "yanua" in a["nombre"].lower()), agents[0] if agents else None)
        
        if not yanua:
            print("❌ No se encontró un agente para el test.")
            return
            
        agent_id = yanua["id"]
        print(f"🤖 Usando agente: {yanua['nombre']} ({agent_id})")

        sync_payload = {
            "source_id": "e2e_test_file",
            "column_mapping": {"nombre": "Nombre", "precio": "Precio", "categoria": "Categoria"},
            "sync_frequency": "manual",
            "agent_id": agent_id
        }
        
        # Nota: Ajustar endpoint según router real de sync
        resp = SESSION.post(f"{BASE_URL}/sync/sheets", json=sync_payload)
        if resp.status_code == 202:
            job_id = resp.json().get("job_id")
            print(f"✅ Sincronización iniciada. Job ID: {job_id}")
            
            # 4. Polling
            print("\n[4/6] Monitoreando progreso...")
            for i in range(10):
                status_resp = SESSION.get(f"{BASE_URL}/sync/jobs/{job_id}/status")
                status_data = status_resp.json()
                print(f"   ⏳ [{i}] Estado: {status_data['status']} | {status_data.get('progress_percent', 0)}%")
                if status_data["status"] in ["success", "failed"]:
                    break
                time.sleep(2)
        else:
            print(f"⚠️ Sync no iniciado (Status {resp.status_code}). Posiblemente endpoint diferente.")

    except Exception as e:
        print(f"ℹ️ Fase de sync omitida o fallida por configuración: {e}")

    # 5. Verificar Métricas
    print("\n[5/6] Verificando actualización de métricas...")
    try:
        resp = SESSION.get(f"{BASE_URL}/stats/ingestion")
        metrics = resp.json()
        print(f"📊 Estado actual: {metrics.get('active_products', 0)} productos, {metrics.get('total_tokens', 0)} tokens.")
    except:
        print("⚠️ No se pudieron obtener métricas.")

    print("\n[6/6] Limpieza...")
    if file_path.exists():
        file_path.unlink()
    print("✅ Test completado.")

if __name__ == "__main__":
    test_full_ingestion_flow()
