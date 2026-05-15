import httpx
from typing import Dict
from config import obtener_config
from core.encryption import EncryptionService


def _build_redirect_uri(settings, path: str) -> str:
    """
    Construye redirect_uri de forma robusta.
    Prioridad: OAUTH_REDIRECT_BASE_URL > api_base_url > primer cors_origin > fallback local.
    Nunca indexa cors_origins directamente (puede estar vacío).
    """
    base = (
        getattr(settings, "oauth_redirect_base_url", None)
        or getattr(settings, "api_base_url", None)
        or (settings.cors_origins[0] if settings.cors_origins else None)
        or "http://localhost:9000"
    )
    return f"{base}{path}"


class UnifiedSocialAuthService:
    """
    Gestiona la autenticación con Google y Microsoft.
    Retorna datos del usuario Y los tokens OAuth para pre-conectar Google Sheets.
    Los tokens se cifran con EncryptionService antes de retornarse para persistencia.
    """

    def __init__(self):
        self.settings = obtener_config()
        self.PROVIDERS = {
            "google": {
                "token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
                "client_id": getattr(self.settings, "GOOGLE_OAUTH_CLIENT_ID", ""),
                "client_secret": getattr(self.settings, "GOOGLE_OAUTH_CLIENT_SECRET", ""),
                "redirect_uri": _build_redirect_uri(
                    self.settings, "/api/v1/auth/callback/google"
                ),
            },
            "microsoft": {
                "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                "userinfo_url": "https://graph.microsoft.com/v1.0/me",
                "client_id": getattr(self.settings, "MICROSOFT_OAUTH_CLIENT_ID", ""),
                "client_secret": getattr(self.settings, "MICROSOFT_OAUTH_CLIENT_SECRET", ""),
                "redirect_uri": _build_redirect_uri(
                    self.settings, "/api/v1/auth/callback/microsoft"
                ),
            },
        }

    async def handle_provider_exchange(self, code: str, provider: str) -> Dict:
        """
        1. Intercambia el 'code' por 'access_token' y 'refresh_token'.
        2. Obtiene el perfil del usuario.
        3. Cifra los tokens con EncryptionService antes de retornarlos.
        4. Retorna un diccionario listo para guardar en BD.
        """
        if provider not in self.PROVIDERS:
            raise ValueError(f"Proveedor no soportado: {provider}")

        config = self.PROVIDERS[provider]

        async with httpx.AsyncClient() as client:
            # --- Paso A: Obtener Tokens ---
            token_data = {
                "code": code,
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "redirect_uri": config["redirect_uri"],
                "grant_type": "authorization_code",
            }

            if provider == "microsoft":
                token_data["scope"] = "https://graph.microsoft.com/.default"

            token_response = await client.post(config["token_url"], data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()

            # --- Paso B: Obtener Perfil de Usuario ---
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            user_response = await client.get(config["userinfo_url"], headers=headers)
            user_response.raise_for_status()
            profile = user_response.json()

        # --- Paso C: Cifrar tokens antes de persistir ---
        access_token_raw = tokens.get("access_token", "")
        refresh_token_raw = tokens.get("refresh_token", "")

        encrypted_access = (
            EncryptionService.encrypt(access_token_raw) if access_token_raw else None
        )
        encrypted_refresh = (
            EncryptionService.encrypt(refresh_token_raw) if refresh_token_raw else None
        )

        # --- Paso D: Estandarizar datos ---
        if provider == "google":
            return {
                "email": profile.get("email"),
                "name": profile.get("name"),
                "avatar": profile.get("picture"),
                "provider": "google",
                "provider_id": profile.get("sub"),
                "oauth_access_token": encrypted_access,
                "oauth_refresh_token": encrypted_refresh,
            }
        elif provider == "microsoft":
            return {
                "email": profile.get("userPrincipalName") or profile.get("mail"),
                "name": profile.get("displayName"),
                "avatar": None,
                "provider": "microsoft",
                "provider_id": profile.get("id"),
                "oauth_access_token": encrypted_access,
                "oauth_refresh_token": encrypted_refresh,
            }
