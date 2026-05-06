from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum

class SalesStage(str, Enum):
    INTRO = "introduction"
    QUALIFICATION = "qualification"
    ANALYSIS = "needs_analysis"
    PRESENTATION = "presentation"
    OBJECTION = "handling_objections"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    FOLLOW_UP = "follow_up"

class ConversationState(BaseModel):
    session_id: str
    current_stage: SalesStage = SalesStage.INTRO
    customer_name: Optional[str] = None
    pain_points: List[str] = []
    objections: List[str] = []
    product_interest: Optional[str] = None
    sentiment_score: float = 0.5
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Historial resumido para contexto
    summary: str = ""

class StageAnalyzer:
    """Analiza el mensaje del usuario para detectar cambios de etapa"""
    
    KEYWORDS = {
        SalesStage.INTRO: ["hola", "buenos", "inicio", "empezar"],
        SalesStage.QUALIFICATION: ["necesito", "busco", "quiero", "tengo"],
        SalesStage.ANALYSIS: ["problema", "dolor", "difícil", "costoso"],
        SalesStage.PRESENTATION: ["muestra", "demo", "cómo funciona", "características"],
        SalesStage.OBJECTION: ["pero", "caro", "duda", "temo", "no estoy seguro"],
        SalesStage.NEGOTIATION: ["precio", "descuento", "oferta", "condición"],
        SalesStage.CLOSING: ["comprar", "pagar", "contratar", "listo", "finalizar"],
        SalesStage.FOLLOW_UP: ["después", "luego", "soporte", "garantía"]
    }

    @staticmethod
    def detect_stage(text: str, current: SalesStage) -> SalesStage:
        text_lower = text.lower()
        
        # Lógica simple de detección (se puede mejorar con LLM)
        for stage, keywords in StageAnalyzer.KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                # Evitar regresiones drásticas, permitir avance o lateralidad
                if stage == SalesStage.CLOSING or stage == SalesStage.OBJECTION:
                    return stage
                if stage.value > current.value: 
                    return stage
        
        return current

    @staticmethod
    def get_system_prompt(stage: SalesStage) -> str:
        prompts = {
            SalesStage.INTRO: "Eres un vendedor amable. Saluda, preséntate y pregunta cómo puedes ayudar hoy.",
            SalesStage.QUALIFICATION: "Haz preguntas abiertas para entender qué necesita el cliente exactamente.",
            SalesStage.ANALYSIS: "Profundiza en sus problemas. Muestra empatía y confirma que entiendes su dolor.",
            SalesStage.PRESENTATION: "Presenta la solución conectando características con sus dolores específicos.",
            SalesStage.OBJECTION: "Escucha activamente. Valida su preocupación y ofrece evidencia o contra-argumentos suaves.",
            SalesStage.NEGOTIATION: "Busca un ganar-ganar. Ofrece opciones flexibles sin regalar valor innecesario.",
            SalesStage.CLOSING: "Guía hacia la acción final. Pregunta si está listo para proceder o generar el link de pago.",
            SalesStage.FOLLOW_UP: "Agradece, confirma los siguientes pasos y ofrece soporte continuo."
        }
        return prompts.get(stage, prompts[SalesStage.INTRO])
