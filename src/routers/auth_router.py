# =============================================================================
# FLUXAGENT V2 — ROUTER DE AUTENTICACIÓN
# =============================================================================
# Endpoints públicos (no requieren token):
#   POST /api/v1/auth/register  — Crear tenant + usuario admin
#   POST /api/v1/auth/login     — Autenticar y obtener JWT
#   POST /api/v1/auth/refresh   — Renovar token válido
#
# Endpoints protegidos (requieren token):
#   GET  /api/v1/auth/me        — Perfil del usuario actual
# =============================================================================

import logging
from uuid import UUID, uuid4
from typing import Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auth import (
    PayloadToken,
    crear_access_token,
    get_usuario_actual,
    hash_password,
    verify_password,
)
from database import configurar_rls, obtener_sesion
from core.encryption import EncryptionService
from services.social_auth import UnifiedSocialAuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])


# =============================================================================
# SCHEMAS DE REQUEST / RESPONSE
# =============================================================================

class RegisterRequest(BaseModel):
    """Datos para crear un nuevo tenant con usuario admin."""
    nombre_empresa: Optional[str] = None
    nombre_usuario: str
    email:          str
    password:       str
    plan:           str = "starter"
    branding:       Optional[dict] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")
        return v
    
    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class LoginRequest(BaseModel):
    email:    str
    password: str


class TokenResponse(BaseModel):
    """Respuesta exitosa de login/register."""
    access_token: str
    token_type:   str = "bearer"
    usuario: dict
    is_new_user: Optional[bool] = False

class SocialLoginRequest(BaseModel):
    code: str
    provider: str


# =============================================================================
# POST /register
# =============================================================================

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registra un nuevo cliente (tenant) con usuario admin",
)
async def register(
    datos:  RegisterRequest,
    db:     AsyncSession = Depends(obtener_sesion),
):
    """
    Crea:
    1. Un nuevo tenant (empresa/cliente)
    2. Un usuario con rol 'admin' vinculado a ese tenant
    3. Retorna un JWT listo para usar

    Los límites del plan (starter/pro/enterprise) se aplican automáticamente.
    
    Si es plan enterprise, opcionalmente guarda branding (color, logo, etc.)
    """
    email_normalizado = datos.email.lower().strip()
    
    # Verificar email único
    result = await db.execute(
        text("SELECT id FROM usuarios WHERE email = :email"),
        {"email": email_normalizado},
    )
    if result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado. Intenta iniciar sesión.",
        )

    # Límites por plan
    PLAN_LIMITES = {
        "starter":    {"max_agentes": 1,  "max_mensajes_mes": 500,  "max_instancias_whatsapp": 1},
        "pro":        {"max_agentes": 5,  "max_mensajes_mes": 5000, "max_instancias_whatsapp": 3},
        "enterprise": {"max_agentes": 20, "max_mensajes_mes": 50000,"max_instancias_whatsapp": 10},
    }
    limites = PLAN_LIMITES.get(datos.plan, PLAN_LIMITES["starter"])

    # Si es empresa y tiene nombre de empresa, usarla. 
    # Si es individual y tiene nombre de empresa, usarlo como nombre de tienda.
    # Si no hay nombre de empresa, usar el nombre del usuario + " Store"
    nombre_usuario_str = (datos.nombre_usuario or "").strip()
    nombre_empresa_final = (datos.nombre_empresa or "").strip() if datos.nombre_empresa else f"{nombre_usuario_str} Store"

    tenant_id  = uuid4()
    usuario_id = uuid4()

    # Preparar branding JSON si existe
    branding_json = None
    if datos.branding:
        import json
        branding_json = json.dumps(datos.branding)

    # Crear tenant
    await db.execute(
        text("""
            INSERT INTO tenants (id, nombre_empresa, email_contacto, plan,
                                 max_agentes, max_mensajes_mes, max_instancias_whatsapp,
                                 color_primario, branding_config)
            VALUES (:id, :empresa, :email, :plan,
                    :max_agentes, :max_mensajes, :max_whatsapp,
                    :color, :branding)
        """),
        {
            "id":          str(tenant_id),
            "empresa":     nombre_empresa_final,
            "email":       email_normalizado,
            "plan":        datos.plan,
            "max_agentes": limites["max_agentes"],
            "max_mensajes": limites["max_mensajes_mes"],
            "max_whatsapp": limites["max_instancias_whatsapp"],
            "color":       datos.branding.get("color_primario") if datos.branding else "#6366f1",
            "branding":    branding_json,
        },
    )
    # Removing early commit to keep transaction atomic
    # Crear usuario usando fn_crear_usuario (SECURITY DEFINER, bypassa RLS)
    password_hash = hash_password(datos.password)
    await db.execute(
        text("""
            SELECT fn_crear_usuario(
                CAST(:uid AS UUID), CAST(:tid AS UUID), :email, :phash, :nombre, 'admin'
            )
        """),
        {
            "uid":    str(usuario_id),
            "tid":    str(tenant_id),
            "email":  (datos.email or "").lower().strip(),
            "phash":  password_hash,
            "nombre": nombre_usuario_str,
        },
    )
    
    # Auto-crear agente inicial "Yanua" por defecto para el Wizard RAG
    agent_id = uuid4()
    await db.execute(
        text("""
            INSERT INTO agents (
                id, tenant_id, nombre, area, estado,
                modelo, temperatura, max_tokens, canales
            )
            VALUES (
                :id, :tenant_id, 'Yanua', 'Asistente Principal', 'activo',
                'nomic-embed-text', 0.7, 512, ARRAY['web_chat']::text[]
            )
        """),
        {
            "id": str(agent_id),
            "tenant_id": str(tenant_id)
        }
    )
    
    await db.commit()

    # Generar token JWT
    token_payload = PayloadToken(
        sub=str(usuario_id),
        tenant_id=str(tenant_id),
        rol="admin",
        nombre=nombre_usuario_str,
        plan=datos.plan,
    )
    token = crear_access_token(token_payload)

    logger.info(f"Nuevo tenant registrado: {nombre_empresa_final} | plan={datos.plan}")
    return TokenResponse(
        access_token=token,
        usuario={
            "id":          str(usuario_id),
            "nombre":      nombre_usuario_str,
            "email":       email_normalizado,
            "rol":         "admin",
            "plan":        datos.plan,
            "tenant_id":   str(tenant_id),
            "nombre_empresa": nombre_empresa_final,
        },
    )


# =============================================================================
# POST /login
# =============================================================================

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autentica un usuario y retorna un JWT",
)
async def login(
    credenciales: LoginRequest,
    db:           AsyncSession = Depends(obtener_sesion),
):
    """
    Verifica email + contraseña con bcrypt.
    Si son correctas, retorna un JWT que incluye tenant_id, rol y nombre.

    El frontend debe guardar este token (localStorage o cookie httpOnly)
    y enviarlo en cada request como: Authorization: Bearer <token>
    """
    email = credenciales.email.lower().strip()

    # Buscar usuario usando fn_login_usuario (SECURITY DEFINER, bypassa RLS)
    result = await db.execute(
        text("SELECT id, tenant_id, password_hash, nombre, rol, plan, nombre_empresa, estado_tenant FROM fn_login_usuario(:email)"),
        {"email": email},
    )
    fila = result.fetchone()

    if not fila:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos.",
        )

    user_id, tenant_id, pwd_hash, nombre, rol, plan, empresa, tenant_estado = fila

    # Verificar tenant activo
    if tenant_estado != "activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta está suspendida. Contacta al soporte.",
        )

    # Verificar contraseña
    if not verify_password(credenciales.password, pwd_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos.",
        )

    # Actualizar último login (usando fn o SET RLS context)
    await configurar_rls(db, tenant_id)
    await db.execute(
        text("UPDATE usuarios SET ultimo_login = NOW() WHERE id = :id"),
        {"id": str(user_id)},
    )
    await db.commit()

    # Generar JWT
    token_payload = PayloadToken(
        sub=str(user_id),
        tenant_id=str(tenant_id),
        rol=rol,
        nombre=nombre,
        plan=plan,
    )
    token = crear_access_token(token_payload)

    logger.info(f"Login exitoso: {email} | tenant={tenant_id} | rol={rol}")
    return TokenResponse(
        access_token=token,
        usuario={
            "id":             str(user_id),
            "nombre":         nombre,
            "email":          email,
            "rol":            rol,
            "plan":           plan,
            "tenant_id":      str(tenant_id),
            "nombre_empresa": empresa,
        },
    )


# =============================================================================
# GET /me
# =============================================================================

@router.get(
    "/me",
    summary="Retorna el perfil del usuario autenticado",
)
async def me(
    usuario: PayloadToken = Depends(get_usuario_actual),
    db:      AsyncSession = Depends(obtener_sesion),
):
    """
    Retorna los datos del usuario actual extraídos del JWT + DB.
    Usado por el frontend para mostrar el nombre y plan en la barra superior.
    """
    result = await db.execute(
        text("""
            SELECT u.nombre, u.email, u.rol, u.ultimo_login,
                   t.nombre_empresa, t.plan, t.estado
            FROM   usuarios u
            JOIN   tenants  t ON t.id = u.tenant_id
            WHERE  u.id = :user_id
        """),
        {"user_id": usuario.sub},
    )
    fila = result.fetchone()
    if not fila:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    nombre, email, rol, ultimo_login, empresa, plan, estado = fila
    return {
        "id":             usuario.sub,
        "tenant_id":      usuario.tenant_id,
        "nombre":         nombre,
        "email":          email,
        "rol":            rol,
        "plan":           plan,
        "nombre_empresa": empresa,
        "estado_tenant":  estado,
        "ultimo_login":   str(ultimo_login) if ultimo_login else None,
    }


# =============================================================================
# POST /refresh
# =============================================================================

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renueva el token JWT del usuario actual",
)
async def refresh_token(
    usuario: PayloadToken = Depends(get_usuario_actual),
    db:      AsyncSession = Depends(obtener_sesion),
):
    """
    Emite un nuevo JWT con fecha de expiración actualizada.
    El token anterior sigue siendo válido hasta que expire.
    """
    # Verificar que el usuario siga activo en DB
    result = await db.execute(
        text("SELECT estado FROM usuarios WHERE id = :id"),
        {"id": usuario.sub},
    )
    fila = result.fetchone()
    if not fila or fila[0] != "activo":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Cuenta desactivada.")

    nuevo_payload = PayloadToken(
        sub=usuario.sub,
        tenant_id=usuario.tenant_id,
        rol=usuario.rol,
        nombre=usuario.nombre,
        plan=usuario.plan,
    )
    token = crear_access_token(nuevo_payload)
    return TokenResponse(
        access_token=token,
        usuario={"nombre": usuario.nombre, "rol": usuario.rol, "plan": usuario.plan},
    )

# =============================================================================
# POST /social
# =============================================================================

@router.post(
    "/social",
    response_model=TokenResponse,
    summary="Login / Registro Unificado con Redes Sociales",
)
async def social_login_or_register(
    datos: SocialLoginRequest,
    db:    AsyncSession = Depends(obtener_sesion)
):
    """
    Endpoint de Social Login / Registro Unificado.
    1. Si el usuario existe -> Login (Retorna JWT).
    2. Si NO existe -> Crea Tenant + Usuario + Agente Yanua + Guarda Token OAuth.
    """
    code = datos.code
    provider = datos.provider

    # 1. Obtener datos de Google/Microsoft
    auth_service = UnifiedSocialAuthService()
    user_data = await auth_service.handle_provider_exchange(code, provider)
    email_normalizado = user_data["email"].lower().strip()
    
    # 2. Verificar si el usuario ya existe
    result = await db.execute(
        text("SELECT id, nombre, tenant_id, rol, plan_actual as plan FROM usuarios u JOIN tenants t ON u.tenant_id = t.id WHERE u.email = :email"),
        {"email": email_normalizado}
    )
    existing_user = result.fetchone()
    
    if existing_user:
        # === CASO A: LOGIN ===
        user_id = existing_user.id
        tenant_id = existing_user.tenant_id
        
        # Actualizar último login
        await configurar_rls(db, tenant_id)
        await db.execute(
            text("UPDATE usuarios SET ultimo_login = NOW() WHERE id = :id"),
            {"id": str(user_id)}
        )
        await db.commit()
        
        token_payload = PayloadToken(
            sub=str(user_id),
            tenant_id=str(tenant_id),
            rol=existing_user.rol,
            nombre=existing_user.nombre,
            plan=existing_user.plan,
        )
        token = crear_access_token(token_payload)
        
        return TokenResponse(
            access_token=token,
            is_new_user=False,
            usuario={
                "id": str(user_id),
                "nombre": existing_user.nombre,
                "email": email_normalizado,
                "rol": existing_user.rol,
                "plan": existing_user.plan,
                "tenant_id": str(tenant_id)
            }
        )
    else:
        # === CASO B: SIGN UP (Súper Transacción) ===
        tenant_id = uuid4()
        user_id = uuid4()
        nombre_empresa = f"{user_data['name'].strip()} Store"
        
        # B.1 Crear Tenant
        await db.execute(
            text("""
                INSERT INTO tenants (id, nombre_empresa, email_contacto, plan,
                                     max_agentes, max_mensajes_mes, max_instancias_whatsapp,
                                     color_primario)
                VALUES (:id, :empresa, :email, 'starter',
                        1, 500, 1,
                        '#6366f1')
            """),
            {
                "id": str(tenant_id),
                "empresa": nombre_empresa,
                "email": email_normalizado
            }
        )
        
        # B.2 Crear Usuario (fn_crear_usuario bypassa RLS)
        dummy_password = hash_password(str(uuid4()))
        await db.execute(
            text("""
                SELECT fn_crear_usuario(
                    CAST(:uid AS UUID), CAST(:tid AS UUID), :email, :phash, :nombre, 'admin'
                )
            """),
            {
                "uid": str(user_id),
                "tid": str(tenant_id),
                "email": email_normalizado,
                "phash": dummy_password,
                "nombre": user_data["name"].strip()
            }
        )
        
        # B.3 Crear Agente Yanua
        agent_id = uuid4()
        await db.execute(
            text("""
                INSERT INTO agents (
                    id, tenant_id, nombre, area, estado,
                    modelo, temperatura, max_tokens, canales
                )
                VALUES (
                    :id, :tenant_id, 'Yanua', 'Asistente Principal', 'activo',
                    'nomic-embed-text', 0.7, 512, ARRAY['web_chat']::text[]
                )
            """),
            {
                "id": str(agent_id),
                "tenant_id": str(tenant_id)
            }
        )
        
        # B.4 Pre-conectar la cuenta (OAuth Sheets)
        if user_data.get("oauth_refresh_token"):
            enc_service = EncryptionService()
            await db.execute(
                text("""
                    INSERT INTO connected_accounts (
                        id, tenant_id, provider, provider_user_id, provider_email,
                        access_token_encrypted, refresh_token_encrypted, is_active
                    ) VALUES (
                        :id, :tenant_id, :provider, :provider_id, :email,
                        :access, :refresh, TRUE
                    )
                """),
                {
                    "id": str(uuid4()),
                    "tenant_id": str(tenant_id),
                    "provider": provider,
                    "provider_id": user_data.get("provider_id"),
                    "email": email_normalizado,
                    "access": enc_service.encrypt(user_data["oauth_access_token"]),
                    "refresh": enc_service.encrypt(user_data["oauth_refresh_token"])
                }
            )
        
        await db.commit()
        
        token_payload = PayloadToken(
            sub=str(user_id),
            tenant_id=str(tenant_id),
            rol="admin",
            nombre=user_data["name"].strip(),
            plan="starter",
        )
        token = crear_access_token(token_payload)
        
        return TokenResponse(
            access_token=token,
            is_new_user=True,
            usuario={
                "id": str(user_id),
                "nombre": user_data["name"].strip(),
                "email": email_normalizado,
                "rol": "admin",
                "plan": "starter",
                "tenant_id": str(tenant_id),
                "nombre_empresa": nombre_empresa
            }
        )
