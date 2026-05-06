from typing import List, Dict, Any
import os

from .conversation_state import ConversationState, SalesStage, StageAnalyzer
# from .tools.sales_tools import SALES_TOOLS

class SalesAgent:
    def __init__(self, session_id: str, is_premium: bool = False):
        self.session_id = session_id
        self.is_premium = is_premium
        
        # Model
        self.llm = None
        
        # State
        self.state = ConversationState(session_id=session_id)
        
        # Memory
        self.memory = None
        
        # Agent
        self.agent = None
        self.executor = None

    def _get_system_prompt(self) -> str:
        base_prompt = StageAnalyzer.get_system_prompt(self.state.current_stage)
        premium_instruction = ""
        
        if self.is_premium:
            premium_instruction = "\n[MODULO PREMIUM ACTIVADO]: Tienes acceso a análisis de sentimiento avanzado, generación de voz neural y priorización de respuestas."
            
        return f"""
        Eres un experto en ventas especializado en e-commerce.
        Etapa actual: {self.state.current_stage.value}
        Instrucción específica: {base_prompt}
        {premium_instruction}
        
        Si detectas un cambio de intención en el usuario, adapta tu respuesta pero mantén el objetivo de venta.
        Extrae nombres y datos clave silenciosamente.
        """

    async def chat(self, user_message: str) -> Dict[str, Any]:
        # 1. Analizar etapa
        new_stage = StageAnalyzer.detect_stage(user_message, self.state.current_stage)
        if new_stage != self.state.current_stage:
            self.state.current_stage = new_stage
            # Actualizar prompt dinámico si cambia etapa (requiere reiniciar agente en LangChain clásico o usar PromptTemplate dinámico)
            # Para simplificar, actualizamos el system message en memoria si fuera necesario
            
        # 2. Mock Agent
        try:
            output_text = f"Mock response for: {user_message}"
            
            # 3. Extraer datos (simulado, se puede mejorar con OutputParser)
            if "me llamo" in user_message.lower():
                self.state.customer_name = user_message.split("me llamo")[-1].strip()
                
            return {
                "response": output_text,
                "stage": self.state.current_stage.value,
                "session_id": self.session_id,
                "is_premium": self.is_premium
            }
        except Exception as e:
            return {
                "response": "Lo siento, tuve un error procesando tu solicitud. ¿Podemos intentar de nuevo?",
                "error": str(e),
                "stage": self.state.current_stage.value
            }
