import httpx
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from urllib.parse import urlencode

from config import obtener_config
config = obtener_config()
from core.encryption import EncryptionService

logger = logging.getLogger(__name__)

class UnifiedOAuthService:
    """
    Servicio unificado para OAuth2 con proveedores populares en LATAM.
    Soportados: Google (Gmail + Sheets), Microsoft (Outlook + Excel), Yahoo.
    """
    
    # URL Base por defecto si no está en config
    API_BASE_URL = getattr(config, 'api_base_url', 'http://localhost:9000')

    PROVIDERS = {
        "google": {
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
            "client_id": getattr(config, 'google_oauth_client_id', ''),
            "client_secret": getattr(config, 'google_oauth_client_secret', ''),
            "redirect_uri": f"{API_BASE_URL}/api/v1/oauth/callback/google",
        },
        "microsoft": {
            "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            "userinfo_url": "https://graph.microsoft.com/v1.0/me",
            "client_id": getattr(config, 'microsoft_oauth_client_id', ''),
            "client_secret": getattr(config, 'microsoft_oauth_client_secret', ''),
            "redirect_uri": f"{API_BASE_URL}/api/v1/oauth/callback/microsoft",
        },
        "yahoo": {
            "auth_url": "https://api.login.yahoo.com/oauth2/request_auth",
            "token_url": "https://api.login.yahoo.com/oauth2/get_token",
            "userinfo_url": "https://api.login.yahoo.com/openid/v1/userinfo",
            "client_id": getattr(config, 'yahoo_oauth_client_id', ''),
            "client_secret": getattr(config, 'yahoo_oauth_client_secret', ''),
            "redirect_uri": f"{API_BASE_URL}/api/v1/oauth/callback/yahoo",
        }
    }
    
    @classmethod
    def get_auth_url(cls, provider: str, scopes: List[str], state: Optional[str] = None) -> str:
        if provider not in cls.PROVIDERS:
            raise ValueError(f"Proveedor no soportado: {provider}")
        
        cfg = cls.PROVIDERS[provider]
        state = state or secrets.token_urlsafe(32)
        
        params = {
            "client_id": cfg["client_id"],
            "redirect_uri": cfg["redirect_uri"],
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        
        if provider == "google":
            params["include_granted_scopes"] = "true"
        elif provider == "microsoft":
            params["response_mode"] = "query"
            
        return f"{cfg['auth_url']}?{urlencode(params)}"
    
    @classmethod
    async def exchange_code_for_tokens(cls, provider: str, code: str, state: str) -> Dict:
        if provider not in cls.PROVIDERS:
            raise ValueError(f"Proveedor no soportado: {provider}")
            
        cfg = cls.PROVIDERS[provider]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                cfg["token_url"],
                data={
                    "client_id": cfg["client_id"],
                    "client_secret": cfg["client_secret"],
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": cfg["redirect_uri"],
                },
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            tokens = response.json()
            
        return {
            "access_token": EncryptionService.encrypt(tokens["access_token"]),
            "refresh_token": EncryptionService.encrypt(tokens.get("refresh_token", "")),
            "expires_in": tokens.get("expires_in", 3600),
            "token_type": tokens.get("token_type", "Bearer"),
            "scope": tokens.get("scope", ""),
        }
        
    @classmethod
    async def get_user_info(cls, provider: str, access_token: str) -> Dict:
        cfg = cls.PROVIDERS[provider]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(cfg["userinfo_url"], headers=headers)
            response.raise_for_status()
            return response.json()
            
    @classmethod
    async def refresh_access_token(cls, provider: str, refresh_token_encrypted: str) -> Dict:
        cfg = cls.PROVIDERS[provider]
        refresh_token = EncryptionService.decrypt(refresh_token_encrypted)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                cfg["token_url"],
                data={
                    "client_id": cfg["client_id"],
                    "client_secret": cfg["client_secret"],
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            tokens = response.json()
            
        return {
            "access_token": EncryptionService.encrypt(tokens["access_token"]),
            "expires_in": tokens.get("expires_in", 3600),
            "scope": tokens.get("scope", ""),
        }
