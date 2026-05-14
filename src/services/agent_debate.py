"""
CAMEL Agent Debate Layer (Sprint D.1 - Fortress Path v2.7)
==========================================================
Implementa el patrón "Role-Playing" de CAMEL-AI para resolver
excepciones y decisiones complejas que el SOP rígido no cubre.

Arquitectura:
  Initiator Agent  <---debate--->  Critic Agent
        |                              |
        +---------> Consensus <--------+
                        |
                   Final Decision

Los agentes se comunican internamente vía Ollama (privado).
El resultado del debate es auditado y trazado via CanonicalEnvelope.
"""
import asyncio
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class DebateVerdict(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ESCALATE = "escalate"
    NEEDS_MORE_INFO = "needs_more_info"


@dataclass
class DebateMessage:
    """Un turno en el diálogo entre agentes."""
    turn: int
    role: str          # "initiator" | "critic" | "moderator"
    content: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class DebateResult:
    """Resultado completo de un debate agentic."""
    debate_id: str
    topic: str
    verdict: DebateVerdict
    confidence: float       # 0.0 - 1.0
    reasoning: str
    messages: List[DebateMessage]
    duration_ms: int
    consensus_reached: bool

    def to_audit_dict(self) -> Dict[str, Any]:
        return {
            "debate_id": self.debate_id,
            "topic": self.topic,
            "verdict": self.verdict.value,
            "confidence": self.confidence,
            "consensus_reached": self.consensus_reached,
            "turns": len(self.messages),
            "duration_ms": self.duration_ms,
        }


class OllamaDebateClient:
    """
    Cliente liviano para comunicarse con Ollama en el loop de debate.
    Usa el endpoint local directamente sin dependencias externas.
    """
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model

    async def chat(self, system_prompt: str, user_message: str) -> str:
        """Llama al modelo Ollama local y retorna la respuesta."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "stream": False,
                }
                resp = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                resp.raise_for_status()
                return resp.json()["message"]["content"]
        except Exception as e:
            logger.error(f"[OllamaDebateClient] Error: {e}")
            # Fallback mock para modo de pruebas sin Ollama activo
            return f"[MOCK RESPONSE] Análisis del agente para: {user_message[:80]}..."


class AgentDebater:
    """
    Un agente participante en el debate.
    Tiene un rol específico y perspectiva definida.
    """
    def __init__(self, role: str, persona: str, ollama: OllamaDebateClient):
        self.role = role
        self.persona = persona
        self.ollama = ollama
        self.system_prompt = f"""Eres un especialista con el rol de {role}.
{persona}

REGLAS DEL DEBATE:
- Analiza la situación desde tu perspectiva de especialista.
- Sé directo y fundamenta tu posición con hechos.
- Si el otro agente tiene razón, concede el punto con evidencia.
- Siempre concluye con una recomendación clara: APROBAR / RECHAZAR / ESCALAR.
- Mantén el foco en el impacto para el negocio y el cliente.
"""

    async def respond(self, topic: str, previous_argument: Optional[str] = None) -> str:
        if previous_argument:
            message = f"Tema en debate: {topic}\n\nArgumento previo del otro especialista:\n{previous_argument}\n\n¿Cuál es tu análisis y posición?"
        else:
            message = f"Analiza esta situación desde tu perspectiva de especialista:\n\n{topic}"

        return await self.ollama.chat(self.system_prompt, message)


class AgentDebateOrchestrator:
    """
    Orquestador del debate entre agentes (CAMEL Pattern).
    Gestiona el loop de diálogo y detecta consenso.
    """

    MAX_TURNS = 4  # Límite de turnos para evitar loops infinitos

    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama = OllamaDebateClient(base_url=ollama_url, model=model)

    def _build_agents_for_scenario(self, scenario_type: str) -> tuple[AgentDebater, AgentDebater]:
        """Selecciona los agentes especialistas según el escenario."""
        agents_map = {
            "order_validation": (
                AgentDebater(
                    role="Sales Specialist",
                    persona="Eres el especialista de ventas. Tu prioridad es cerrar la venta y satisfacer al cliente, pero siempre dentro de las reglas de negocio.",
                    ollama=self.ollama,
                ),
                AgentDebater(
                    role="Risk & Compliance Officer",
                    persona="Eres el oficial de cumplimiento. Tu prioridad es proteger al negocio de fraudes, errores de stock y violaciones de políticas.",
                    ollama=self.ollama,
                ),
            ),
            "identity_conflict": (
                AgentDebater(
                    role="Customer Success Manager",
                    persona="Tu prioridad es mantener una experiencia de cliente positiva y resolver duplicados con empatía.",
                    ollama=self.ollama,
                ),
                AgentDebater(
                    role="Data Integrity Specialist",
                    persona="Tu prioridad es la integridad de los datos. Los perfiles duplicados son un riesgo operativo serio.",
                    ollama=self.ollama,
                ),
            ),
            "payment_exception": (
                AgentDebater(
                    role="Finance Analyst",
                    persona="Analizas el impacto financiero de las decisiones. Eres conservador con el riesgo.",
                    ollama=self.ollama,
                ),
                AgentDebater(
                    role="Operations Manager",
                    persona="Priorizas la continuidad operativa y la velocidad de resolución para el cliente.",
                    ollama=self.ollama,
                ),
            ),
        }
        return agents_map.get(
            scenario_type,
            agents_map["order_validation"]  # Fallback
        )

    async def run_debate(
        self,
        topic: str,
        context: Dict[str, Any],
        scenario_type: str = "order_validation",
    ) -> DebateResult:
        """
        Ejecuta el loop de debate entre dos agentes especialistas.
        """
        debate_id = str(uuid4())
        start_time = time.time()
        messages: List[DebateMessage] = []

        logger.info(f"[Debate] Iniciando debate {debate_id} sobre: {topic[:80]}")

        initiator, critic = self._build_agents_for_scenario(scenario_type)

        # Enriquecer el tópico con contexto de negocio
        full_topic = f"{topic}\n\nContexto del negocio:\n" + "\n".join(
            f"- {k}: {v}" for k, v in context.items()
        )

        # === TURNO 1: Initiator abre el debate ===
        init_response = await initiator.respond(full_topic)
        messages.append(DebateMessage(turn=1, role=initiator.role, content=init_response))
        logger.info(f"[Debate] Turno 1 ({initiator.role}): {init_response[:100]}...")

        # === TURNO 2: Critic responde ===
        critic_response = await critic.respond(full_topic, previous_argument=init_response)
        messages.append(DebateMessage(turn=2, role=critic.role, content=critic_response))
        logger.info(f"[Debate] Turno 2 ({critic.role}): {critic_response[:100]}...")

        # === TURNO 3: Initiator replica ===
        final_init = await initiator.respond(full_topic, previous_argument=critic_response)
        messages.append(DebateMessage(turn=3, role=initiator.role, content=final_init))

        # === TURNO 4: Síntesis del Moderador (Ollama) ===
        moderator_prompt = """Eres el Moderador final de este debate entre especialistas.
Tu trabajo es sintetizar los argumentos y emitir una decisión final clara.

INSTRUCCIONES:
1. Resume los argumentos clave de ambos lados.
2. Emite un veredicto: APROBAR / RECHAZAR / ESCALAR / NECESITA_MAS_INFO
3. Asigna un porcentaje de confianza (0-100%) en tu decisión.
4. Justifica brevemente tu veredicto.

Responde en formato JSON exactamente así:
{
  "verdict": "APPROVE|REJECT|ESCALATE|NEEDS_MORE_INFO",
  "confidence": 85,
  "reasoning": "Explicación breve...",
  "consensus_reached": true
}"""

        debate_transcript = "\n\n".join(
            f"[{m.role}]: {m.content}" for m in messages
        )
        moderator_msg = f"Transcripción del debate:\n\n{debate_transcript}\n\nEmite tu veredicto:"
        moderator_response = await self.ollama.chat(moderator_prompt, moderator_msg)
        messages.append(DebateMessage(turn=4, role="Moderator", content=moderator_response))

        # Parsear veredicto del moderador
        verdict, confidence, reasoning, consensus = self._parse_verdict(moderator_response)

        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(f"[Debate] Finalizado en {duration_ms}ms. Veredicto: {verdict.value} ({confidence:.0%})")

        return DebateResult(
            debate_id=debate_id,
            topic=topic,
            verdict=verdict,
            confidence=confidence,
            reasoning=reasoning,
            messages=messages,
            duration_ms=duration_ms,
            consensus_reached=consensus,
        )

    def _parse_verdict(self, moderator_response: str) -> tuple:
        """Parsea el JSON de veredicto del moderador con tolerancia a errores."""
        import json, re

        # Extraer bloque JSON de la respuesta
        json_match = re.search(r'\{.*?\}', moderator_response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                verdict_str = data.get("verdict", "ESCALATE").upper()
                verdict_map = {
                    "APPROVE": DebateVerdict.APPROVE,
                    "REJECT": DebateVerdict.REJECT,
                    "ESCALATE": DebateVerdict.ESCALATE,
                    "NEEDS_MORE_INFO": DebateVerdict.NEEDS_MORE_INFO,
                }
                return (
                    verdict_map.get(verdict_str, DebateVerdict.ESCALATE),
                    data.get("confidence", 70) / 100,
                    data.get("reasoning", "Sin razonamiento provisto."),
                    data.get("consensus_reached", False),
                )
            except json.JSONDecodeError:
                pass

        # Fallback si el modelo no genera JSON correcto
        response_lower = moderator_response.lower()
        if "apro" in response_lower or "approve" in response_lower:
            return DebateVerdict.APPROVE, 0.70, "Consenso implícito de aprobación.", False
        elif "rechaz" in response_lower or "reject" in response_lower:
            return DebateVerdict.REJECT, 0.70, "Consenso implícito de rechazo.", False
        else:
            return DebateVerdict.ESCALATE, 0.50, "Sin consenso claro. Escalando a humano.", False
