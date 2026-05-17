import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from database import sesion_db
from config import obtener_config
from core.llm.router import llm_router

logger = logging.getLogger(__name__)
config = obtener_config()

# =============================================================================
# MOTOR CENTRAL DE CHAT
# =============================================================================

async def procesar_mensaje_entrante(
    tenant_id: UUID,
    agent_id: UUID,
    canal: str,
    lead_externo_id: str,
    mensaje_texto: str,
    instancia_nombre: Optional[str] = None
) -> str:
    """
    Función central para procesar un mensaje entrante (ej. de WhatsApp).
    Busca al agente, recupera contexto RAG, llama a Ollama y guarda la conversación.
    """
    async with sesion_db(tenant_id) as db:
        # 1. Obtener información del agente
        res_agent = await db.execute(text("""
            SELECT name, instructions, model, temperature, max_tokens, personality, gender, mood, sales_script
            FROM agents WHERE id = :agent_id AND tenant_id = :tenant_id
        """), {"agent_id": str(agent_id), "tenant_id": str(tenant_id)})
        
        agente = res_agent.fetchone()
        if not agente:
            logger.error(f"Agente {agent_id} no encontrado para tenant {tenant_id}")
            return "Lo siento, el agente no está disponible en este momento."

        # 2. Obtener o crear conversación
        res_conv = await db.execute(text("""
            SELECT id FROM conversaciones 
            WHERE tenant_id = :tid AND lead_externo_id = :lead AND canal = :canal AND estado = 'activa'
            ORDER BY iniciada_en DESC LIMIT 1
        """), {"tid": str(tenant_id), "lead": lead_externo_id, "canal": canal})
        
        conv = res_conv.fetchone()
        if not conv:
            res_new_conv = await db.execute(text("""
                INSERT INTO conversaciones (tenant_id, agent_id, lead_externo_id, canal, estado)
                VALUES (:tid, :aid, :lead, :canal, 'activa')
                RETURNING id
            """), {"tid": str(tenant_id), "aid": str(agent_id), "lead": lead_externo_id, "canal": canal})
            conversation_id = res_new_conv.scalar()
        else:
            conversation_id = conv.id

        # 3. Guardar el mensaje del usuario
        await db.execute(text("""
            INSERT INTO mensajes (conversacion_id, tenant_id, rol, contenido)
            VALUES (:cid, :tid, 'usuario', :contenido)
        """), {"cid": str(conversation_id), "tid": str(tenant_id), "contenido": mensaje_texto})
        
        # 4. Recuperar contexto RAG (Búsqueda vectorial simulada o real)
        contexto_rag = await buscar_contexto_rag(db, tenant_id, agent_id, mensaje_texto)
        
        # 5. Obtener historial reciente
        res_hist = await db.execute(text("""
            SELECT rol, contenido FROM mensajes 
            WHERE conversacion_id = :cid
            ORDER BY creado_en DESC LIMIT 10
        """), {"cid": str(conversation_id)})
        historial_inverso = res_hist.fetchall()
        
        # Invertir para que estén en sort_order cronológico
        mensajes_llm = []
        
        # System prompt
        prompt_sistema = f"Eres {agente.name}, un asistente {agente.gender} con tone {agente.mood}.\n"
        if agente.personality: prompt_sistema += f"Personalidad: {agente.personality}\n"
        if agente.instructions: prompt_sistema += f"Instrucciones: {agente.instructions}\n"
        
        if contexto_rag:
            prompt_sistema += f"\n\nContexto de la empresa (Usa esta información para responder):\n{contexto_rag}\n"

        mensajes_llm.append({"role": "system", "content": prompt_sistema})
        
        for msg in reversed(historial_inverso):
            rol_llm = "assistant" if msg.rol == "asistente" else "user"
            mensajes_llm.append({"role": rol_llm, "content": msg.contenido})
            
        # 6. Llamar a Ollama (Loop de tools)
        import json
        from services.tool_executor import ToolExecutor
        from core.tool_registry import COMMERCE_TOOLS
        
        executor = ToolExecutor()
        for tool in COMMERCE_TOOLS:
            executor.register(tool)
            
        commerce_schemas = executor.get_all_tools_schema()
        
        respuesta_llm = await llamar_ollama(mensajes_llm, agente.model, agente.temperature, tools=commerce_schemas)
        
        while isinstance(respuesta_llm, dict) and "tool_calls" in respuesta_llm:
            tool_calls = respuesta_llm["tool_calls"]
            mensajes_llm.append({
                "role": "assistant",
                "content": respuesta_llm.get("content", ""),
                "tool_calls": tool_calls
            })
            
            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                arguments = tool_call["function"]["arguments"]
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                
                logger.info(f"LLM llamando a tool: {function_name} con args {arguments}")
                
                res = await executor.execute(function_name, arguments, str(tenant_id))
                tool_result = json.dumps(res)
                    
                mensajes_llm.append({
                    "role": "tool",
                    "name": function_name,
                    "content": tool_result
                })
            
            # Segunda llamada al LLM con los resultados
            respuesta_llm = await llamar_ollama(mensajes_llm, agente.model, agente.temperature, tools=commerce_schemas)
            
        respuesta_texto_crudo = respuesta_llm if isinstance(respuesta_llm, str) else respuesta_llm.get("content", "")
        
        from services.text_cleaner import clean_for_whatsapp
        respuesta_texto = clean_for_whatsapp(respuesta_texto_crudo)
        
        # 7. Guardar la respuesta del asistente
        await db.execute(text("""
            INSERT INTO mensajes (conversacion_id, tenant_id, rol, contenido)
            VALUES (:cid, :tid, 'asistente', :contenido)
        """), {"cid": str(conversation_id), "tid": str(tenant_id), "contenido": respuesta_texto})
        
        await db.commit()
        return respuesta_texto


async def buscar_contexto_rag(db: AsyncSession, tenant_id: UUID, agent_id: UUID, pregunta: str) -> str:
    """Obtiene contexto semántico para la pregunta usando Ollama embeddings."""
    try:
        # Generar embedding de la pregunta
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{config.ollama_base_url}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": pregunta}
            )
            if resp.status_code == 200:
                vector = resp.json().get("embedding")
                if vector:
                    # Búsqueda vectorial
                    vector_str = "[" + ",".join(map(str, vector)) + "]"
                    res = await db.execute(text("""
                        SELECT contenido FROM knowledge_chunks
                        WHERE tenant_id = :tid 
                        ORDER BY embedding <-> CAST(:vec AS vector) LIMIT 3
                    """), {"tid": str(tenant_id), "vec": vector_str})
                    
                    chunks = [row.contenido for row in res.fetchall()]
                    if chunks:
                        return "\n---\n".join(chunks)
    except Exception as e:
        logger.error(f"Error en RAG: {e}")
    return ""


COMMERCE_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Verifica si un producto está disponible en inventario y obtiene su price.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Nombre del producto a buscar"
                    }
                },
                "required": ["product_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_quote",
            "description": "Crea una cotización oficial para un cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "catalog_item_id": {"type": "string"},
                                "quantity": {"type": "integer"},
                                "unit_price": {"type": "number"}
                            },
                            "required": ["catalog_item_id", "quantity", "unit_price"]
                        }
                    }
                },
                "required": ["items"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_order",
            "description": "Crea un pedido u sort_order de compra.",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "catalog_item_id": {"type": "string"},
                                "quantity": {"type": "integer"},
                                "unit_price": {"type": "number"}
                            },
                            "required": ["catalog_item_id", "quantity", "unit_price"]
                        }
                    },
                    "quote_id": {
                        "type": "string",
                        "description": "ID de la cotización si la hay"
                    }
                },
                "required": ["items"]
            }
        }
    }
]

async def llamar_ollama(mensajes: list, model: str, temperature: float, tools: list = None):
    """Llama al LLM (Ollama local o cloud) y obtiene la respuesta."""
    try:
        return await llm_router.generate(
            messages=mensajes,
            model=model,
            temperature=temperature,
            max_tokens=2048,
            tools=tools
        )
    except Exception as e:
        logger.error(f"Error en LLM: {e}")
        return "Lo siento, mi servicio cognitivo no está disponible temporalmente."

