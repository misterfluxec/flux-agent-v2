from __future__ import annotations
from typing import Any
from uuid import uuid4


class FluxError(Exception):
    http_status: int = 500
    error_code: str = "INTERNAL_ERROR"
    default_message: str = "Error interno del servidor"

    def __init__(self, message: str | None = None, detail: Any = None):
        self.message = message or self.default_message
        self.detail = detail
        self.instance_id = str(uuid4())
        super().__init__(self.message)

    def to_problem(self, path: str = "") -> dict:
        return {
            "type": f"https://fluxagent.io/errors/{self.error_code.lower()}",
            "title": self.error_code.replace("_", " ").title(),
            "status": self.http_status,
            "detail": self.message,
            "instance": f"{path}#{self.instance_id}",
            **({"extra": self.detail} if self.detail else {}),
        }


# ── Auth ──────────────────────────────────────────────
class AuthError(FluxError):
    http_status = 401
    error_code = "AUTH_ERROR"
    default_message = "No autenticado"


class TokenExpiredError(AuthError):
    error_code = "TOKEN_EXPIRED"
    default_message = "Token expirado"


class InsufficientPermissionsError(AuthError):
    http_status = 403
    error_code = "INSUFFICIENT_PERMISSIONS"
    default_message = "Permisos insuficientes"


# ── Tenant ────────────────────────────────────────────
class TenantError(FluxError):
    http_status = 403
    error_code = "TENANT_ERROR"
    default_message = "Error de tenant"


class TenantNotFoundError(TenantError):
    http_status = 404
    error_code = "TENANT_NOT_FOUND"
    default_message = "Tenant no encontrado"


class TenantIsolationError(TenantError):
    http_status = 403
    error_code = "TENANT_ISOLATION_VIOLATION"
    default_message = "Violación de aislamiento de tenant"


# ── Business Rules ────────────────────────────────────
class BusinessRuleError(FluxError):
    http_status = 422
    error_code = "BUSINESS_RULE_VIOLATION"
    default_message = "Regla de negocio violada"


class PlanLimitExceededError(BusinessRuleError):
    error_code = "PLAN_LIMIT_EXCEEDED"
    default_message = "Límite del plan alcanzado"


class InvalidStateTransitionError(BusinessRuleError):
    error_code = "INVALID_STATE_TRANSITION"
    default_message = "Transición de estado inválida"


class ResourceNotFoundError(BusinessRuleError):
    http_status = 404
    error_code = "RESOURCE_NOT_FOUND"
    default_message = "Recurso no encontrado"


# ── Commerce ──────────────────────────────────────────
class CommerceError(FluxError):
    http_status = 422
    error_code = "COMMERCE_ERROR"
    default_message = "Error en operación comercial"


class QuoteExpiredError(CommerceError):
    error_code = "QUOTE_EXPIRED"
    default_message = "La cotización ha expirado"


class InsufficientStockError(CommerceError):
    error_code = "INSUFFICIENT_STOCK"
    default_message = "Stock insuficiente"


class PaymentError(CommerceError):
    http_status = 402
    error_code = "PAYMENT_ERROR"
    default_message = "Error en el pago"


# ── Integration ───────────────────────────────────────
class IntegrationError(FluxError):
    http_status = 502
    error_code = "INTEGRATION_ERROR"
    default_message = "Error de integración externa"


class ChannelUnavailableError(IntegrationError):
    error_code = "CHANNEL_UNAVAILABLE"
    default_message = "Canal de mensajería no disponible"


class LLMError(IntegrationError):
    error_code = "LLM_ERROR"
    default_message = "Error en el modelo de lenguaje"


class WebhookValidationError(IntegrationError):
    http_status = 400
    error_code = "WEBHOOK_VALIDATION_FAILED"
    default_message = "Firma de webhook inválida"


# Mantiene compatibilidad con código que usaba SlotUnavailableError directamente
class SlotUnavailableError(BusinessRuleError):
    error_code = "SLOT_UNAVAILABLE"
    default_message = "Horario no disponible"
