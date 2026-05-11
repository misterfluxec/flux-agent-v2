import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any
import json

from services.ai_copilot.context_engine import ContextEngine
from services.ai_copilot.bounded_prompt_engine import BoundedPromptEngine

logger = logging.getLogger(__name__)

class IncidentExplainer:
    """
    Fase 4C — Sprint 4C.1: Incident Explainer.
    
    Orquesta el flujo: 
    Memory → ContextEngine → SafetyGuardrails → BoundedPromptEngine → AuditLog
    """

    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def explain(self, correlation_id: str) -> Dict[str, Any]:
        """
        Genera una explicación auditable de un incidente y la registra en BDD.
        """
        # 1. Obtener contexto seguro
        context_engine = ContextEngine(self.db, self.tenant_id)
        safe_context = await context_engine.build_incident_context(correlation_id)

        # 2. Generar explicación acotada
        llm_response = BoundedPromptEngine.explain_incident(safe_context)

        # 3. Registrar en Audit Trail (OBLIGATORIO)
        await self._audit_log_response(
            correlation_id=correlation_id,
            safe_context=safe_context,
            llm_response=llm_response
        )

        return llm_response

    async def generate_tenant_insight(self) -> Dict[str, Any]:
        """
        Genera un insight a nivel negocio y lo registra.
        """
        context_engine = ContextEngine(self.db, self.tenant_id)
        safe_context = await context_engine.build_tenant_context()

        llm_response = BoundedPromptEngine.generate_tenant_insight(safe_context)

        await self._audit_log_response(
            correlation_id=None,
            safe_context=safe_context,
            llm_response=llm_response
        )

        return llm_response

    async def _audit_log_response(self, correlation_id: str | None, safe_context: Dict[str, Any], llm_response: Dict[str, Any]):
        """Escribe en ai_response_audit_log para trazabilidad Enterprise."""
        q = text("""
            INSERT INTO ai_response_audit_log (
                tenant_id, correlation_id, prompt_version, context_version,
                sources_used, confidence, generated_response, model_used,
                token_count, latency_ms, context_hash, derived_chain_hash
            ) VALUES (
                :t, :cid, :pv, :cv, :sources, :conf, :resp, :model, :tokens, :lat, :chash, :dhash
            )
        """)
        
        try:
            await self.db.execute(q, {
                "t": self.tenant_id,
                "cid": correlation_id,
                "pv": llm_response.get("prompt_version", "unknown"),
                "cv": safe_context.get("context_version", "unknown"),
                "sources": json.dumps(llm_response.get("sources", [])),
                "conf": llm_response.get("confidence", 0.0),
                "resp": llm_response.get("response", ""),
                "model": "simulated_gpt_4o_mini", # Placeholder
                "tokens": 450, # Placeholder
                "lat": 1200, # Placeholder
                "chash": llm_response.get("context_hash"),
                "dhash": llm_response.get("derived_chain_hash")
            })
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.warning(f"Error escribiendo audit log (ai_response_audit_log might not exist): {e}")
