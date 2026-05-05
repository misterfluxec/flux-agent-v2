from fastapi import APIRouter, Depends, HTTPException, status
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func
from typing import List, Dict, Any, Optional
import psutil
from uuid import UUID
import logging

from database import obtener_sesion
from auth import solo_super_admin, PayloadToken
from config import obtener_config

logger = logging.getLogger("admin_router")
router = APIRouter(prefix="/api/v1/admin", tags=["SuperAdmin"], dependencies=[Depends(solo_super_admin)])
config = obtener_config()

# -------------------------------------------------------------------------
# INFRAESTRUCTURA & MÉTRICAS
# -------------------------------------------------------------------------

@router.get("/sysinfo")
async def sysinfo():
    """Retorna métricas de hardware y salud del sistema."""
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        # Verificar salud de Ollama
        ollama_health = "error"
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{config.ollama_base_url}/api/tags")
                if resp.status_code == 200:
                    ollama_health = "operativo"
        except:
            ollama_health = "desconectado"

    except Exception as e:
        logger.error(f"Error obteniendo sysinfo: {e}")
        cpu = 0
        ram = type('obj', (object,), {'percent': 0, 'total': 0, 'used': 0})
        disk = type('obj', (object,), {'percent': 0, 'total': 0, 'used': 0})
        ollama_health = "error"

    return {
        "cpu_percent": cpu,
        "ram_percent": ram.percent,
        "ram_total_gb": round(ram.total / (1024**3), 1),
        "ram_used_gb": round(ram.used / (1024**3), 1),
        "disk_percent": disk.percent,
        "disk_total_gb": round(disk.total / (1024**3), 1),
        "disk_used_gb": round(disk.used / (1024**3), 1),
        "ollama_status": ollama_health,
        "active_brain": config.ollama_modelo_chat,
        "db_status": "conectado"
    }

# -------------------------------------------------------------------------
# CONTROL DE MODELOS IA (OLLAMA)
# -------------------------------------------------------------------------

@router.get("/models")
async def list_models():
    """Lista los modelos disponibles en el motor Ollama local."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{config.ollama_base_url}/api/tags")
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail="Error contactando a Ollama")
            
            data = resp.json()
            models = data.get("models", [])
            
            return [
                {
                    "name": m["name"],
                    "size_gb": round(m["size"] / (1024**3), 2),
                    "modified": m["modified_at"],
                    "active": m["name"] == config.ollama_modelo_chat
                }
                for m in models
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama offline: {str(e)}")

@router.post("/models/pull")
async def pull_model(model_name: str):
    """Ordena a Ollama descargar un nuevo modelo."""
    try:
        # Esto es asíncrono en Ollama, pero el backend solo envía la orden
        async with httpx.AsyncClient(timeout=None) as client:
            # Usamos streaming falso para capturar solo el inicio
            resp = await client.post(f"{config.ollama_base_url}/api/pull", json={"name": model_name, "stream": False})
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------------------
# GESTIÓN DE TENANTS & PLANES
# -------------------------------------------------------------------------

@router.get("/tenants")
async def list_tenants(db: AsyncSession = Depends(obtener_sesion)):
    """Lista detallada de tenants con métricas de consumo y planes."""
    query = """
        SELECT id, nombre, plan, estado, 
               max_mensajes_mes, mensajes_usados_mes,
               contrato_inicio, contrato_fin
        FROM tenants
        ORDER BY creado_en DESC
    """
    result = await db.execute(text(query))
    rows = result.fetchall()
    
    return [
        {
            "id": str(r.id),
            "nombre": r.nombre,
            "plan": r.plan,
            "estado": r.estado,
            "usage": {
                "used": r.mensajes_usados_mes,
                "limit": r.max_mensajes_mes,
                "percent": round((r.mensajes_usados_mes / r.max_mensajes_mes * 100), 1) if r.max_mensajes_mes > 0 else 0
            },
            "contrato": {
                "inicio": r.contrato_inicio.isoformat() if r.contrato_inicio else None,
                "fin": r.contrato_fin.isoformat() if r.contrato_fin else "Vitalicio"
            }
        }
        for r in rows
    ]

@router.patch("/tenants/{tenant_id}/plan")
async def update_tenant_plan(tenant_id: UUID, payload: Dict[str, Any], db: AsyncSession = Depends(obtener_sesion)):
    """Cambia el plan y los límites de un tenant."""
    nuevo_plan = payload.get("plan")
    nuevos_limites = payload.get("max_mensajes")
    
    if nuevo_plan not in ["starter", "pro", "enterprise"]:
        raise HTTPException(status_code=400, detail="Plan inválido")

    query = text("""
        UPDATE tenants 
        SET plan = :plan, max_mensajes_mes = :max 
        WHERE id = :id 
        RETURNING id
    """)
    result = await db.execute(query, {"plan": nuevo_plan, "max": nuevos_limites, "id": str(tenant_id)})
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    
    await db.commit()
    return {"message": f"Tenant actualizado a plan {nuevo_plan}"}

# -------------------------------------------------------------------------
# VISIBILIDAD GLOBAL DE AGENTES
# -------------------------------------------------------------------------

@router.get("/agents")
async def list_all_agents(db: AsyncSession = Depends(obtener_sesion)):
    """Vista de ingeniería de todos los agentes desplegados en la plataforma."""
    query = """
        SELECT a.id, a.nombre, a.tipo, a.estado, t.nombre as tenant_nombre
        FROM agents a
        JOIN tenants t ON a.tenant_id = t.id
        ORDER BY a.creado_en DESC
    """
    result = await db.execute(text(query))
    rows = result.fetchall()
    return [
        {
            "id": str(r.id),
            "nombre": r.nombre,
            "tipo": r.tipo,
            "estado": r.estado,
            "tenant": r.tenant_nombre
        }
        for r in rows
    ]

# -------------------------------------------------------------------------
# SOPORTE Y TICKET SYSTEM
# -------------------------------------------------------------------------

@router.get("/tickets")
async def get_tickets(db: AsyncSession = Depends(obtener_sesion)):
    query = """
        SELECT t.id, t.asunto, t.estado, t.prioridad, ten.nombre as tenant_nombre, t.creado_en
        FROM tickets t
        LEFT JOIN tenants ten ON t.tenant_id = ten.id
        ORDER BY t.creado_en DESC
    """
    result = await db.execute(text(query))
    rows = result.fetchall()
    return [
        {
            "id": str(r.id),
            "tenant": r.tenant_nombre or "Global",
            "asunto": r.asunto,
            "estado": r.estado,
            "prioridad": r.prioridad,
            "fecha": r.creado_en.isoformat()
        }
        for r in rows
    ]
