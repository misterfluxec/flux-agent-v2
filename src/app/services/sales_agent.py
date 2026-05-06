from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from typing import List, Dict, Any
import os

from .conversation_state import ConversationState, SalesStage, StageAnalyzer
from .tools.sales_tools import SALES_TOOLS

class SalesAgent:
    def __init__(self, session_id: str, is_premium: bool = False):
        self.session_id = session_id
        self.is_premium = is_premium
        
        # Configuración del Modelo
        model_name = "gpt-4o" if is_premium else "gpt-3.5-turbo" # O modelo local si es open source puro
        self.llm = ChatOpenAI(model=model_name, temperature=0.7)
        
        # Estado inicial
        self.state = ConversationState(session_id=session_id)
        
        # Memoria
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", 
            return_messages=True
        )
        
        # Agente
        self.agent = create_openai_functions_agent(self.llm, SALES_TOOLS, self._get_system_prompt())
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=SALES_TOOLS,
            memory=self.memory,
            verbose=True
        )

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
            
        # 2. Ejecutar agente
        try:
            response = await self.executor.ainvoke({"input": user_message})
            output_text = response["output"]
            
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
