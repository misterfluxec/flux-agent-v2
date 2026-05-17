# =============================================================================
# FLUXAGENT V2 — ROUTER DE GESTIÓN DE USUARIOS DEL TENANT
# =============================================================================
# Endpoints para gestionar el equipo de un tenant (invitar, editar, eliminar)
# Solo accesible para users con role 'admin'
# =============================================================================

import logging
from uuid import UUID, uuid4
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auth import (
    PayloadToken,
    get_usuario_actual,
    get_tenant_actual,
    hash_password,
    solo_admin,
)
from database import obtener_sesion, configurar_rls

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["Usuarios del Tenant"])


# =============================================================================
# SCHEMAS
# =============================================================================

class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str
    role: str  # admin, viewer, agente
    password: Optional[str] = None  # Si no se envía, se genera una invitación


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None  # is_active, inactivo, suspendido


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    status: str
    last_login: Optional[str] = None
    created_at: str


# =============================================================================
# GET /api/v1/users — Lista users del tenant
# =============================================================================

@router.get("", summary="Lista todos los users del tenant")
async def list_users(
    usuario: PayloadToken = Depends(solo_admin),
    db: AsyncSession = Depends(obtener_sesion),
) -> list[UserResponse]:
    """
    Retorna la lista de users del tenant actual.
    Solo admins pueden ver esta información.
    """
    await configurar_rls(db, UUID(usuario.tenant_id))
    
    result = await db.execute(
        text("""
            SELECT id, email, name, role, status, last_login, created_at
            FROM users
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
        """),
        {"tenant_id": usuario.tenant_id}
    )
    
    users = []
    for row in result.fetchall():
        users.append(UserResponse(
            id=str(row.id),
            email=row.email,
            name=row.name or "",
            role=row.role,
            status=row.status,
            last_login=str(row.last_login) if row.last_login else None,
            created_at=str(row.created_at),
        ))
    
    return users


# =============================================================================
# POST /api/v1/users — Crear nuevo usuario
# =============================================================================

@router.post("", summary="Crea un nuevo usuario en el tenant", status_code=status.HTTP_201_CREATED)
async def create_user(
    datos: CreateUserRequest,
    usuario: PayloadToken = Depends(solo_admin),
    db: AsyncSession = Depends(obtener_sesion),
):
    """
    Crea un nuevo usuario dentro del tenant.
    El role debe ser: admin, viewer, o agente.
    Si no se proporciona contraseña, se genera una invitación.
    """
    await configurar_rls(db, UUID(usuario.tenant_id))
    
    # Verificar que el email no exista en el tenant
    result_check = await db.execute(
        text("SELECT id FROM users WHERE tenant_id = :tid AND email = :email"),
        {"tid": usuario.tenant_id, "email": datos.email.lower()}
    )
    if result_check.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está en uso dentro de este tenant."
        )
    
    # Verificar límite de users según el plan
    result_plan = await db.execute(
        text("SELECT plan, max_usuarios FROM tenants WHERE id = :tid"),
        {"tid": usuario.tenant_id}
    )
    plan_row = result_plan.fetchone()
    if not plan_row:
        raise HTTPException(status_code=500, detail="Tenant no encontrado")
    
    # Contar users actuales
    result_count = await db.execute(
        text("SELECT COUNT(*) FROM users WHERE tenant_id = :tid"),
        {"tid": usuario.tenant_id}
    )
    current_count = result_count.scalar() or 0
    
    # Por ahora usamos un límite hardcoded. En producción, leer de la config del plan
    max_usuarios = {"starter": 3, "pro": 10, "enterprise": 100}.get(plan_row.plan, 3)
    
    if current_count >= max_usuarios:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Has alcanzado el límite de users ({max_usuarios}) de tu plan. Haz upgrade para más users."
        )
    
    # Crear usuario
    nuevo_usuario_id = uuid4()
    password_hash = hash_password(datos.password) if datos.password else hash_password(f"Temp{uuid4().hex[:8]}")
    
    await db.execute(
        text("""
            INSERT INTO users (id, tenant_id, email, password_hash, name, role, status)
            VALUES (:id, :tid, :email, :pwd, :name, :role, 'is_active')
        """),
        {
            "id": str(nuevo_usuario_id),
            "tid": usuario.tenant_id,
            "email": datos.email.lower(),
            "pwd": password_hash,
            "name": datos.name.strip(),
            "role": datos.role if datos.role in ("admin", "viewer", "agente") else "viewer",
        }
    )
    await db.commit()
    
    logger.info(f"Usuario creado: {datos.email} | tenant={usuario.tenant_id} | role={datos.role}")
    
    return {
        "mensaje": "Usuario creado correctamente",
        "usuario": {
            "id": str(nuevo_usuario_id),
            "email": datos.email.lower(),
            "name": datos.name.strip(),
            "role": datos.role,
        }
    }


# =============================================================================
# GET /api/v1/users/{user_id} — Obtener usuario específico
# =============================================================================

@router.get("/{user_id}", summary="Obtiene un usuario específico")
async def get_user(
    user_id: UUID,
    usuario: PayloadToken = Depends(solo_admin),
    db: AsyncSession = Depends(obtener_sesion),
) -> UserResponse:
    await configurar_rls(db, UUID(usuario.tenant_id))
    
    result = await db.execute(
        text("""
            SELECT id, email, name, role, status, last_login, created_at
            FROM users
            WHERE id = :uid AND tenant_id = :tid
        """),
        {"uid": str(user_id), "tid": usuario.tenant_id}
    )
    
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return UserResponse(
        id=str(row.id),
        email=row.email,
        name=row.name or "",
        role=row.role,
        status=row.status,
        last_login=str(row.last_login) if row.last_login else None,
        created_at=str(row.created_at),
    )


# =============================================================================
# PATCH /api/v1/users/{user_id} — Actualizar usuario
# =============================================================================

@router.patch("/{user_id}", summary="Actualiza un usuario del tenant")
async def update_user(
    user_id: UUID,
    datos: UpdateUserRequest,
    usuario: PayloadToken = Depends(solo_admin),
    db: AsyncSession = Depends(obtener_sesion),
):
    """
    Actualiza name, role o status de un usuario.
    No se puede actualizar a uno mismo.
    """
    await configurar_rls(db, UUID(usuario.tenant_id))
    
    # Verificar que el usuario pertenezca al tenant
    result_check = await db.execute(
        text("SELECT role FROM users WHERE id = :uid AND tenant_id = :tid"),
        {"uid": str(user_id), "tid": usuario.tenant_id}
    )
    target_user = result_check.fetchone()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # No permitir que un admin se degrade a sí mismo
    if str(user_id) == usuario.sub and datos.role and datos.role != "admin":
        raise HTTPException(
            status_code=400,
            detail="No puedes degradar tu propio role de administrador."
        )
    
    # Construir query dinámico
    updates = []
    params = {"uid": str(user_id), "tid": usuario.tenant_id}
    
    if datos.name is not None:
        updates.append("name = :name")
        params["name"] = datos.name.strip()
    
    if datos.role is not None and datos.role in ("admin", "viewer", "agente"):
        updates.append("role = :role")
        params["role"] = datos.role
    
    if datos.status is not None and datos.status in ("is_active", "inactivo", "suspendido"):
        updates.append("status = :status")
        params["status"] = datos.status
    
    if not updates:
        return {"mensaje": "No hay cambios para aplicar"}
    
    query = f"UPDATE users SET {', '.join(updates)} WHERE id = :uid AND tenant_id = :tid"
    await db.execute(text(query), params)
    await db.commit()
    
    logger.info(f"Usuario actualizado: {user_id} | tenant={usuario.tenant_id}")
    
    return {"mensaje": "Usuario actualizado correctamente"}


# =============================================================================
# DELETE /api/v1/users/{user_id} — Eliminar usuario
# =============================================================================

@router.delete("/{user_id}", summary="Elimina un usuario del tenant")
async def delete_user(
    user_id: UUID,
    usuario: PayloadToken = Depends(solo_admin),
    db: AsyncSession = Depends(obtener_sesion),
):
    """
    Elimina un usuario del tenant.
    No se puede eliminar a uno mismo.
    """
    await configurar_rls(db, UUID(usuario.tenant_id))
    
    # No permitirse eliminarse a sí mismo
    if str(user_id) == usuario.sub:
        raise HTTPException(
            status_code=400,
            detail="No puedes eliminar tu propia cuenta."
        )
    
    # Verificar que el usuario pertenezca al tenant
    result_check = await db.execute(
        text("SELECT name FROM users WHERE id = :uid AND tenant_id = :tid"),
        {"uid": str(user_id), "tid": usuario.tenant_id}
    )
    if not result_check.fetchone():
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar que no sea el último admin
    result_admin_count = await db.execute(
        text("""
            SELECT COUNT(*) FROM users 
            WHERE tenant_id = :tid AND role = 'admin' AND status = 'is_active'
        """),
        {"tid": usuario.tenant_id}
    )
    admin_count = result_admin_count.scalar() or 0
    
    if admin_count <= 1:
        # Si el usuario a eliminar es admin y es el único, verificar
        result_target_rol = await db.execute(
            text("SELECT role FROM users WHERE id = :uid"),
            {"uid": str(user_id)}
        )
        target_rol = result_target_rol.fetchone()
        if target_rol and target_rol.role == "admin":
            raise HTTPException(
                status_code=400,
                detail="No puedes eliminar el último administrador del tenant."
            )
    
    await db.execute(
        text("DELETE FROM users WHERE id = :uid AND tenant_id = :tid"),
        {"uid": str(user_id), "tid": usuario.tenant_id}
    )
    await db.commit()
    
    logger.info(f"Usuario eliminado: {user_id} | tenant={usuario.tenant_id}")
    
    return {"mensaje": "Usuario eliminado correctamente"}


# =============================================================================
# POST /api/v1/users/{user_id}/reset-password — Resetear contraseña
# =============================================================================

@router.post("/{user_id}/reset-password", summary="Resetea la contraseña de un usuario")
async def reset_password(
    user_id: UUID,
    usuario: PayloadToken = Depends(solo_admin),
    db: AsyncSession = Depends(obtener_sesion),
):
    """
    Genera una nueva contraseña temporal para el usuario.
    """
    await configurar_rls(db, UUID(usuario.tenant_id))
    
    # Verificar que el usuario pertenezca al tenant
    result_check = await db.execute(
        text("SELECT email FROM users WHERE id = :uid AND tenant_id = :tid"),
        {"uid": str(user_id), "tid": usuario.tenant_id}
    )
    if not result_check.fetchone():
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Generar contraseña temporal
    temp_password = f"Temp{uuid4().hex[:8]}"
    password_hash = hash_password(temp_password)
    
    await db.execute(
        text("UPDATE users SET password_hash = :pwd WHERE id = :uid AND tenant_id = :tid"),
        {"pwd": password_hash, "uid": str(user_id), "tid": usuario.tenant_id}
    )
    await db.commit()
    
    logger.info(f"Password reseteado para usuario: {user_id} | tenant={usuario.tenant_id}")
    
    return {
        "mensaje": "Contraseña reseteada correctamente",
        "password_temporal": temp_password,
        "nota": "Comparte esta contraseña con el usuario. Deberá cambiarla en su próximo inicio de sesión."
    }