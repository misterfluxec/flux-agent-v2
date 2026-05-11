from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel

from database import obtener_sesion, configurar_rls
from auth import get_tenant_actual_opcional, PayloadToken

router = APIRouter(prefix="/api/v1/catalog", tags=["Catálogo Comercial"])

class CatalogItemCreate(BaseModel):
    type: str
    name: str
    description: Optional[str] = None
    base_price: float
    currency: str = "USD"
    duration_minutes: Optional[int] = None
    stock_quantity: int = 0
    requires_booking: bool = False
    requires_payment: bool = True
    metadata: Optional[dict] = {}

class CatalogItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[float] = None
    stock_quantity: Optional[int] = None
    estado: Optional[str] = None

@router.get("")
async def listar_catalogo(
    current_tenant: PayloadToken = Depends(get_tenant_actual_opcional),
    db: AsyncSession = Depends(obtener_sesion)
):
    """Retorna la lista de ítems del catálogo del tenant autenticado."""
    if not current_tenant:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    await configurar_rls(db, UUID(current_tenant.tenant_id))
    
    result = await db.execute(text("""
        SELECT id, type, name, description, base_price, currency, stock_quantity, estado, metadata
        FROM catalog_items
        ORDER BY created_at DESC
    """))
    
    items = []
    for row in result.fetchall():
        items.append({
            "id": str(row.id),
            "type": row.type,
            "name": row.name,
            "description": row.description,
            "base_price": float(row.base_price) if row.base_price else 0,
            "currency": row.currency,
            "stock_quantity": row.stock_quantity,
            "estado": row.estado,
            "metadata": row.metadata
        })
        
    return items

@router.patch("/{item_id}")
async def actualizar_item(
    item_id: UUID,
    datos: CatalogItemUpdate,
    current_tenant: PayloadToken = Depends(get_tenant_actual_opcional),
    db: AsyncSession = Depends(obtener_sesion)
):
    """Actualiza propiedades de un ítem del catálogo."""
    if not current_tenant:
        raise HTTPException(status_code=401, detail="No autenticado")
        
    await configurar_rls(db, UUID(current_tenant.tenant_id))
    
    # Construir query dinámico
    updates = []
    params = {"id": str(item_id)}
    
    if datos.name is not None:
        updates.append("name = :name")
        params["name"] = datos.name
        
    if datos.description is not None:
        updates.append("description = :desc")
        params["desc"] = datos.description
        
    if datos.base_price is not None:
        updates.append("base_price = :price")
        params["price"] = datos.base_price
        
    if datos.stock_quantity is not None:
        updates.append("stock_quantity = :stock")
        params["stock"] = datos.stock_quantity
        
    if datos.estado is not None:
        updates.append("estado = :estado")
        params["estado"] = datos.estado
        
    if not updates:
        return {"mensaje": "No hay cambios"}
        
    updates.append("updated_at = NOW()")
    query = f"UPDATE catalog_items SET {', '.join(updates)} WHERE id = :id RETURNING id"
    
    result = await db.execute(text(query), params)
    if not result.scalar():
         raise HTTPException(status_code=404, detail="Item no encontrado")
         
    await db.commit()
    return {"mensaje": "Item actualizado"}

class BulkImportRequest(BaseModel):
    items: List[dict]
    update_existing: bool = True

@router.post("/import")
async def importar_catalogo_bulk(
    payload: BulkImportRequest,
    current_tenant: PayloadToken = Depends(get_tenant_actual_opcional),
    db: AsyncSession = Depends(obtener_sesion)
):
    """
    Importación masiva de ítems al catálogo. Ideal para sync de CSVs locales o integraciones custom.
    """
    if not current_tenant:
        raise HTTPException(status_code=401, detail="No autenticado")
        
    tenant_id_uuid = UUID(current_tenant.tenant_id)
    await configurar_rls(db, tenant_id_uuid)
    
    if not payload.items:
        return {"mensaje": "No hay ítems para importar", "procesados": 0}

    procesados = 0
    errores = 0
    
    async with db.begin():
        for item in payload.items:
            try:
                name = item.get("name")
                if not name:
                    errores += 1
                    continue
                    
                item_type = item.get("type", "physical_product")
                desc = item.get("description", "")
                price = float(item.get("base_price", item.get("precio", 0)))
                stock = int(item.get("stock_quantity", item.get("stock", 0)))
                
                query = text("""
                    INSERT INTO catalog_items (tenant_id, type, name, description, base_price, stock_quantity, updated_at)
                    VALUES (:tenant, :type, :name, :desc, :price, :stock, NOW())
                    ON CONFLICT (tenant_id, name) DO UPDATE SET
                        type = EXCLUDED.type,
                        description = EXCLUDED.description,
                        base_price = EXCLUDED.base_price,
                        stock_quantity = catalog_items.stock_quantity + EXCLUDED.stock_quantity,
                        updated_at = NOW()
                """)
                
                await db.execute(query, {
                    "tenant": str(tenant_id_uuid),
                    "type": item_type,
                    "name": name,
                    "desc": desc,
                    "price": price,
                    "stock": stock
                })
                procesados += 1
            except Exception as e:
                errores += 1
                print(f"Error importando item {item}: {e}")
                
    return {"mensaje": f"Importación completada", "procesados": procesados, "errores": errores}
