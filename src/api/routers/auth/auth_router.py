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
    company_name: Optional[str] = None
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
    2. Un usuario con role 'admin' vinculado a ese tenant
    3. Retorna un JWT listo para usar

    Los límites del plan (starter/pro/enterprise) se aplican automáticamente.
    
    Si es plan enterprise, opcionalmente guarda branding (color, logo, etc.)
    """
    email_normalizado = datos.email.lower().strip()
    
    # Verificar email único
    result = await db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": email_normalizado},
    )
    if result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado. Intenta iniciar sesión.",
        )

    # Límites por plan
    PLAN_LIMITES = {
        "starter":    {"max_agents": 1,  "max_messages_month": 500,  "max_whatsapp_instances": 1},
        "pro":        {"max_agents": 5,  "max_messages_month": 5000, "max_whatsapp_instances": 3},
        "enterprise": {"max_agents": 20, "max_messages_month": 50000,"max_whatsapp_instances": 10},
    }
    limites = PLAN_LIMITES.get(datos.plan, PLAN_LIMITES["starter"])

    # Si es empresa y tiene name de empresa, usarla. 
    # Si es individual y tiene name de empresa, usarlo como name de tienda.
    # Si no hay name de empresa, usar el name del usuario + " Store"
    nombre_usuario_str = (datos.nombre_usuario or "").strip()
    nombre_empresa_final = (datos.company_name or "").strip() if datos.company_name else f"{nombre_usuario_str} Store"

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
            INSERT INTO tenants (id, company_name, contact_email, plan,
                                 max_agents, max_messages_month, max_whatsapp_instances,
                                 primary_color, branding_config)
            VALUES (:id, :empresa, :email, :plan,
                    :max_agents, :max_mensajes, :max_whatsapp,
                    :color, :branding)
        """),
        {
            "id":          str(tenant_id),
            "empresa":     nombre_empresa_final,
            "email":       email_normalizado,
            "plan":        datos.plan,
            "max_agents": limites["max_agents"],
            "max_mensajes": limites["max_messages_month"],
            "max_whatsapp": limites["max_whatsapp_instances"],
            "color":       datos.branding.get("primary_color") if datos.branding else "#6366f1",
            "branding":    branding_json,
        },
    )
    # Removing early commit to keep transaction atomic
    # Crear usuario usando fn_crear_usuario (SECURITY DEFINER, bypassa RLS)
    password_hash = hash_password(datos.password)
    await db.execute(
        text("""
            SELECT fn_crear_usuario(
                CAST(:tid AS UUID), CAST(:uid AS UUID), :name, :email, :phash, 'admin'
            )
        """),
        {
            "tid":    str(tenant_id),
            "uid":    str(usuario_id),
            "name": nombre_usuario_str,
            "email":  (datos.email or "").lower().strip(),
            "phash":  password_hash,
        },
    )
    
    # Auto-crear agente inicial "Yanua" por defecto para el Wizard RAG
    agent_id = uuid4()
    await db.execute(
        text("""
            INSERT INTO agents (
                id, tenant_id, name, area, status,
                model, temperature, max_tokens, channels
            )
            VALUES (
                :id, :tenant_id, 'Yanua', 'Asistente Principal', 'is_active',
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
        role="admin",
        name=nombre_usuario_str,
        plan=datos.plan,
    )
    token = crear_access_token(token_payload)

    logger.info(f"Nuevo tenant registrado: {nombre_empresa_final} | plan={datos.plan}")
    return TokenResponse(
        access_token=token,
        usuario={
            "id":          str(usuario_id),
            "name":      nombre_usuario_str,
            "email":       email_normalizado,
            "role":         "admin",
            "plan":        datos.plan,
            "tenant_id":   str(tenant_id),
            "company_name": nombre_empresa_final,
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
    Si son correctas, retorna un JWT que incluye tenant_id, role y name.

    El frontend debe guardar este token (localStorage o cookie httpOnly)
    y enviarlo en cada request como: Authorization: Bearer <token>
    """
    email = credenciales.email.lower().strip()

    # Buscar usuario usando fn_login_usuario (SECURITY DEFINER, bypassa RLS)
    result = await db.execute(
        text("SELECT id, tenant_id, password_hash, name, role, plan, company_name, estado_tenant FROM fn_login_usuario(:email)"),
        {"email": email},
    )
    fila = result.fetchone()

    if not fila:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos.",
        )

    user_id, tenant_id, pwd_hash, name, role, plan, empresa, tenant_estado = fila

    # Verificar tenant is_active
    if tenant_estado != "is_active":
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
        text("UPDATE users SET last_login = NOW() WHERE id = :id"),
        {"id": str(user_id)},
    )
    await db.commit()

    # Generar JWT
    token_payload = PayloadToken(
        sub=str(user_id),
        tenant_id=str(tenant_id),
        role=role,
        name=name,
        plan=plan,
    )
    token = crear_access_token(token_payload)

    logger.info(f"Login exitoso: {email} | tenant={tenant_id} | role={role}")
    return TokenResponse(
        access_token=token,
        usuario={
            "id":             str(user_id),
            "name":         name,
            "email":          email,
            "role":            role,
            "plan":           plan,
            "tenant_id":      str(tenant_id),
            "company_name": empresa,
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
    Usado por el frontend para mostrar el name y plan en la barra superior.
    """
    result = await db.execute(
        text("""
            SELECT u.name, u.email, u.role, u.last_login,
                   t.company_name, t.plan, t.status
            FROM   users u
            JOIN   tenants  t ON t.id = u.tenant_id
            WHERE  u.id = :user_id
        """),
        {"user_id": usuario.sub},
    )
    fila = result.fetchone()
    if not fila:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    name, email, role, last_login, empresa, plan, status = fila
    return {
        "id":             usuario.sub,
        "tenant_id":      usuario.tenant_id,
        "name":         name,
        "email":          email,
        "role":            role,
        "plan":           plan,
        "company_name": empresa,
        "estado_tenant":  status,
        "last_login":   str(last_login) if last_login else None,
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
    # Verificar que el usuario siga is_active en DB
    result = await db.execute(
        text("SELECT status FROM users WHERE id = :id"),
        {"id": usuario.sub},
    )
    fila = result.fetchone()
    if not fila or fila[0] != "is_active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Cuenta desactivada.")

    nuevo_payload = PayloadToken(
        sub=usuario.sub,
        tenant_id=usuario.tenant_id,
        role=usuario.role,
        name=usuario.name,
        plan=usuario.plan,
    )
    token = crear_access_token(nuevo_payload)
    return TokenResponse(
        access_token=token,
        usuario={"name": usuario.name, "role": usuario.role, "plan": usuario.plan},
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
        text("SELECT id, name, tenant_id, role, plan_actual as plan FROM users u JOIN tenants t ON u.tenant_id = t.id WHERE u.email = :email"),
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
            text("UPDATE users SET last_login = NOW() WHERE id = :id"),
            {"id": str(user_id)}
        )
        await db.commit()
        
        token_payload = PayloadToken(
            sub=str(user_id),
            tenant_id=str(tenant_id),
            role=existing_user.role,
            name=existing_user.name,
            plan=existing_user.plan,
        )
        token = crear_access_token(token_payload)
        
        return TokenResponse(
            access_token=token,
            is_new_user=False,
            usuario={
                "id": str(user_id),
                "name": existing_user.name,
                "email": email_normalizado,
                "role": existing_user.role,
                "plan": existing_user.plan,
                "tenant_id": str(tenant_id)
            }
        )
    else:
        # === CASO B: SIGN UP (Súper Transacción) ===
        tenant_id = uuid4()
        user_id = uuid4()
        company_name = f"{user_data['name'].strip()} Store"
        
        # B.1 Crear Tenant
        await db.execute(
            text("""
                INSERT INTO tenants (id, company_name, contact_email, plan,
                                     max_agents, max_messages_month, max_whatsapp_instances,
                                     primary_color)
                VALUES (:id, :empresa, :email, 'starter',
                        1, 500, 1,
                        '#6366f1')
            """),
            {
                "id": str(tenant_id),
                "empresa": company_name,
                "email": email_normalizado
            }
        )
        
        # B.2 Crear Usuario (fn_crear_usuario bypassa RLS)
        dummy_password = hash_password(str(uuid4()))
        await db.execute(
            text("""
                SELECT fn_crear_usuario(
                    CAST(:uid AS UUID), CAST(:tid AS UUID), :email, :phash, :name, 'admin'
                )
            """),
            {
                "uid": str(user_id),
                "tid": str(tenant_id),
                "email": email_normalizado,
                "phash": dummy_password,
                "name": user_data["name"].strip()
            }
        )
        
        # B.3 Crear Agente Yanua
        agent_id = uuid4()
        await db.execute(
            text("""
                INSERT INTO agents (
                    id, tenant_id, name, area, status,
                    model, temperature, max_tokens, channels
                )
                VALUES (
                    :id, :tenant_id, 'Yanua', 'Asistente Principal', 'is_active',
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
            role="admin",
            name=user_data["name"].strip(),
            plan="starter",
        )
        token = crear_access_token(token_payload)
        
        return TokenResponse(
            access_token=token,
            is_new_user=True,
            usuario={
                "id": str(user_id),
                "name": user_data["name"].strip(),
                "email": email_normalizado,
                "role": "admin",
                "plan": "starter",
                "tenant_id": str(tenant_id),
                "company_name": company_name
            }
        )
