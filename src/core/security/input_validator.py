"""
Reusable Pydantic Validators for Input Sanitization
Centraliza validaciones de dominio para mantener consistencia y seguridad.
"""
import re
from typing import Annotated, TypeVar, Union
from pydantic import Field, field_validator, BaseModel
from pydantic_core import PydanticCustomError
from enum import Enum

# ─────────────────────────────────────────────────────────────
# Validadores de Campo Reutilizables (Annotated)
# ─────────────────────────────────────────────────────────────

def validate_password_strength(value: str) -> str:
    """
    Valida que el password cumpla política bancaria:
    - Mínimo 8 caracteres
    - Al menos 1 mayúscula
    - Al menos 1 número
    - Al menos 1 carácter especial (!@#$%^&*()_+-=[]{}|;:,.<>?)
    """
    if len(value) < 8:
        raise PydanticCustomError(
            "password_too_short",
            "Password must be at least 8 characters long"
        )
    if not re.search(r"[A-Z]", value):
        raise PydanticCustomError(
            "password_no_uppercase",
            "Password must contain at least one uppercase letter"
        )
    if not re.search(r"\d", value):
        raise PydanticCustomError(
            "password_no_digit",
            "Password must contain at least one number"
        )
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", value):
        raise PydanticCustomError(
            "password_no_special",
            "Password must contain at least one special character"
        )
    return value


def validate_temperature(value: float) -> float:
    """Valida que la temperature de LLM esté en rango seguro [0.0, 1.0]"""
    if not 0.0 <= value <= 1.0:
        raise PydanticCustomError(
            "temperature_out_of_range",
            "Temperature must be between 0.0 and 1.0"
        )
    return value


def validate_max_tokens(value: int) -> int:
    """Valida límite de tokens para prevenir DoS por prompts gigantes"""
    if not 1 <= value <= 8192:
        raise PydanticCustomError(
            "tokens_out_of_range",
            "Max tokens must be between 1 and 8192"
        )
    return value


def validate_webhook_url(value: str) -> str:
    """Valida que una URL de webhook sea HTTPS y tenga dominio válido"""
    if not value.startswith("https://"):
        raise PydanticCustomError(
            "webhook_not_https",
            "Webhook URL must use HTTPS protocol"
        )
    if not re.match(r"^https://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$", value):
        raise PydanticCustomError(
            "webhook_invalid_format",
            "Webhook URL has invalid format"
        )
    return value


# ─────────────────────────────────────────────────────────────
# Type Aliases con Validación Incorporada (Reutilizables)
# ─────────────────────────────────────────────────────────────

# Para uso con Pydantic V2
SecurePassword = Annotated[
    str,
    Field(min_length=8, max_length=128, description="Password con política de seguridad")
]

TemperatureField = Annotated[
    float,
    Field(default=0.7, ge=0.0, le=1.0, description="Temperatura de creatividad del LLM"),
]

TokensField = Annotated[
    int,
    Field(default=512, ge=1, le=8192, description="Límite de tokens para generación"),
]

WebhookURL = Annotated[
    str,
    Field(max_length=512, description="URL HTTPS para webhooks"),
]

# ─────────────────────────────────────────────────────────────
# Enums de Dominio Validados
# ─────────────────────────────────────────────────────────────

class LLMProviderEnum(str, Enum):
    """Proveedores de LLM soportados con validación de name"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    
    @classmethod
    def is_local(cls, provider: str) -> bool:
        return provider == cls.OLLAMA


class AgentTypeEnum(str, Enum):
    """Tipos de agente con validación estricta"""
    SALES = "sales"
    SUPPORT = "support"
    RESERVATIONS = "reservations"
    CUSTOM = "custom"


# ─────────────────────────────────────────────────────────────
# BaseModel Base con Validación Común
# ─────────────────────────────────────────────────────────────

class SecureBaseModel(BaseModel):
    """
    BaseModel con validaciones de seguridad aplicadas por defecto.
    Heredar de esta clase para todos los schemas de entrada de API.
    """
    
    @field_validator("*", mode="before")
    @classmethod
    def sanitize_input(cls, v):
        """
        Sanitización exhaustiva de inputs:
        1. Previene inyección XSS eliminando HTML tags vía Bleach.
        2. Elimina espacios en blanco excesivos.
        """
        if isinstance(v, str):
            # Limpiar XSS (remueve tags html/script/etc)
            import bleach
            v_clean = bleach.clean(v, tags=[], attributes={}, protocols=[], strip=True)
            return v_clean.strip()
        return v
    
    model_config = {
        "extra": "forbid",
        "strict": True
    }
