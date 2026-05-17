# =============================================================================
# FLUXAGENT V2 — AGENTE DE VENTAS (LangGraph-style)
# =============================================================================
# Implementa el flujo de conversación como un grafo de nodos:
#
#   [Usuario] → [Nodo Recuperación RAG] → [Nodo Generación LLM] → [Respuesta]
#
# Cada nodo es una función pura y testeble de forma independiente.
# La arquitectura está preparada para migrar a LangGraph sin refactorizar.
# =============================================================================

import json
import logging
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from agents.base_agent import AgenteBase, ContextoAgente, MensajeChat, RespuestaAgente
from config import obtener_config
from services.ingestion import ServicioIngesta

logger = logging.getLogger(__name__)
config = obtener_config()

_servicio_ingesta = ServicioIngesta()


def _generar_secciones_script(cfg: dict) -> str:
    """Genera las secciones de Reglas, Fases y Scripts para el prompt."""
    script = cfg.get("sales_script", {})
    if not script or "reglas" not in script:
        script = cfg
    
    secciones = []
    
    # 1. Reglas de Oro
    reglas = [r for r in script.get("reglas", []) if r.get("enabled")]
    if reglas:
        seccion_reglas = "## TUS REGLAS DE ORO (ESTRICTAS):\n"
        for i, r in enumerate(reglas):
            seccion_reglas += f"{i+1}. {r['rule']}: {r['description']}\n"
        secciones.append(seccion_reglas)
    else:
        secciones.append("""## TUS REGLAS:
1. Responde SIEMPRE en español, en 2-4 oraciones concisas.
2. Usa SOLO la información de tu base de conocimiento. Si no sabes, dilo honestamente.
3. Detecta intención de compra y ofrece el siguiente paso concreto.
4. Nunca reveles que eres IA a menos que te pregunten directamente.
5. Si el cliente da sus datos de contacto, agradécele y confirma que un asesor lo contactará.""")

    # 2. Fases de Venta
    fases = [f for f in script.get("fases", []) if f.get("enabled")]
    if fases:
        seccion_fases = "## ESTRATEGIA DE VENTA (POR FASES):\n"
        seccion_fases += "Identifica en qué fase estás y actúa según el objective. Adapta las frases a tu tone.\n"
        for f in fases:
            seccion_fases += f"- [{f['name']}]: {f['objective']}. Sugerencia: {', '.join(f.get('keyPhrases', []))}\n"
        secciones.append(seccion_fases)
    
    # 3. Scripts Personalizados / Respuestas Rápidas
    scripts = [s for s in script.get("scripts", []) if s.get("enabled")]
    if scripts:
        seccion_scripts = "## RESPUESTAS PREDEFINIDAS (Úsalas como referencia):\n"
        for s in scripts:
            seccion_scripts += f"- SI {s['trigger']} -> ENTONCES: {s['content']}\n"
        secciones.append(seccion_scripts)
        
    # 4. Escalación
    escalacion = script.get("escalacion", {})
    if escalacion.get("enabled") and escalacion.get("keywords"):
        keywords = ", ".join(escalacion.get("keywords", []))
        mensaje_escalacion = escalacion.get("mensaje", "Entiendo, déjame transferirte con un asesor humano.")
        seccion_escalacion = f"## ESCALACIÓN (IMPORTANTE):\nSi el cliente menciona alguna de las siguientes palabras: [{keywords}], DEBES usar exactamente esta frase y no decir nada más: \"{mensaje_escalacion}\". Esto activará la transferencia a un humano."
        secciones.append(seccion_escalacion)
        
    return "\n\n".join(secciones)


# =============================================================================
# ESTADO DEL GRAFO (equivalente a State en LangGraph)
# =============================================================================

@dataclass
class EstadoConversacion:
    """
    Estado completo que se pasa entre nodos del grafo de conversación.
    Cada nodo lee el status, lo enriquece y lo pasa al siguiente.
    """
    contexto:         ContextoAgente
    chunks_rag:       list[dict] = field(default_factory=list)
    prompt_sistema:   str = ""
    respuesta_final:  Optional[str] = None
    tokens_usados:    int = 0
    modelo_usado:     str = ""


# =============================================================================
# NODOS DEL GRAFO
# =============================================================================

async def nodo_recuperacion(
    status:  EstadoConversacion,
    sesion:  AsyncSession,
) -> EstadoConversacion:
    """
    NODO 1: Recuperación semántica (RAG Retrieval).
    """
    ctx = status.contexto
    logger.info(
        f"[RAG] Buscando contexto | tenant={ctx.tenant_id} | "
        f"pregunta='{ctx.mensaje_usuario[:60]}...'"
    )

    try:
        chunks = await _servicio_ingesta.buscar(
            sesion=sesion,
            consulta=ctx.mensaje_usuario,
            tenant_id=ctx.tenant_id,
            agent_id=ctx.agent_id if ctx.agent_id else None,
            top_k=5,
        )
        status.chunks_rag = chunks
        logger.info(f"[RAG] {len(chunks)} chunks recuperados con similitud > 0.3")
    except Exception as exc:
        logger.warning(f"[RAG] Búsqueda vectorial falló, continuando sin contexto: {exc}")
        status.chunks_rag = []

    return status


async def nodo_generacion(
    status:  EstadoConversacion,
    stream:  bool = False,
) -> EstadoConversacion:
    """
    NODO 2: Generación de respuesta con LLM (Ollama).
    """
    ctx = status.contexto
    cfg = ctx.configuracion

    # Construir sección de contexto RAG para el prompt
    contexto_rag = ""
    if status.chunks_rag:
        partes = [f"[Ref {i+1}]: {c['contenido']}" for i, c in enumerate(status.chunks_rag)]
        contexto_rag = "\n\n## INFORMACIÓN DE TU BASE DE CONOCIMIENTO:\n" + "\n\n".join(partes)

    secciones_script = _generar_secciones_script(cfg)

    humor_desc = {
        "formal":      "extremadamente formal y corporativo",
        "profesional": "profesional pero cercano y empático",
        "amigable":    "muy amigable, cálido y accesible",
        "casual":      "casual, conversacional y directo",
        "humoristico": "con un toque de mood natural, pero siempre útil",
    }.get(cfg.get("mood", "profesional"), "profesional")

    prompt_sistema = f"""Eres {cfg.get('name', 'Asistente')}, asistente de ventas IA {cfg.get('gender', 'neutro')}.

## TU ESTILO:
Eres {humor_desc}. {cfg.get('personality', '')}

## TU EMPRESA:
{cfg.get('business_type', 'Empresa de servicios')}

## TUS INSTRUCCIONES:
{cfg.get('instructions', 'Ayuda al cliente a encontrar lo que necesita y guíalo hacia una compra.')}

{secciones_script}

{contexto_rag}"""

    status.prompt_sistema = prompt_sistema

    # Construir mensajes para Ollama
    mensajes_ollama = [{"role": "system", "content": prompt_sistema}]
    for msg in ctx.historial[-10:]:
        rol_map = {"usuario": "user", "asistente": "assistant", "sistema": "system"}
        mensajes_ollama.append({"role": rol_map.get(msg.role, "user"), "content": msg.contenido})
    mensajes_ollama.append({"role": "user", "content": ctx.mensaje_usuario})

    model = cfg.get("model", config.ollama_modelo_chat)
    temperature = float(cfg.get("temperature", 0.7))
    max_tokens = int(cfg.get("max_tokens", 512))

    logger.info(f"[LLM] Generando respuesta | model={model} | temp={temperature}")

    async with httpx.AsyncClient(
        base_url=config.ollama_base_url,
        timeout=httpx.Timeout(config.ollama_timeout),
    ) as cliente:
        respuesta = await cliente.post(
            "/api/chat",
            json={
                "model":   model,
                "messages": mensajes_ollama,
                "stream":   False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
        )
        respuesta.raise_for_status()
        datos = respuesta.json()

    status.respuesta_final = datos.get("message", {}).get("content", "")
    status.tokens_usados = (
        datos.get("prompt_eval_count", 0) + datos.get("eval_count", 0)
    )
    status.modelo_usado = datos.get("model", model)

    return status


async def nodo_generacion_stream(
    status: EstadoConversacion,
) -> AsyncGenerator[str, None]:
    """
    NODO 2 (Streaming): Versión SSE del nodo de generación.
    """
    ctx = status.contexto
    cfg = ctx.configuracion

    model = cfg.get("model", config.ollama_modelo_chat)
    temperature = float(cfg.get("temperature", 0.7))
    max_tokens = int(cfg.get("max_tokens", 512))

    prompt_sistema = status.prompt_sistema or "Eres un asistente de ventas profesional."

    mensajes_ollama = [{"role": "system", "content": prompt_sistema}]
    for msg in ctx.historial[-10:]:
        rol_map = {"usuario": "user", "asistente": "assistant", "sistema": "system"}
        mensajes_ollama.append({"role": rol_map.get(msg.role, "user"), "content": msg.contenido})
    mensajes_ollama.append({"role": "user", "content": ctx.mensaje_usuario})

    try:
        async with httpx.AsyncClient(
            base_url=config.ollama_base_url,
            timeout=httpx.Timeout(config.ollama_timeout),
        ) as cliente:
            async with cliente.stream(
                "POST",
                "/api/chat",
                json={
                    "model":    model,
                    "messages": mensajes_ollama,
                    "stream":   True,
                    "options":  {"temperature": temperature, "num_predict": max_tokens},
                },
            ) as resp:
                resp.raise_for_status()
                async for linea in resp.aiter_lines():
                    if not linea.strip():
                        continue
                    try:
                        datos = json.loads(linea)
                        token = datos.get("message", {}).get("content", "")
                        if token:
                            yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
                        if datos.get("done"):
                            yield f"data: {json.dumps({'token': '', 'done': True, 'model': datos.get('model', '')})}\n\n"
                            break
                    except json.JSONDecodeError:
                        continue

    except Exception as exc:
        logger.error(f"[STREAM] Error en streaming: {exc}")
        yield f"data: {json.dumps({'error': str(exc), 'done': True})}\n\n"


# =============================================================================
# AGENTE PRINCIPAL (Orquestador del grafo)
# =============================================================================

class AgentDeVentas(AgenteBase):
    def __init__(self):
        super().__init__(name="Agente de Ventas FluxAgent V2")

    def construir_prompt_sistema(self, contexto: ContextoAgente) -> str:
        return f"Asistente de ventas para {contexto.configuracion.get('name', 'el cliente')}"

    async def procesar(
        self,
        contexto: ContextoAgente,
        sesion:   Optional[AsyncSession] = None,
    ) -> RespuestaAgente:
        status = EstadoConversacion(contexto=contexto)
        if sesion:
            status = await nodo_recuperacion(status, sesion)
        status = await nodo_generacion(status)
        return RespuestaAgente(
            contenido=status.respuesta_final or "No pude generar una respuesta.",
            tokens_usados=status.tokens_usados,
            modelo_usado=status.modelo_usado,
            fuentes_rag=[c.get("fuente_nombre", "") for c in status.chunks_rag],
            metadatos={"chunks_usados": len(status.chunks_rag)},
        )

    async def procesar_streaming(
        self,
        contexto: ContextoAgente,
        sesion:   Optional[AsyncSession] = None,
    ) -> AsyncGenerator[str, None]:
        status = EstadoConversacion(contexto=contexto)
        if sesion:
            status = await nodo_recuperacion(status, sesion)
        
        estado_con_prompt = await _preparar_estado_para_stream(status)
        async for token_sse in nodo_generacion_stream(estado_con_prompt):
            yield token_sse


async def _preparar_estado_para_stream(status: EstadoConversacion) -> EstadoConversacion:
    ctx = status.contexto
    cfg = ctx.configuracion

    contexto_rag = ""
    if status.chunks_rag:
        partes = [f"[Ref {i+1}]: {c['contenido']}" for i, c in enumerate(status.chunks_rag)]
        contexto_rag = "\n\n## INFORMACIÓN DE TU BASE DE CONOCIMIENTO:\n" + "\n\n".join(partes)

    humor_desc = {
        "formal": "formal y corporativo", "profesional": "profesional y empático",
        "amigable": "amigable y cálido", "casual": "casual y directo",
        "humoristico": "con sentido del mood natural",
    }.get(cfg.get("mood", "profesional"), "profesional")

    secciones_script = _generar_secciones_script(cfg)

    status.prompt_sistema = f"""Eres {cfg.get('name', 'Asistente')}, asistente de ventas IA.

Eres {humor_desc}. {cfg.get('personality', '')}

Empresa: {cfg.get('business_type', 'Empresa de servicios')}
Instrucciones: {cfg.get('instructions', 'Ayuda al cliente.')}

{secciones_script}

{contexto_rag}"""

    return status
