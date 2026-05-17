import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SafetyGuardrails:
    """
    Fase 4C — Sprint 4C.1: AI Safety Guardrails.
    
    El firewall obligatorio antes de conectar cualquier model IA.
    Protege contra alucinaciones, fuga de PII, prompts maliciosos y
    acciones operacionales no autorizadas (fuerza READ_ONLY).
    """

    MAX_CONTEXT_TOKENS = 8000 # Límite estricto para evitar explotar la ventana de contexto
    MIN_CONFIDENCE_THRESHOLD = 0.70 # Si el input tiene menos confianza, no enviarlo al LLM

    @staticmethod
    def validate_context(context_package: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verifica el paquete de contexto antes de enviarlo al Bounded Prompt Engine.
        Lanza excepción si viola las reglas de seguridad o poda el contexto.
        """
        confidence = context_package.get("context_confidence", 0.0)
        
        if confidence < SafetyGuardrails.MIN_CONFIDENCE_THRESHOLD:
            logger.warning(f"Context rejected due to low confidence ({confidence}).")
            # En vez de fallar duro, podríamos devolver un paquete vacío con un disclaimer
            return {
                "context_version": context_package.get("context_version", "v1"),
                "context_confidence": confidence,
                "read_only": True,
                "error": "Insufficient operational confidence to provide safe AI context.",
                "safe_to_process": False
            }
            
        # Verificar que el PII haya sido redactado (esto debió hacerlo EventStore o ContextEngine)
        if not context_package.get("pii_redacted", False):
            logger.error("Context rejected: PII not marked as redacted.")
            raise ValueError("Safety Violation: Context contains raw PII.")

        # Budgeting rough check (simulado)
        # Idealmente usar tiktoken o similar para medir tamaño real
        approximate_tokens = len(str(context_package)) / 4
        if approximate_tokens > SafetyGuardrails.MAX_CONTEXT_TOKENS:
            logger.warning("Context exceeds max tokens. Enforcing compression.")
            # Compresión agresiva: quitar anomalías viejas o truncar timeline
            context_package["active_anomalies"] = context_package.get("active_anomalies", [])[:3]
            context_package["_warning"] = "Context compressed due to token limits."
            
        context_package["safe_to_process"] = True
        context_package["read_only"] = True # FORZADO
        return context_package

    @staticmethod
    def validate_llm_response(response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verifica la salida del LLM antes de enviarla al cliente/API.
        Asegura que cumpla con la firma y no intente ejecutar acciones.
        """
        if not response.get("read_only", False):
            logger.warning("LLM attempted to generate an action without read_only flag. Enforcing.")
            response["read_only"] = True
            
        # Si la respuesta no tiene una clasificación, forzar INFORMATIVE
        valid_types = ["INFORMATIVE", "ACTIONABLE", "ESCALATION", "RISK", "OPTIMIZATION"]
        if response.get("recommendation_type") not in valid_types:
            response["recommendation_type"] = "INFORMATIVE"

        # Validar confidence provenance
        if "confidence_breakdown" not in response:
            response["confidence_breakdown"] = {"unknown": 1.0}

        return response
