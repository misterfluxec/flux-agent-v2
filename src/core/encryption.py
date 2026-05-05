"""
FLUXAGENT V2 — ENCRYPTION SERVICE (Producción-Ready)
=====================================================
Servicio de cifrado para credenciales sensibles (tokens BYOA, API keys).

Modo MVP  : ENCRYPT_SENSITIVE_DATA=false → base64 puro (sin cifrado real)
Modo Prod : ENCRYPT_SENSITIVE_DATA=true  → Fernet (AES-128-CBC) + PBKDF2

Generar ENCRYPTION_KEY:
    openssl rand -base64 32

Activar en .env:
    ENCRYPT_SENSITIVE_DATA=true
    ENCRYPTION_KEY="<resultado del comando anterior>"
"""

import os
import base64
import logging
from typing import Optional, Union

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Error de cifrado/descifrado."""
    pass


class EncryptionService:
    """
    Servicio singleton para cifrado simétrico de credenciales BYOA.

    Uso típico:
        # Al arrancar la app (lifespan):
        EncryptionService.initialize()

        # Cifrar antes de guardar en BD:
        token_seguro = EncryptionService.encrypt(token_plano)

        # Descifrar al leer de BD:
        token_plano = EncryptionService.decrypt(token_seguro)

        # En logs (nunca el valor real):
        logger.info("Token: %s", EncryptionService.mask(token_seguro))
    """

    _instance = None
    _fernet: Optional[Fernet] = None
    _enabled: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ------------------------------------------------------------------
    # Inicialización
    # ------------------------------------------------------------------

    @classmethod
    def initialize(
        cls,
        encryption_key: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        """
        Inicializa el servicio. Llamar una sola vez en el startup de la app.

        Args:
            encryption_key: Clave maestra (mínimo 32 chars). Si None, lee ENCRYPTION_KEY.
            enabled: Forzar estado. Si None, lee ENCRYPT_SENSITIVE_DATA.
        """
        cls._enabled = enabled if enabled is not None else (
            os.getenv("ENCRYPT_SENSITIVE_DATA", "false").lower() == "true"
        )

        if not cls._enabled:
            logger.info("🔓 EncryptionService: Modo MVP (sin cifrado real)")
            return

        key = encryption_key or os.getenv("ENCRYPTION_KEY", "")
        if not key:
            raise ValueError(
                "ENCRYPTION_KEY es requerida cuando ENCRYPT_SENSITIVE_DATA=true. "
                "Generarla con: openssl rand -base64 32"
            )

        cls._fernet = cls._derive_fernet(key)
        logger.info("🔐 EncryptionService: Fernet activo (PBKDF2-SHA256, 100k iteraciones)")

    @classmethod
    def _derive_fernet(cls, password: str) -> Fernet:
        """Deriva clave Fernet de 32 bytes desde la contraseña usando PBKDF2."""
        salt = b"fluxagent_byoa_salt_v1"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key)

    # ------------------------------------------------------------------
    # Operaciones principales
    # ------------------------------------------------------------------

    @classmethod
    def encrypt(cls, plaintext: Union[str, bytes]) -> str:
        """
        Cifra un valor y retorna string base64.

        En modo MVP: codifica en base64 sin cifrar (reversible).
        En modo Prod: cifra con Fernet y codifica en base64.
        """
        if isinstance(plaintext, str):
            plaintext_bytes = plaintext.encode()
        else:
            plaintext_bytes = plaintext

        if not cls._enabled:
            return base64.urlsafe_b64encode(plaintext_bytes).decode()

        try:
            encrypted = cls._fernet.encrypt(plaintext_bytes)
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error("Encryption failed: %s", e, exc_info=True)
            raise EncryptionError(f"Error cifrando datos: {e}")

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """
        Descifra un string base64 y retorna el valor original.

        En modo MVP: decodifica base64 directamente.
        En modo Prod: descifra con Fernet.
        """
        if not ciphertext:
            return ciphertext

        if not cls._enabled:
            try:
                return base64.urlsafe_b64decode(ciphertext.encode()).decode()
            except Exception:
                return ciphertext  # Datos previos al encoding, compatibilidad

        try:
            raw = base64.urlsafe_b64decode(ciphertext.encode())
            decrypted = cls._fernet.decrypt(raw)
            return decrypted.decode()
        except InvalidToken:
            logger.error("Decryption failed: token inválido o clave incorrecta")
            raise EncryptionError("Descifrado fallido: token inválido o clave no coincide")
        except Exception as e:
            logger.error("Decryption failed: %s", e, exc_info=True)
            raise EncryptionError(f"Error descifrando datos: {e}")

    @classmethod
    def mask(cls, value: Optional[str], visible_chars: int = 4) -> str:
        """
        Enmascara un valor para logs seguros.
        Ejemplo: 'EAABm0Px9Zk...' → 'EAAB***_Zk'
        """
        if not value:
            return "NULL"
        if value in ("NULL", "") or value.startswith("*"):
            return value

        # Intentar decodificar para enmascarar el valor real, no el encoding
        try:
            if cls._enabled and cls._fernet:
                decoded = cls.decrypt(value)
            else:
                decoded = base64.urlsafe_b64decode(value.encode()).decode()
        except Exception:
            decoded = value

        if len(decoded) <= visible_chars * 2:
            return "*" * len(decoded)
        return decoded[:visible_chars] + "***" + decoded[-visible_chars:]

    @classmethod
    def is_enabled(cls) -> bool:
        """Retorna True si el cifrado real está activo."""
        return cls._enabled


# ---------------------------------------------------------------------------
# Función de compatibilidad (para imports existentes: from core.encryption import mask_sensitive)
# ---------------------------------------------------------------------------

def mask_sensitive(value: Optional[str], visible_chars: int = 4) -> str:
    """Wrapper de compatibilidad para EncryptionService.mask()."""
    return EncryptionService.mask(value, visible_chars)
