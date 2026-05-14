from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import hashlib
import json

class ToolIntent(BaseModel):
    """
    Representa la intención de ejecutar una herramienta extraída por el LLM.
    El LLM NUNCA ejecuta herramientas directamente; solo produce un Intent.
    """
    tool: str = Field(..., description="Nombre de la herramienta solicitada")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza del LLM en la extracción (0.0 a 1.0)")
    extracted_parameters: Dict[str, Any] = Field(default_factory=dict, description="Parámetros extraídos del contexto")
    source_prompt_hash: str = Field(..., description="Hash SHA-256 del prompt que generó este intent (para trazabilidad)")
    reasoning: str = Field(..., description="Cadena de pensamiento (CoT) del LLM justificando esta extracción")
    
    def calculate_intent_hash(self) -> str:
        """Calcula un hash único para el contenido de la intención."""
        payload = {
            "tool": self.tool,
            "params": self.extracted_parameters
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
