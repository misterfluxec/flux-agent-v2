from typing import Dict, Any, List
from pydantic import BaseModel
import time

class DependencyHealth(BaseModel):
    name: str
    status: str # "UP", "DOWN", "DEGRADED"
    latency_ms: int
    error: str = None

class RuntimeHealthReport(BaseModel):
    status: str # "HEALTHY", "DEGRADED", "UNHEALTHY"
    uptime_seconds: int
    dependencies: List[DependencyHealth]
    active_agents: int
    deadlocked_agents: int
    memory_usage_mb: float

class RuntimeHealth:
    """
    Health check integral del sistema operativo de agentes (Sprint D.2E)
    """
    def __init__(self, redis_client=None, ollama_client=None):
        self.redis = redis_client
        self.ollama = ollama_client
        self.start_time = time.time()
        
    async def check_redis(self) -> DependencyHealth:
        start = time.time()
        try:
            if self.redis:
                await self.redis.ping()
            latency = int((time.time() - start) * 1000)
            return DependencyHealth(name="redis", status="UP", latency_ms=latency)
        except Exception as e:
            return DependencyHealth(name="redis", status="DOWN", latency_ms=0, error=str(e))
            
    async def check_ollama(self) -> DependencyHealth:
        start = time.time()
        try:
            # TODO: Real check to Ollama
            latency = int((time.time() - start) * 1000)
            return DependencyHealth(name="ollama", status="UP", latency_ms=latency)
        except Exception as e:
            return DependencyHealth(name="ollama", status="DOWN", latency_ms=0, error=str(e))

    async def get_health_report(self) -> RuntimeHealthReport:
        redis_health = await self.check_redis()
        ollama_health = await self.check_ollama()
        
        deps = [redis_health, ollama_health]
        
        status = "HEALTHY"
        if any(d.status == "DOWN" for d in deps):
            status = "UNHEALTHY"
        elif any(d.status == "DEGRADED" for d in deps):
            status = "DEGRADED"
            
        return RuntimeHealthReport(
            status=status,
            uptime_seconds=int(time.time() - self.start_time),
            dependencies=deps,
            active_agents=0, # TODO: Connect to AgentRegistry
            deadlocked_agents=0, # TODO: Check Agent Execution states
            memory_usage_mb=0.0 # TODO: psutil
        )
