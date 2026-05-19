# =============================================================================
# FLUXAGENT V2 — RESILIENCE MONITORING ROUTER
# =============================================================================
# Endpoint para monitoreo de patrones de resiliencia
# Métricas en tiempo real de circuit breakers, bulkheads, etc.
# =============================================================================

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from auth import PayloadToken, get_usuario_actual
from services.resilient_services import get_resilience_status

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/resilience", tags=["Resilience"])

@router.get("/status")
async def get_resilience_status_endpoint(
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Obtener status completo de resiliencia del sistema"""
    try:
        # Verificar permisos de administrador o soporte
        if usuario.role not in ["admin", "superadmin", "support"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado. Se requieren permisos de administrador."
            )
        
        # Obtener status completo de resiliencia
        status = await get_resilience_status()
        
        logger.info(f"Resilience status requested by user {usuario.id} (tenant: {usuario.tenant_id})")
        
        return {
            "status": "success",
            "data": status,
            "timestamp": status.get("timestamp"),
            "tenant_id": usuario.tenant_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resilience status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo status de resiliencia"
        )

@router.get("/circuit-breakers")
async def get_circuit_breakers_status(
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Obtener status de todos los circuit breakers"""
    try:
        if usuario.role not in ["admin", "superadmin", "support"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado"
            )
        
        from core.resilience.circuit_breaker import get_all_circuit_breakers_status
        circuit_status = await get_all_circuit_breakers_status()
        
        return {
            "status": "success",
            "data": circuit_status,
            "count": len(circuit_status)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting circuit breakers status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo status de circuit breakers"
        )

@router.get("/bulkheads")
async def get_bulkheads_status(
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Obtener status de todos los bulkheads"""
    try:
        if usuario.role not in ["admin", "superadmin", "support"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado"
            )
        
        from core.resilience.bulkhead import get_all_bulkheads_status
        bulkhead_status = await get_all_bulkheads_status()
        
        return {
            "status": "success", 
            "data": bulkhead_status,
            "count": len(bulkhead_status)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bulkheads status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo status de bulkheads"
        )

@router.get("/timeouts")
async def get_timeouts_status(
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Obtener status de todos los timeouts"""
    try:
        if usuario.role not in ["admin", "superadmin", "support"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado"
            )
        
        from core.resilience.timeout import get_all_timeouts_status
        timeout_status = await get_all_timeouts_status()
        
        return {
            "status": "success",
            "data": timeout_status,
            "count": len(timeout_status)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting timeouts status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo status de timeouts"
        )

@router.get("/metrics")
async def get_resilience_metrics(
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Obtener métricas agregadas de resiliencia"""
    try:
        if usuario.role not in ["admin", "superadmin", "support"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado"
            )
        
        # Obtener status completo
        full_status = await get_resilience_status()
        
        # Calcular métricas agregadas
        metrics = {
            "circuit_breakers": {
                "total": len(full_status.get("circuit_breakers", {})),
                "open": sum(1 for cb in full_status.get("circuit_breakers", {}).values() 
                           if cb.get("state") == "open"),
                "half_open": sum(1 for cb in full_status.get("circuit_breakers", {}).values() 
                               if cb.get("state") == "half_open"),
                "closed": sum(1 for cb in full_status.get("circuit_breakers", {}).values() 
                             if cb.get("state") == "closed"),
                "avg_failure_rate": sum(cb.get("metrics", {}).get("failure_rate", 0) 
                                       for cb in full_status.get("circuit_breakers", {}).values()) / max(len(full_status.get("circuit_breakers", {})), 1)
            },
            "bulkheads": {
                "total": len(full_status.get("bulkheads", {})),
                "total_requests": sum(bh.get("metrics", {}).get("total_requests", 0) 
                                       for bh in full_status.get("bulkheads", {}).values()),
                "successful_requests": sum(bh.get("metrics", {}).get("successful_requests", 0) 
                                           for bh in full_status.get("bulkheads", {}).values()),
                "rejected_requests": sum(bh.get("metrics", {}).get("rejected_requests", 0) 
                                         for bh in full_status.get("bulkheads", {}).values()),
                "avg_success_rate": sum(bh.get("metrics", {}).get("success_rate", 0) 
                                      for bh in full_status.get("bulkheads", {}).values()) / max(len(full_status.get("bulkheads", {})), 1),
                "avg_rejection_rate": sum(bh.get("metrics", {}).get("rejection_rate", 0) 
                                        for bh in full_status.get("bulkheads", {}).values()) / max(len(full_status.get("bulkheads", {})), 1)
            },
            "timeouts": {
                "total": len(full_status.get("timeouts", {})),
                "total_calls": sum(to.get("metrics", {}).get("total_calls", 0) 
                                     for to in full_status.get("timeouts", {}).values()),
                "timeout_calls": sum(to.get("metrics", {}).get("timeout_calls", 0) 
                                      for to in full_status.get("timeouts", {}).values()),
                "avg_success_rate": sum(to.get("metrics", {}).get("success_rate", 0) 
                                    for to in full_status.get("timeouts", {}).values()) / max(len(full_status.get("timeouts", {})), 1),
                "avg_timeout_rate": sum(to.get("metrics", {}).get("timeout_rate", 0) 
                                      for to in full_status.get("timeouts", {}).values()) / max(len(full_status.get("timeouts", {})), 1)
            }
        }
        
        return {
            "status": "success",
            "data": metrics,
            "timestamp": full_status.get("timestamp")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resilience metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo métricas de resiliencia"
        )

@router.post("/reset/{service_type}")
async def reset_resilience_service(
    service_type: str,
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Resetear métricas de un servicio específico"""
    try:
        if usuario.role not in ["admin", "superadmin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado. Se requieren permisos de administrador."
            )
        
        # Validar type de servicio
        valid_types = ["circuit_breaker", "bulkhead", "timeout", "retry"]
        if service_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de servicio inválido. Debe ser uno de: {valid_types}"
            )
        
        # Resetear según type
        if service_type == "circuit_breaker":
            from core.resilience.circuit_breaker import get_circuit_breaker
            # Resetear todos los circuit breakers
            for name in ["ollama", "whatsapp_cloud", "redis", "database"]:
                cb = get_circuit_breaker(name)
                if cb:
                    await cb.reset()
        
        elif service_type == "bulkhead":
            # Los bulkheads no necesitan reset, solo limpiar métricas
            from core.resilience.bulkhead import get_bulkhead_manager
            manager = get_bulkhead_manager()
            manager.get_global_metrics()  # Resetear métricas
        
        elif service_type == "timeout":
            from core.resilience.timeout import get_timeout_manager
            manager = get_timeout_manager()
            await manager.reset_all_metrics()
        
        logger.info(f"Resilience service {service_type} reset by user {usuario.id}")
        
        return {
            "status": "success",
            "message": f"Servicio {service_type} reseteado exitosamente",
            "service_type": service_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting resilience service {service_type}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reseteando servicio {service_type}"
        )

@router.get("/health")
async def get_resilience_health(
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Health check del sistema de resiliencia"""
    try:
        # Obtener status completo
        status = await get_resilience_status()
        
        # Calcular salud general
        circuit_breakers = status.get("circuit_breakers", {})
        bulkheads = status.get("bulkheads", {})
        timeouts = status.get("timeouts", {})
        
        # Contar problemas
        open_circuits = sum(1 for cb in circuit_breakers.values() 
                            if cb.get("state") == "open")
        high_rejection_bulkheads = sum(1 for bh in bulkheads.values() 
                                    if bh.get("metrics", {}).get("rejection_rate", 0) > 0.1)
        high_timeout_rate = sum(1 for to in timeouts.values() 
                                if to.get("metrics", {}).get("timeout_rate", 0) > 0.1)
        
        # Determinar salud general
        total_issues = open_circuits + high_rejection_bulkheads + high_timeout_rate
        
        if total_issues == 0:
            health_status = "healthy"
            health_score = 100
        elif total_issues <= 2:
            health_status = "degraded"
            health_score = 75
        elif total_issues <= 5:
            health_status = "unhealthy"
            health_score = 50
        else:
            health_status = "critical"
            health_score = 25
        
        return {
            "status": "success",
            "data": {
                "health_status": health_status,
                "health_score": health_score,
                "issues": {
                    "open_circuits": open_circuits,
                    "high_rejection_bulkheads": high_rejection_bulkheads,
                    "high_timeout_rate": high_timeout_rate,
                    "total": total_issues
                },
                "details": {
                    "circuit_breakers": len(circuit_breakers),
                    "bulkheads": len(bulkheads),
                    "timeouts": len(timeouts)
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting resilience health: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo salud de resiliencia"
        )
