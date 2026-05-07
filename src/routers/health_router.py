# =============================================================================
# HEALTH CHECK ROUTER - MONITOREO DE CIRCUIT BREAKERS
# =============================================================================

from fastapi import APIRouter
from datetime import datetime
import time
from typing import Dict, Any

from core.resilience.circuit_breaker import _circuit_breakers

router = APIRouter(prefix="/health", tags=["health"])

# Variable global para tracking de uptime
app_start_time = time.time()

@router.get("")
async def system_health():
    """Endpoint de salud del sistema con estado de circuit breakers"""
    
    # Obtener estado de todos los circuit breakers registrados
    circuits_status = {}
    for name, breaker in _circuit_breakers.items():
        circuits_status[name] = {
            "state": breaker.state.value,
            "failureCount": breaker.failure_count,
            "lastFailureTime": breaker.last_failure_time.isoformat() if breaker.last_failure_time else None,
            "recoveryTimeout": breaker.recovery_timeout,
        }
    
    # Determinar estado general del sistema
    open_circuits = [c for c in circuits_status.values() if c["state"] == "OPEN"]
    
    if len(open_circuits) > 2:
        status = "unhealthy"
    elif len(open_circuits) > 0:
        status = "degraded"
    else:
        status = "healthy"
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "circuits": circuits_status,
        "version": "1.0.0",  # Podría venir de config
        "uptime": int(time.time() - app_start_time),
    }

@router.get("/ping")
async def ping():
    """Endpoint simple para verificación de conectividad"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@router.get("/circuits")
async def circuits_detail():
    """Endpoint detallado con información de cada circuit breaker"""
    circuits_status = {}
    for name, breaker in _breakers.items():
        circuits_status[name] = {
            "state": breaker.state.value,
            "failureCount": breaker.failure_count,
            "lastFailureTime": breaker.last_failure_time.isoformat() if breaker.last_failure_time else None,
            "recoveryTimeout": breaker.recovery_timeout,
            "successCount": breaker.success_count,
            "lastSuccessTime": breaker.last_success_time.isoformat() if breaker.last_success_time else None,
        }
    
    return {
        "circuits": circuits_status,
        "total": len(circuits_status),
        "timestamp": datetime.utcnow().isoformat(),
    }
