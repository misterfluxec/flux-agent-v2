from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel

from database import obtener_sesion, configurar_rls
from auth import get_tenant_actual_opcional

router = APIRouter(prefix="/api/v1/products", tags=["Inventario"])

class ProductUpdate(BaseModel):
    price: Optional[float] = None
    stock: Optional[int] = None

@router.get("")
async def listar_productos(
    tenant_id: UUID = Depends(get_tenant_actual_opcional),
    db: AsyncSession = Depends(obtener_sesion)
):
    """Retorna la lista de productos del tenant autenticado."""
    if not tenant_id:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    await configurar_rls(db, tenant_id)
    
    result = await db.execute(text("""
        SELECT id, codigo, name, price, stock, status, description
        FROM productos
        WHERE tenant_id = :tid
        ORDER BY created_at DESC
    """), {"tid": str(tenant_id)})
    
    productos = []
    for row in result.fetchall():
        productos.append({
            "id": str(row.id),
            "codigo": row.codigo,
            "name": row.name,
            "price": float(row.price) if row.price else 0,
            "stock": row.stock,
            "status": row.status,
            "description": row.description
        })
        
    return productos

@router.patch("/{producto_id}")
async def actualizar_producto(
    producto_id: UUID,
    datos: ProductUpdate,
    tenant_id: UUID = Depends(get_tenant_actual_opcional),
    db: AsyncSession = Depends(obtener_sesion)
):
    """Actualiza price o stock de un producto."""
    if not tenant_id:
        raise HTTPException(status_code=401, detail="No autenticado")
        
    await configurar_rls(db, tenant_id)
    
    # Validar que exista
    check = await db.execute(text("SELECT id FROM productos WHERE id = :id AND tenant_id = :tid"), 
                           {"id": str(producto_id), "tid": str(tenant_id)})
    if not check.scalar():
        raise HTTPException(status_code=404, detail="Producto no encontrado")
        
    # Construir query dinámico
    updates = []
    params = {"id": str(producto_id), "tid": str(tenant_id)}
    
    if datos.price is not None:
        updates.append("price = :price")
        params["price"] = datos.price
        
    if datos.stock is not None:
        updates.append("stock = :stock")
        params["stock"] = datos.stock
        
    if not updates:
        return {"mensaje": "No hay cambios"}
        
    updates.append("updated_at = NOW()")
    query = f"UPDATE productos SET {', '.join(updates)} WHERE id = :id AND tenant_id = :tid"
    
    await db.execute(text(query), params)
    await db.commit()
    
    return {"mensaje": "Producto actualizado"}
