import logging
import json
from typing import Dict, Any

from services.ai_copilot.safety_guardrails import SafetyGuardrails

logger = logging.getLogger(__name__)

class BoundedPromptEngine:
    """
    Fase 4C — Sprint 4C.1: Bounded Prompt Engine.
    
    Asegura que las interacciones con el LLM estén rígidamente formateadas,
    versionadas y limitadas. 
    Aplica la Recommendation Classification Layer.
    """

    # Registro de versiones de prompts (Inmutables en código)
    PROMPTS = {
        "tenant_summary_v1.0": """
You are the FluxAgent AI Copilot (Operational Commerce OS).
Analyze the following operational context and provide a brief executive summary and recommendation.

RULES:
1. DO NOT invent data. Use ONLY the provided context.
2. DO NOT suggest autonomous actions.
3. Classify your recommendation into one of these types: INFORMATIVE, ACTIONABLE, ESCALATION, RISK, OPTIMIZATION.
4. Output STRICTLY in the requested JSON format.

CONTEXT:
{context_json}

OUTPUT FORMAT:
{
  "response": "Your executive summary here...",
  "recommendation_type": "INFORMATIVE"
}
        """,
        "incident_explainer_v1.0": """
You are the FluxAgent AI Copilot.
Explain the following incident timeline to a support agent.

RULES:
1. Explain what happened chronologically.
2. If there are failures, explain the probable operational impact based on the events.
3. DO NOT invent events.
4. Classify your recommendation type (INFORMATIVE, ACTIONABLE, ESCALATION, RISK, OPTIMIZATION).
5. Output STRICTLY in JSON format.

CONTEXT:
{context_json}

OUTPUT FORMAT:
{
  "response": "Timeline explanation here...",
  "recommendation_type": "INFORMATIVE"
}
        """
    }

    @staticmethod
    def generate_tenant_insight(safe_context: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un insight operacional a nivel tenant."""
        if not safe_context.get("safe_to_process"):
            return BoundedPromptEngine._fallback_response(safe_context, "Context validation failed.")

        prompt_id = "tenant_summary_v1.0"
        prompt_template = BoundedPromptEngine.PROMPTS[prompt_id]
        
        # 1. Format Prompt
        # final_prompt = prompt_template.replace("{context_json}", json.dumps(safe_context))
        
        # 2. LLM Call (Simulada para MVP)
        # Aquí iría la llamada real a OpenAI/Gemini
        simulated_llm_output = {
            "response": "El análisis de memoria indica una tasa de fallos de pago anómala, coincidente con un drift de inventario. Se recomienda revisar el gateway de pagos y forzar una conciliación.",
            "recommendation_type": "ACTIONABLE"
        }

        # 3. Empaquetar y Validar Respuesta
        return BoundedPromptEngine._package_response(simulated_llm_output, safe_context, prompt_id)

    @staticmethod
    def explain_incident(safe_context: Dict[str, Any]) -> Dict[str, Any]:
        """Genera la explicación de un incidente específico."""
        if not safe_context.get("safe_to_process"):
            return BoundedPromptEngine._fallback_response(safe_context, "Incident context validation failed.")

        prompt_id = "incident_explainer_v1.0"
        
        # LLM Call (Simulada)
        simulated_llm_output = {
            "response": "El pago falló inicialmente por timeout (TRANSIENT). El sistema ejecutó 3 retries. La reconciliación fue exitosa en el último intento. No se detectó pérdida de inventario.",
            "recommendation_type": "INFORMATIVE"
        }

        return BoundedPromptEngine._package_response(simulated_llm_output, safe_context, prompt_id)

    @staticmethod
    def _package_response(llm_output: Dict[str, Any], context: Dict[str, Any], prompt_id: str) -> Dict[str, Any]:
        """Aplica la firma obligatoria a todas las respuestas del LLM."""
        
        raw_response = {
            "response": llm_output.get("response", "No response generated."),
            "recommendation_type": llm_output.get("recommendation_type", "INFORMATIVE"),
            "confidence": context.get("context_confidence", 0.0),
            "confidence_breakdown": context.get("confidence_breakdown", {}),
            "sources": context.get("sources_used", []),
            "prompt_version": prompt_id,
            "context_hash": context.get("context_hash", "unknown"),
            "derived_chain_hash": context.get("derived_chain_hash", "unknown"),
            "read_only": context.get("read_only", True)
        }

        # Última capa de seguridad antes de devolver
        return SafetyGuardrails.validate_llm_response(raw_response)

    @staticmethod
    def _fallback_response(context: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        return {
            "response": f"System limitation: {error_msg} {context.get('error', '')}",
            "recommendation_type": "INFORMATIVE",
            "confidence": 0.0,
            "confidence_breakdown": {"error": 1.0},
            "sources": [],
            "prompt_version": "fallback_v1",
            "context_hash": "error",
            "derived_chain_hash": "error",
            "read_only": True
        }
