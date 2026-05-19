import logging
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from pydantic import BaseModel

from database import obtener_sesion
from services.unified_oauth import UnifiedOAuthService
from services.spreadsheet_sync_rag import RAGSyncEngine
from core.sensitive_logger import log_safe

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/oauth", tags=["OAuth & Sync"])

class SyncRequest(BaseModel):
    tenant_id: str
    agent_id: str
    source_id: str
    source_name: str
    source_type: str
    column_mapping: Dict[str, str]

@router.get("/authorize/{provider}")
async def authorize_provider(provider: str, tenant_id: str, request: Request):
    """
    Inicia el flujo de OAuth2 redirigiendo al proveedor.
    """
    scopes = []
    if provider == "google":
        scopes = ["openid", "email", "profile", "https://www.googleapis.com/auth/spreadsheets.readonly"]
    elif provider == "microsoft":
        scopes = ["openid", "email", "profile", "offline_access", "Files.Read.All"]
    
    # Usamos tenant_id como state para simplificar (en prod, usar JWT firmado)
    state = tenant_id
    url = UnifiedOAuthService.get_auth_url(provider, scopes, state)
    return RedirectResponse(url)

@router.get("/callback/{provider}")
@log_safe
async def oauth_callback(provider: str, code: str, state: str):
    """
    Recibe el código OAuth, intercambia por tokens y guarda en connected_accounts.
    """
    tenant_id = state
    
    try:
        # 1. Obtener tokens
        tokens = await UnifiedOAuthService.exchange_code_for_tokens(provider, code, state)
        access_token_enc = tokens["access_token"]
        refresh_token_enc = tokens["refresh_token"]
        
        # 2. Obtener info del usuario (opcional, para UI)
        # user_info = await UnifiedOAuthService.get_user_info(provider, EncryptionService.decrypt(access_token_enc))
        
        # 3. Guardar en DB
        async with obtener_sesion() as db:
            async with db.begin():
                await db.execute(text("""
                    INSERT INTO connected_accounts 
                    (tenant_id, provider, provider_user_id, provider_email, access_token_encrypted, refresh_token_encrypted)
                    VALUES (:tenant_id, :provider, :user_id, :email, :access, :refresh)
                    ON CONFLICT (tenant_id, provider, provider_user_id) 
                    DO UPDATE SET 
                        access_token_encrypted = EXCLUDED.access_token_encrypted,
                        refresh_token_encrypted = EXCLUDED.refresh_token_encrypted,
                        updated_at = NOW()
                """), {
                    "tenant_id": tenant_id,
                    "provider": provider,
                    "user_id": "oauth_user", # Simplificado
                    "email": "user@domain.com", # Simplificado
                    "access": access_token_enc,
                    "refresh": refresh_token_enc
                })
                
        return {"status": "success", "message": f"Cuenta {provider} conectada exitosamente"}
        
    except Exception as e:
        logger.error(f"Error en callback OAuth {provider}: {e}")
        raise HTTPException(status_code=500, detail="Error de autenticación")

@router.post("/sync/preview")
async def preview_sheet(req: SyncRequest):
    """Obtiene una vista previa de la hoja para validar las columnas"""
    try:
        async with obtener_sesion() as db:
            result = await db.execute(text("""
                SELECT access_token_encrypted FROM connected_accounts
                WHERE tenant_id = :tenant_id AND provider = :provider LIMIT 1
            """), {"tenant_id": req.tenant_id, "provider": "google" if req.source_type == "google_sheets" else "microsoft"})
            row = result.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Cuenta no conectada")
                
            from core.encryption import EncryptionService
            access_token = EncryptionService.decrypt(row[0])
            
            if req.source_type == "google_sheets":
                headers, rows = await RAGSyncEngine.fetch_google_sheet_data(access_token, req.source_id)
            else:
                headers, rows = await RAGSyncEngine.fetch_excel_online_data(access_token, req.source_id)
                
            mapping = RAGSyncEngine.detect_column_mapping(headers)
            
            return {
                "headers": headers,
                "suggested_mapping": mapping,
                "preview_rows": rows[:3]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
