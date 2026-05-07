# =============================================================================
# FLUXAGENT V2 — DOMAIN AGENTS PROMPTS
# =============================================================================
# Factory centralizado para generación de prompts de agentes
# Separación de lógica de negocio de infraestructura
# =============================================================================

from typing import Optional, Dict, Any, Tuple
from .schemas import AgentType

class AgentPromptFactory:
    """Factory centralizado para generación de prompts de agentes IA"""
    
    @staticmethod
    def create_system_prompt(
        agent_type: AgentType,
        personality: Optional[str] = None,
        instructions: Optional[str] = None,
        specialty: Optional[str] = None,
        script_ventas: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Genera prompt del sistema + script según tipo de agente
        
        Args:
            agent_type: Tipo de agente (sales, support, bookings, custom)
            personality: Personalidad del agente
            instructions: Instrucciones específicas
            specialty: Especialidad del agente
            script_ventas: Scripts de ventas (para agentes de ventas)
            **kwargs: Parámetros adicionales
            
        Returns:
            Tuple[str, Optional[Dict]]: (system_prompt, script_ventas)
        """
        
        if agent_type == AgentType.SALES:
            return AgentPromptFactory._create_sales_prompt(
                personality, instructions, specialty, script_ventas, **kwargs
            )
        elif agent_type == AgentType.SUPPORT:
            return AgentPromptFactory._create_support_prompt(
                personality, instructions, specialty, **kwargs
            )
        elif agent_type == AgentType.BOOKINGS:
            return AgentPromptFactory._create_bookings_prompt(
                personality, instructions, specialty, **kwargs
            )
        else:  # CUSTOM
            return AgentPromptFactory._create_custom_prompt(
                personality, instructions, specialty, **kwargs
            )
    
    @staticmethod
    def _create_sales_prompt(
        personality: Optional[str],
        instructions: Optional[str],
        specialty: Optional[str],
        script_ventas: Optional[Dict[str, Any]],
        **kwargs
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Crea prompt para agente de ventas"""
        
        # Usar lógica legacy existente
        try:
            from agents.sales_agent import generate_sales_prompt as legacy_generate
            
            # Construir datos para legacy
            agent_data = {
                "personalidad": personality,
                "instrucciones": instructions,
                "specialty": specialty,
                "script_ventas": script_ventas,
                **kwargs
            }
            
            return legacy_generate(agent_data)
            
        except ImportError:
            # Fallback si no existe legacy
            return AgentPromptFactory._fallback_sales_prompt(
                personality, instructions, specialty, script_ventas
            )
    
    @staticmethod
    def _create_support_prompt(
        personality: Optional[str],
        instructions: Optional[str],
        specialty: Optional[str],
        **kwargs
    ) -> Tuple[str, None]:
        """Crea prompt para agente de soporte"""
        
        base_prompt = "Eres un agente de soporte técnico profesional y amable."
        
        if specialty:
            base_prompt += f" Tu especialidad es: {specialty}."
        
        if personality:
            base_prompt += f" Tu personalidad: {personality}."
        
        if instructions:
            base_prompt += f" Instrucciones específicas: {instructions}"
        
        base_prompt += """

## TUS RESPONSABILIDADES:
- Ayudar a resolver problemas técnicos de manera clara y paciente
- Escuchar activamente las necesidades del cliente
- Ofrecer soluciones prácticas y efectivas
- Escalar problemas complejos cuando sea necesario
- Mantener un tono profesional y empático

## TU ENFOQUE:
1. Escuchar el problema con atención
2. Hacer preguntas claras para diagnosticar
3. Ofrecer soluciones paso a paso
4. Verificar que el problema esté resuelto
5. Documentar el caso para futuras referencias

## REGLAS IMPORTANTES:
- Nunca inventes soluciones técnicas
- Admite cuando no sabes algo y ofrece escalar
- Siempre confirma que el cliente entendió la solución
- Mantén la calma incluso con clientes frustrados
"""
        
        return base_prompt, None
    
    @staticmethod
    def _create_bookings_prompt(
        personality: Optional[str],
        instructions: Optional[str],
        specialty: Optional[str],
        **kwargs
    ) -> Tuple[str, None]:
        """Crea prompt para agente de reservas"""
        
        base_prompt = "Eres un agente de reservas eficiente y organizado."
        
        if specialty:
            base_prompt += f" Tu especialidad es: {specialty}."
        
        if personality:
            base_prompt += f" Tu personalidad: {personality}."
        
        if instructions:
            base_prompt += f" Instrucciones específicas: {instructions}"
        
        base_prompt += """

## TUS RESPONSABILIDADES:
- Gestionar reservas de manera eficiente
- Verificar disponibilidad en tiempo real
- Confirmar detalles de reservación
- Manejar cambios y cancelaciones
- Enviar recordatorios y confirmaciones

## TU ENFOQUE:
1. Verificar disponibilidad solicitada
2. Presentar opciones disponibles
3. Confirmar detalles del cliente
4. Procesar la reservación
5. Enviar confirmación clara

## REGLAS IMPORTANTES:
- Siempre verifica disponibilidad antes de prometer
- Confirma todos los detalles importantes
- Explica claramente políticas de cancelación
- Maneja cambios con flexibilidad cuando sea posible
"""
        
        return base_prompt, None
    
    @staticmethod
    def _create_custom_prompt(
        personality: Optional[str],
        instructions: Optional[str],
        specialty: Optional[str],
        **kwargs
    ) -> Tuple[str, None]:
        """Crea prompt para agente personalizado"""
        
        base_prompt = f"Eres un asistente especializado."
        
        if specialty:
            base_prompt += f" Tu especialidad es: {specialty}."
        
        if personality:
            base_prompt += f" Tu personalidad: {personality}."
        
        if instructions:
            base_prompt += f" Instrucciones: {instructions}"
        
        base_prompt += """

## TUS RESPONSABILIDADES:
- Proporcionar asistencia según tu especialidad
- Mantener un tono profesional y servicial
- Adaptarte a las necesidades del cliente
- Buscar la mejor solución para cada caso

## TU ENFOQUE:
1. Escuchar atentamente la solicitud
2. Analizar la mejor manera de ayudar
3. Proporcionar una respuesta clara y útil
4. Verificar que el cliente quede satisfecho
"""
        
        return base_prompt, None
    
    @staticmethod
    def _fallback_sales_prompt(
        personality: Optional[str],
        instructions: Optional[str],
        specialty: Optional[str],
        script_ventas: Optional[Dict[str, Any]]
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Prompt fallback para ventas si legacy no disponible"""
        
        base_prompt = "Eres un agente de ventas profesional y persuasivo."
        
        if specialty:
            base_prompt += f" Tu especialidad es: {specialty}."
        
        if personality:
            base_prompt += f" Tu personalidad: {personality}."
        
        if instructions:
            base_prompt += f" Instrucciones: {instructions}"
        
        base_prompt += """

## TUS RESPONSABILIDADES:
- Identificar necesidades del cliente
- Presentar soluciones adecuadas
- Guiar hacia una decisión de compra
- Manejar objeciones de manera profesional
- Cerrar ventas efectivamente

## TU ENFOQUE:
1. Descubrir necesidades del cliente
2. Presentar beneficios relevantes
3. Manejar dudas y objeciones
4. Facilitar el proceso de compra
5. Asegurar satisfacción post-venta

## REGLAS IMPORTANTES:
- Nunca presiones al cliente
- Enfócate en beneficios, no características
- Escucha activamente las necesidades
- Sé honesto sobre limitaciones
"""
        
        # Script básico si no se proporciona
        default_script = {
            "fases": [
                {"nombre": "descubrimiento", "objetivo": "Identificar necesidades"},
                {"nombre": "presentacion", "objetivo": "Mostrar soluciones"},
                {"nombre": "cierre", "objetivo": "Facilitar decisión"}
            ],
            "reglas": [
                "Escuchar antes de hablar",
                "Enfocarse en beneficios",
                "Manejar objeciones con empatía"
            ],
            "scripts": [
                "¿Qué estás buscando exactamente?",
                "Basado en lo que me dices, te recomiendo...",
                "¿Te gustaría proceder con la compra?"
            ],
            "escalacion": {
                "enabled": True,
                "keywords": ["gerente", "supervisor", "no puedo"]
            }
        }
        
        return base_prompt, script_ventas or default_script

class PromptTemplate:
    """Templates reutilizables para prompts"""
    
    @staticmethod
    def get_base_template(agent_type: AgentType) -> str:
        """Obtiene template base para tipo de agente"""
        templates = {
            AgentType.SALES: "Eres un agente de ventas profesional.",
            AgentType.SUPPORT: "Eres un agente de soporte técnico.",
            AgentType.BOOKINGS: "Eres un agente de reservas.",
            AgentType.CUSTOM: "Eres un asistente especializado."
        }
        return templates.get(agent_type, "Eres un asistente profesional.")
    
    @staticmethod
    def get_responsibilities(agent_type: AgentType) -> str:
        """Obtiene responsabilidades por tipo"""
        responsibilities = {
            AgentType.SALES: "Identificar necesidades, presentar soluciones, cerrar ventas.",
            AgentType.SUPPORT: "Resolver problemas técnicos, escalar cuando sea necesario.",
            AgentType.BOOKINGS: "Gestionar reservas, verificar disponibilidad, confirmar detalles.",
            AgentType.CUSTOM: "Proporcionar asistencia especializada según necesidad."
        }
        return responsibilities.get(agent_type, "Proporcionar asistencia profesional.")
