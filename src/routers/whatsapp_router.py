import os
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_tenant_actual
from database import configurar_rls, obtener_sesion
from config import obtener_config

router = APIRouter(
    prefix="/api/v1/whatsapp",
    tags=["WhatsApp & Canales"],
)

config = obtener_config()

# URL de Evolution API (por defecto)
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8081")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "admin_flux_2025")

# Modelos Pydantic
class WhatsAppConnectRequest(BaseModel):
    instancia_nombre: str
    numero_telefono: Optional[str] = None
    agent_id: Optional[UUID] = None  # Si es null, usará el agente por defecto

class WhatsAppStatusResponse(BaseModel):
    instancia_nombre: str
    estado: str
    numero_telefono: Optional[str] = None
    qr_code: Optional[str] = None
    conectado: bool

class WhatsAppInstanceInfo(BaseModel):
    id: UUID
    instancia_nombre: str
    canal: str
    estado: str
    webhook_url: Optional[str] = None
    agent_id: Optional[UUID] = None

@router.post("/connect", response_model=WhatsAppStatusResponse)
async def connect_whatsapp(
    request: WhatsAppConnectRequest,
    tenant_id: UUID = Depends(get_tenant_actual),
    db: AsyncSession = Depends(obtener_sesion)
):
    """
    Crea una instancia de WhatsApp en Evolution API y genera el código QR.
    Registra la instancia en canales_config.
    """
    await configurar_rls(db, tenant_id)
    
    # 1. Validar Evolution API
    if not EVOLUTION_API_KEY:
        raise HTTPException(status_code=500, detail="Evolution API Key no configurada en el servidor.")

    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }

    # 2. Obtener URL de Webhooks del backend
    # En producción deberíamos usar config.backend_url, en local la URL base
    base_url = config.backend_url if hasattr(config, "backend_url") else os.getenv("BASE_URL", "http://localhost:8001")
    webhook_url = f"{base_url}/api/v1/webhooks/whatsapp"

    # Construir token de webhook
    webhook_token = f"tenant-{tenant_id}"

    evolution_payload = {
        "instanceName": request.instancia_nombre,
        "qrcode": True,
        "number": request.numero_telefono,
        "webhook": webhook_url,
        "token": webhook_token
    }

    try:
        # Llamar a Evolution API
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{EVOLUTION_API_URL}/instance/create",
                headers=headers,
                json=evolution_payload
            )
            
            if resp.status_code != 200 and resp.status_code != 201:
                raise HTTPException(status_code=resp.status_code, detail=f"Evolution API Error: {resp.text}")
            
            evolution_data = resp.json()

            # Guardar en base de datos
            token_instancia = evolution_data.get("hash", {}).get("apikey", "")
            if not token_instancia:
                # evolution_data puede devolver un formato distinto dependiendo de la versión
                token_instancia = evolution_data.get("instance", {}).get("token", "")

            # Insert o Update en canales_config
            await db.execute(text("""
                INSERT INTO canales_config (tenant_id, agent_id, canal, instancia_nombre, token_acceso, webhook_url, estado)
                VALUES (:tenant_id, :agent_id, 'whatsapp', :instancia_nombre, :token_acceso, :webhook_url, 'inactivo')
                ON CONFLICT (tenant_id, canal, instancia_nombre) 
                DO UPDATE SET token_acceso = EXCLUDED.token_acceso, webhook_url = EXCLUDED.webhook_url, agent_id = EXCLUDED.agent_id
            """), {
                "tenant_id": str(tenant_id),
                "agent_id": str(request.agent_id) if request.agent_id else None,
                "instancia_nombre": request.instancia_nombre,
                "token_acceso": token_instancia,
                "webhook_url": webhook_url
            })
            
            return WhatsAppStatusResponse(
                instancia_nombre=request.instancia_nombre,
                estado="generando_qr",
                qr_code=evolution_data.get("qrcode", {}).get("base64", evolution_data.get("qrcode")),
                numero_telefono=request.numero_telefono,
                conectado=False
            )
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Error conectando con Evolution API: {str(e)}")


@router.get("/status/{instancia_nombre}", response_model=WhatsAppStatusResponse)
async def get_whatsapp_status(
    instancia_nombre: str,
    tenant_id: UUID = Depends(get_tenant_actual),
    db: AsyncSession = Depends(obtener_sesion)
):
    """
    Obtiene el estado de conexión actual de la instancia.
    """
    await configurar_rls(db, tenant_id)
    
    # 1. Verificar existencia en la DB
    result = await db.execute(text("""
        SELECT id FROM canales_config 
        WHERE tenant_id = :tenant_id AND canal = 'whatsapp' AND instancia_nombre = :instancia_nombre
    """), {"tenant_id": str(tenant_id), "instancia_nombre": instancia_nombre})
    
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Instancia no encontrada para este tenant")

    headers = {"apikey": EVOLUTION_API_KEY}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{EVOLUTION_API_URL}/instance/connectionState/{instancia_nombre}",
                headers=headers
            )
            
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=f"Evolution API Error: {resp.text}")
            
            status_data = resp.json()
            estado_conexion = status_data.get("instance", {}).get("state", "unknown")
            conectado = estado_conexion == "open"

            # Actualizar estado en la DB
            nuevo_estado = "activo" if conectado else "desconectado"
            await db.execute(text("""
                UPDATE canales_config 
                SET estado = :nuevo_estado 
                WHERE tenant_id = :tenant_id AND canal = 'whatsapp' AND instancia_nombre = :instancia_nombre
            """), {"nuevo_estado": nuevo_estado, "tenant_id": str(tenant_id), "instancia_nombre": instancia_nombre})
            
            return WhatsAppStatusResponse(
                instancia_nombre=instancia_nombre,
                estado=estado_conexion,
                numero_telefono=status_data.get("instance", {}).get("owner", None),
                conectado=conectado
            )
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Error conectando con Evolution API: {str(e)}")


@router.delete("/disconnect/{instancia_nombre}")
async def disconnect_whatsapp(
    instancia_nombre: str,
    tenant_id: UUID = Depends(get_tenant_actual),
    db: AsyncSession = Depends(obtener_sesion)
):
    """
    Desconecta y elimina una instancia de WhatsApp.
    """
    await configurar_rls(db, tenant_id)
    
    # 1. Verificar existencia
    result = await db.execute(text("""
        SELECT id FROM canales_config 
        WHERE tenant_id = :tenant_id AND canal = 'whatsapp' AND instancia_nombre = :instancia_nombre
    """), {"tenant_id": str(tenant_id), "instancia_nombre": instancia_nombre})
    
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Instancia no encontrada")

    headers = {"apikey": EVOLUTION_API_KEY}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.delete(
                f"{EVOLUTION_API_URL}/instance/logout/{instancia_nombre}",
                headers=headers
            )
            
            # Borramos la instancia también (o en su defecto log out)
            await client.delete(
                f"{EVOLUTION_API_URL}/instance/delete/{instancia_nombre}",
                headers=headers
            )
            
            # 2. Borrar de la base de datos
            await db.execute(text("""
                DELETE FROM canales_config 
                WHERE tenant_id = :tenant_id AND canal = 'whatsapp' AND instancia_nombre = :instancia_nombre
            """), {"tenant_id": str(tenant_id), "instancia_nombre": instancia_nombre})
            
            return {"status": "success", "message": "Instancia desconectada y eliminada correctamente"}
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Error conectando con Evolution API: {str(e)}")


@router.get("/instances", response_model=List[WhatsAppInstanceInfo])
async def list_whatsapp_instances(
    tenant_id: UUID = Depends(get_tenant_actual),
    db: AsyncSession = Depends(obtener_sesion)
):
    """
    Lista las instancias configuradas por el tenant.
    """
    await configurar_rls(db, tenant_id)
    
    result = await db.execute(text("""
        SELECT id, instancia_nombre, canal, estado, webhook_url, agent_id
        FROM canales_config 
        WHERE tenant_id = :tenant_id AND canal = 'whatsapp'
    """), {"tenant_id": str(tenant_id)})
    
    instancias = []
    for row in result.fetchall():
        instancias.append(WhatsAppInstanceInfo(
            id=row.id,
            instancia_nombre=row.instancia_nombre,
            canal=row.canal,
            estado=row.estado,
            webhook_url=row.webhook_url,
            agent_id=row.agent_id
        ))
    
    return instancias
