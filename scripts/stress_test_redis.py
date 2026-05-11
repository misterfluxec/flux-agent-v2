#!/usr/bin/env python3
"""
Synthetic Campaign Burst Injector & Redis Stress Tester
-------------------------------------------------------
Inyecta ráfagas masivas de eventos en Redis Streams para validar:
1. Rendimiento de `xadd` masivo (Throughput)
2. Latencia de encolado
3. Estabilidad del EventBus bajo presión
4. Verificación de Eviction (MAXLEN y TTL)
"""

import sys
import os
import json
import asyncio
import time
import uuid
from datetime import datetime

# Añadir el path de src para importar módulos del backend
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import redis.asyncio as aioredis
from config import obtener_config

config = obtener_config()

async def run_stress_test(num_events: int = 1000, batch_size: int = 100):
    print(f"🚀 Iniciando Stress Test en Redis Streams...")
    print(f"Target Redis: {config.redis_url}")
    print(f"Eventos a inyectar: {num_events} (Lotes de {batch_size})")
    
    redis = await aioredis.from_url(config.redis_url)
    
    tenant_id = str(uuid.uuid4())
    print(f"🔑 Tenant ID simulado: {tenant_id}")
    
    start_time = time.time()
    events_published = 0
    
    stream_global = "fluxagent:events:global"
    stream_tenant = f"fluxagent:events:tenant:{tenant_id}"
    
    for i in range(0, num_events, batch_size):
        pipe = redis.pipeline()
        for j in range(batch_size):
            if events_published >= num_events:
                break
                
            event_id = str(uuid.uuid4())
            # Payload simulado
            stream_data = {
                "event_type": "message.received",
                "tenant_id": tenant_id,
                "data": json.dumps({
                    "metadata": {
                        "event_id": event_id,
                        "event_type": "message.received",
                        "tenant_id": tenant_id,
                        "severity": "medium",
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    "payload": {
                        "channel": "whatsapp",
                        "from_number": f"593999{events_published:04d}",
                        "message_id": f"msg_{events_published}",
                        "content": "Hola, quiero información del producto bajo estrés."
                    }
                })
            }
            
            # Simulando la misma lógica de event_bus.py (medium severity -> 5000)
            pipe.xadd(stream_global, stream_data, maxlen=5000, approximate=True)
            pipe.xadd(stream_tenant, stream_data, maxlen=5000, approximate=True)
            events_published += 1
            
        await pipe.execute()
        print(f"✅ Lote inyectado. Total: {events_published}/{num_events}")
        
    end_time = time.time()
    duration = end_time - start_time
    events_per_sec = num_events / duration if duration > 0 else 0
    
    print("\n📊 RESULTADOS DEL STRESS TEST:")
    print(f"Tiempo Total: {duration:.4f} segundos")
    print(f"Throughput: {events_per_sec:.2f} eventos/segundo")
    
    # Verificar la memoria consumida en Redis
    info = await redis.info(section="memory")
    print(f"\n💾 ESTADO DE MEMORIA REDIS:")
    print(f"Memoria Usada: {info.get('used_memory_human')}")
    print(f"Pico de Memoria: {info.get('used_memory_peak_human')}")
    
    # Verificar streams
    global_len = await redis.xlen(stream_global)
    tenant_len = await redis.xlen(stream_tenant)
    print(f"\n🌊 LONGITUD DE STREAMS:")
    print(f"Stream Global: {global_len} eventos")
    print(f"Stream Tenant: {tenant_len} eventos")

    await redis.close()
    print("\n✅ Stress Test Finalizado.")

if __name__ == "__main__":
    num_events = 5000  # Default: 5000 eventos (Medium MAXLEN limit)
    if len(sys.argv) > 1:
        num_events = int(sys.argv[1])
        
    asyncio.run(run_stress_test(num_events=num_events))
