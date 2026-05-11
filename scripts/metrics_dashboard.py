#!/usr/bin/env python3
"""
FluxAgent V2 - Operational Metrics Dashboard
--------------------------------------------
Imprime en consola las métricas obligatorias para la validación operacional:
- Redis Memory (used_memory_peak, used_memory)
- Stream Lengths (XLEN)
- Consumer Lag (pendientes en XPENDING)
"""

import sys
import os
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import redis.asyncio as aioredis
from config import obtener_config

config = obtener_config()

async def get_metrics():
    print("📊 RECOPILANDO MÉTRICAS OPERACIONALES...")
    redis = await aioredis.from_url(config.redis_url)
    
    # 1. Memoria Redis
    info = await redis.info(section="memory")
    print("\n[ Redis Memory ]")
    print(f"  Used Memory:      {info.get('used_memory_human')}")
    print(f"  Used Memory Peak: {info.get('used_memory_peak_human')}")
    print(f"  Max Memory:       {info.get('maxmemory_human', 'No limit')}")
    print(f"  Evicted Keys:     {info.get('evicted_keys')}")
    
    # 2. Streams Info
    print("\n[ Redis Streams (Top 5 by size) ]")
    cursor = 0
    streams = []
    while True:
        cursor, keys = await redis.scan(cursor=cursor, match="fluxagent:events:*", count=100)
        for key in keys:
            if await redis.type(key) == b"stream" or await redis.type(key) == "stream":
                # En decode_responses=True, las keys son strings y types son strings. 
                # Pero no le pusimos decode_responses=True, asi que son bytes.
                try:
                    length = await redis.xlen(key)
                    streams.append((key.decode(), length))
                except Exception:
                    pass
        if cursor == 0 or cursor == b"0" or cursor == "0":
            break
            
    streams.sort(key=lambda x: x[1], reverse=True)
    for stream, length in streams[:5]:
        print(f"  {stream}: {length} eventos")
        
    # 3. Consumer Lag (XPENDING global)
    print("\n[ Consumer Groups Lag (fluxagent:processors) ]")
    stream_global = "fluxagent:events:global"
    try:
        pending = await redis.xpending(stream_global, "fluxagent:processors")
        if pending and pending["pending"] > 0:
            print(f"  Consumer Lag: {pending['pending']} eventos pendientes")
            print(f"  Consumers activos: {pending['consumers']}")
        else:
            print("  Consumer Lag: 0 (Procesamiento al día)")
    except Exception as e:
        print("  Consumer Group no encontrado o inactivo.")
        
    await redis.close()
    print("\n✅ Métricas recopiladas con éxito.")

if __name__ == "__main__":
    asyncio.run(get_metrics())
