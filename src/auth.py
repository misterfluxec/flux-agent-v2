# =============================================================================
# FLUXAGENT V2 — MÓDULO DE AUTENTICACIÓN JWT
# =============================================================================
# Centraliza toda la lógica de seguridad:
#   - Hash de contraseñas con bcrypt
#   - Generación y validación de tokens JWT
#   - Dependencia FastAPI: get_usuario_actual / get_tenant_actual
#
# FLUJO:
#   1. Usuario llama POST /api/v1/auth/login con email+password
#   2. Backend verifica bcrypt, genera JWT con {sub, tenant_id, role, name}
#   3. Frontend guarda el token y lo envía en cada request como:
#      Authorization: Bearer <token>
#   4. Cada endpoint protegido usa Depends(get_tenant_actual) para
#      extraer el tenant_id real del token — NUNCA un dummy hardcodeado
# =============================================================================

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from uuid import UUID

import bcrypt as _bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, BeforeValidator, Field

from config import obtener_config

logger = logging.getLogger(__name__)
config = obtener_config()

# =============================================================================
# VALIDACIÓN DE CONTRASEÑA FUERTE (Pydantic v2)
# =============================================================================
# Uso en schemas de registro:
#   password: StrongPassword
# Valida: mín 8 chars, 1 mayúscula, 1 número, 1 carácter especial.

def _validate_strong_password(v: str) -> str:
    """Validador de fortaleza de contraseña para Pydantic v2."""
    if len(v) < 8:
        raise ValueError("Mínimo 8 caracteres")
    if not re.search(r"[A-Z]", v):
        raise ValueError("Requiere al menos una mayúscula")
    if not re.search(r"\d", v):
        raise ValueError("Requiere al menos un número")
    if not re.search(r'[!@#$%^&*()_+\-={}\[\]|;:\'",.<>?]', v):
        raise ValueError("Requiere al menos un carácter especial")
    return v

# Tipo anotado — úsalo como `password: StrongPassword` en cualquier BaseModel
StrongPassword = Annotated[str, BeforeValidator(_validate_strong_password)]

# =============================================================================
# HASH DE CONTRASEÑAS (bcrypt puro — sin passlib para evitar conflictos de versión)
# =============================================================================


def hash_password(password: str) -> str:
    """Genera un hash bcrypt seguro de la contraseña."""
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica que la contraseña en texto plano coincide con su hash bcrypt."""
    try:
        return _bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# =============================================================================
# JWT — PAYLOAD Y TOKENS
# =============================================================================

class PayloadToken(BaseModel):
    """Datos que viajan dentro del JWT."""
    sub:       str          # user_id (UUID como string)
    tenant_id: str          # tenant_id (UUID como string)
    role:       str          # super_admin | admin | agente | viewer
    name:    str          # Nombre del usuario para mostrar en la UI
    plan:      str = "starter"  # Plan del tenant
    exp:       Optional[int] = None


def crear_access_token(payload: PayloadToken) -> str:
    """
    Genera un JWT firmado con HS256.

    El token expira según jwt_expire_minutos en config (por defecto 60 min).
    Para renovación automática, el frontend debe llamar a /api/v1/auth/refresh.
    """
    datos = payload.model_dump(exclude_none=True)
    datos["exp"] = datetime.now(tz=timezone.utc) + timedelta(minutes=config.jwt_expire_minutos)

    return jwt.encode(datos, config.jwt_secret, algorithm=config.jwt_algoritmo)


def decodificar_token(token: str) -> PayloadToken:
    """
    Decodifica y valida un JWT.

    Raises:
        HTTPException 401 — si el token expiró o es inválido
    """
    try:
        datos = jwt.decode(token, config.jwt_secret, algorithms=[config.jwt_algoritmo])
        return PayloadToken(**datos)
    except JWTError as exc:
        logger.warning(f"Token inválido: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado. Inicia sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# =============================================================================
# DEPENDENCIAS FASTAPI
# =============================================================================

_bearer = HTTPBearer(auto_error=False)


async def get_usuario_actual(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> PayloadToken:
    """
    Dependencia que extrae y valida el token del header Authorization.

    Uso en endpoints protegidos:
        usuario: PayloadToken = Depends(get_usuario_actual)
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere autenticación. Incluye el header: Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decodificar_token(credentials.credentials)


async def get_tenant_actual(
    usuario: PayloadToken = Depends(get_usuario_actual),
) -> UUID:
    """
    Dependencia que retorna el tenant_id como UUID del usuario autenticado.

    Reemplaza COMPLETAMENTE el tenant_id dummy '11111111-1111-...' que
    se usaba en desarrollo. Ahora cada request lleva el tenant del usuario real.

    Uso en endpoints:
        tenant_id: UUID = Depends(get_tenant_actual)
    """
    try:
        return UUID(usuario.tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="tenant_id inválido en el token.",
        )


async def get_tenant_actual_opcional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> UUID:
    """
    Versión que devuelve el tenant demo si no hay token.
    Usar SOLO en endpoints públicos de prueba (playground, demo).
    """
    TENANT_DEMO = UUID("11111111-1111-1111-1111-111111111111")
    if not credentials:
        return TENANT_DEMO
    try:
        payload = decodificar_token(credentials.credentials)
        return UUID(payload.tenant_id)
    except Exception:
        return TENANT_DEMO


def solo_admin(usuario: PayloadToken = Depends(get_usuario_actual)) -> PayloadToken:
    """Dependencia que requiere role admin o superior."""
    if usuario.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere role de administrador para esta acción.",
        )
    return usuario


def solo_super_admin(usuario: PayloadToken = Depends(get_usuario_actual)) -> PayloadToken:
    """Dependencia que requiere role super_admin."""
    logger.info(f"Verificando role super_admin para usuario: {usuario.sub} | rol_actual: {usuario.role}")
    if usuario.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere acceso de super-administrador.",
        )
    return usuario
