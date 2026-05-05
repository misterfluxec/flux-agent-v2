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
    precio: Optional[float] = None
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
        SELECT id, codigo, nombre, precio, stock, estado, descripcion
        FROM productos
        WHERE tenant_id = :tid
        ORDER BY creado_en DESC
    """), {"tid": str(tenant_id)})
    
    productos = []
    for row in result.fetchall():
        productos.append({
            "id": str(row.id),
            "codigo": row.codigo,
            "nombre": row.nombre,
            "precio": float(row.precio) if row.precio else 0,
            "stock": row.stock,
            "estado": row.estado,
            "descripcion": row.descripcion
        })
        
    return productos

@router.patch("/{producto_id}")
async def actualizar_producto(
    producto_id: UUID,
    datos: ProductUpdate,
    tenant_id: UUID = Depends(get_tenant_actual_opcional),
    db: AsyncSession = Depends(obtener_sesion)
):
    """Actualiza precio o stock de un producto."""
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
    
    if datos.precio is not None:
        updates.append("precio = :precio")
        params["precio"] = datos.precio
        
    if datos.stock is not None:
        updates.append("stock = :stock")
        params["stock"] = datos.stock
        
    if not updates:
        return {"mensaje": "No hay cambios"}
        
    updates.append("actualizado_en = NOW()")
    query = f"UPDATE productos SET {', '.join(updates)} WHERE id = :id AND tenant_id = :tid"
    
    await db.execute(text(query), params)
    await db.commit()
    
    return {"mensaje": "Producto actualizado"}
