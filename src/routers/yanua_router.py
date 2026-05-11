from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
# from core.rate_limit import limiter (Omitido para la Beta hasta estabilizar rate_limit)

router = APIRouter(prefix="/yanua", tags=["ai-reasoning"])

class ReasoningRequest(BaseModel):
    query: str
    context_scope: str = "general"

@router.post("/reason")
async def reasoning_endpoint(request: Request, payload: ReasoningRequest):
    """Capa LLM on-demand. NO se usa en UI pasiva. Solo bajo demanda explícita."""
    return {
        "status": "queued_for_reasoning",
        "message": "Yanua está procesando tu consulta compleja. Recibirás el análisis en breve.",
        "estimated_ms": 1500
    }
