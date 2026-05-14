import uuid
from contextvars import ContextVar
from typing import Optional

# Distributed tracing context
correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
tenant_id: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)
workflow_run_id: ContextVar[Optional[str]] = ContextVar("workflow_run_id", default=None)
actor_id: ContextVar[Optional[str]] = ContextVar("actor_id", default=None)
request_origin: ContextVar[Optional[str]] = ContextVar("request_origin", default=None)

# LATAM Enterprise Execution Context
country_code: ContextVar[Optional[str]] = ContextVar("country_code", default=None)
currency: ContextVar[Optional[str]] = ContextVar("currency", default=None)
timezone: ContextVar[Optional[str]] = ContextVar("timezone", default=None)

def set_correlation_id(cid: Optional[str] = None) -> str:
    token = cid or str(uuid.uuid4())
    correlation_id.set(token)
    return token

def get_observability_context() -> dict:
    """Returns the current distributed tracing and enterprise context."""
    return {
        "correlation_id": correlation_id.get(),
        "tenant_id": tenant_id.get(),
        "workflow_run_id": workflow_run_id.get(),
        "actor_id": actor_id.get(),
        "request_origin": request_origin.get(),
        "country_code": country_code.get(),
        "currency": currency.get(),
        "timezone": timezone.get()
    }

def bind_context(data: dict):
    """Binds incoming metadata to the current context."""
    if "correlation_id" in data: correlation_id.set(data["correlation_id"])
    if "tenant_id" in data: tenant_id.set(data["tenant_id"])
    if "workflow_run_id" in data: workflow_run_id.set(data["workflow_run_id"])
    if "actor_id" in data: actor_id.set(data["actor_id"])
    if "request_origin" in data: request_origin.set(data["request_origin"])
    if "country_code" in data: country_code.set(data["country_code"])
    if "currency" in data: currency.set(data["currency"])
    if "timezone" in data: timezone.set(data["timezone"])
