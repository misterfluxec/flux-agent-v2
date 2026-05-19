from __future__ import annotations
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from auth import get_usuario_actual, PayloadToken
from core.exceptions import LLMError

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/yanua", tags=["ai-reasoning"])


class ReasoningRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)
    context_scope: str = Field(
        default="general",
        pattern="^(general|commerce|operations|analytics)$",
    )
    max_tokens: int = Field(default=800, ge=50, le=2000)


@router.post("/reason")
@limiter.limit("10/minute")
async def reasoning_endpoint(
    request: Request,
    payload: ReasoningRequest,
    usuario: PayloadToken = Depends(get_usuario_actual),
):
    """
    Razonamiento profundo bajo demanda — Yanua AI.
    Llama directamente al LLM con contexto de negocio.
    Límite: 10 requests/minuto por IP.
    """
    orchestrator = request.app.state.orchestrator
    llm_provider = orchestrator.llm_provider
    tenant_id = str(usuario.tenant_id)

    scope_prompts = {
        "general": (
            "Eres Yanua, el asistente de inteligencia "
            "operacional de FluxAgent. Responde con "
            "análisis claro, conciso y accionable."
        ),
        "commerce": (
            "Eres Yanua, especialista en operaciones "
            "comerciales LATAM. Analiza ventas, inventario "
            "y comportamiento de clientes."
        ),
        "operations": (
            "Eres Yanua, monitor operacional. Analiza "
            "flujos de trabajo, agentes y métricas "
            "de respuesta del sistema."
        ),
        "analytics": (
            "Eres Yanua, analista de datos. Interpreta "
            "métricas, identifica anomalías y propone "
            "acciones basadas en evidencia."
        ),
    }

    system_prompt = scope_prompts.get(
        payload.context_scope, scope_prompts["general"]
    )

    try:
        raw = await llm_provider.generate(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": payload.query},
            ],
            temperature=0.4,
            max_tokens=payload.max_tokens,
        )
    except Exception as exc:
        raise LLMError(
            f"Yanua no pudo procesar la consulta: {exc}"
        )

    content = (
        raw.get("content", "") if isinstance(raw, dict)
        else str(raw)
    )

    if not content:
        raise LLMError("Yanua no generó respuesta.")

    return {
        "status": "completed",
        "query": payload.query,
        "context_scope": payload.context_scope,
        "response": content,
        "tenant_id": tenant_id,
        "model": getattr(llm_provider, "model", "ollama"),
    }


@router.get("/health")
async def yanua_health(
    request: Request,
    usuario: PayloadToken = Depends(get_usuario_actual),
):
    """Verifica disponibilidad del LLM para Yanua."""
    orchestrator = request.app.state.orchestrator
    llm_provider = orchestrator.llm_provider
    try:
        raw = await llm_provider.generate(
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
            temperature=0.0,
        )
        return {"status": "available", "model": getattr(
            llm_provider, "model", "unknown"
        )}
    except Exception as exc:
        return {"status": "unavailable", "error": str(exc)}
