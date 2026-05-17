from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any, List
from uuid import UUID

from database import obtener_sesion, configurar_rls
from auth import get_tenant_actual

router = APIRouter(prefix="/api/v1/leads", tags=["CRM"])

@router.get("", summary="Obtiene la lista de leads/conversaciones")
async def get_leads(
    tenant_id: UUID = Depends(get_tenant_actual),
    db: AsyncSession = Depends(obtener_sesion)
) -> List[Dict[str, Any]]:
    await configurar_rls(db, tenant_id)
    
    # We fetch conversations representing leads.
    # In a real CRM, you'd have a separate `leads` table and join it.
    # Here, we group conversations by `lead_externo_id` to show unique leads,
    # or just show the latest conversation for each lead.
    
    query = """
        SELECT 
            c.id,
            c.lead_externo_id,
            c.canal,
            c.status,
            c.sentimiento,
            c.venta_cerrada,
            c.valor_venta,
            c.iniciada_en,
            c.cerrada_en
        FROM conversaciones c
        WHERE c.tenant_id = :tid
        ORDER BY c.iniciada_en DESC
        LIMIT 100
    """
    
    result = await db.execute(text(query), {"tid": str(tenant_id)})
    filas = result.fetchall()
    
    leads = []
    for row in filas:
        # Extraer teléfono si es de WhatsApp (formato wa-593991234567)
        phone = ""
        name = "Cliente Anónimo"
        email = ""
        
        if row.lead_externo_id:
            if row.lead_externo_id.startswith("wa-"):
                phone = "+" + row.lead_externo_id.replace("wa-", "")
                name = f"Usuario WA ({phone[-4:]})"
            elif "@" in row.lead_externo_id:
                email = row.lead_externo_id
                name = email.split("@")[0]
            else:
                name = row.lead_externo_id
        
        # Mapeo de status para el frontend CRM
        estado_crm = "nuevo"
        if row.venta_cerrada:
            estado_crm = "cerrado"
        elif row.status == "cerrada":
            estado_crm = "perdido" if not row.venta_cerrada else "cerrado"
        elif row.status == "activa":
            estado_crm = "contactado"
            
        leads.append({
            "id": str(row.id),
            "name": name,
            "phone": phone,
            "email": email,
            "canal": row.canal.replace("_chat", ""), # web_chat -> web
            "status": estado_crm,
            "monto": float(row.valor_venta) if row.valor_venta else 0.0,
            "fecha": row.iniciada_en.strftime("%Y-%m-%d %H:%M") if row.iniciada_en else "",
            "sentimiento": float(row.sentimiento) if row.sentimiento else 0.0
        })
        
    return leads
