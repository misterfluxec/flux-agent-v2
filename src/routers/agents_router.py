# =============================================================================
# FLUXAGENT V2 — ROUTER DE AGENTES IA
# =============================================================================
# Gestión de múltiples agentes IA por tenant
# CRUD completo + configuración de personalidad y modelo
# =============================================================================

import logging
import json
from uuid import UUID, uuid4
from typing import Optional, List, Dict, Any
from datetime import time

import os
import shutil
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image

from auth import PayloadToken, get_usuario_actual, get_tenant_actual, solo_admin
from database import obtener_sesion, configurar_rls

logger = logging.getLogger(__name__)

def parse_time(time_str: Optional[str] = None) -> Optional[time]:
    if not time_str:
        return None
    try:
        parts = time_str.split(':')
        return time(int(parts[0]), int(parts[1]))
    except Exception:
        return None

router = APIRouter(prefix="/api/v1/agents", tags=["Agentes IA"])


# =============================================================================
# SCHEMAS
# =============================================================================

class AgentCreate(BaseModel):
    nombre: str
    area: Optional[str] = None
    descripcion: Optional[str] = None
    genero: str = "femenino"
    humor: str = "profesional"
    personalidad: Optional[str] = None
    idioma: str = "Español (Ecuador)"
    tono: str = "profesional"
    coleccion_rag: Optional[str] = None
    tipo_negocio: Optional[str] = None
    objetivo: Optional[str] = None
    instrucciones: Optional[str] = None
    modelo: str = "qwen2.5:3b"
    temperatura: float = 0.7
    max_tokens: int = 512
    canales: List[str] = ["web_chat"]
    horario_inicio: Optional[str] = None
    horario_fin: Optional[str] = None
    dias_atencion: Optional[List[str]] = None
    mensaje_fuera_horario: Optional[str] = None
    script_ventas: Optional[Dict[str, Any]] = None
    agent_type: str = "sales"
    specialty: Optional[str] = None
    system_prompt: Optional[str] = None

class AgentUpdate(BaseModel):
    nombre: Optional[str] = None
    area: Optional[str] = None
    descripcion: Optional[str] = None
    genero: Optional[str] = None
    humor: Optional[str] = None
    personalidad: Optional[str] = None
    idioma: Optional[str] = None
    tono: Optional[str] = None
    coleccion_rag: Optional[str] = None
    tipo_negocio: Optional[str] = None
    objetivo: Optional[str] = None
    instrucciones: Optional[str] = None
    modelo: Optional[str] = None
    temperatura: Optional[float] = None
    max_tokens: Optional[int] = None
    canales: Optional[List[str]] = None
    horario_inicio: Optional[str] = None
    horario_fin: Optional[str] = None
    dias_atencion: Optional[List[str]] = None
    mensaje_fuera_horario: Optional[str] = None
    script_ventas: Optional[Dict[str, Any]] = None
    agent_type: Optional[str] = None
    specialty: Optional[str] = None
    system_prompt: Optional[str] = None

class AgentResponse(BaseModel):
    id: str
    nombre: str
    area: Optional[str] = None
    descripcion: Optional[str] = None
    genero: str
    humor: str
    personalidad: Optional[str] = None
    idioma: str
    tono: str
    coleccion_rag: Optional[str] = None
    tipo_negocio: Optional[str] = None
    objetivo: Optional[str] = None
    instrucciones: Optional[str] = None
    modelo: str
    temperatura: float
    max_tokens: int
    canales: List[str]
    horario_inicio: Optional[str] = None
    horario_fin: Optional[str] = None
    dias_atencion: Optional[List[str]] = None
    mensaje_fuera_horario: Optional[str] = None
    script_ventas: Optional[Dict[str, Any]] = None
    agent_type: str
    specialty: Optional[str] = None
    system_prompt: Optional[str] = None
    estado: str
    creado_en: str
    actualizado_en: str
    knowledge_base_size: int = 0
    last_sync_at: Optional[str] = None


class GenerateIdentityRequest(BaseModel):
    descripcion_negocio: str
    agent_type: str
    tono: str

@router.post("/generate-identity", summary="Genera instrucciones de sistema óptimas usando IA")
async def generate_identity(
    req: GenerateIdentityRequest,
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    from core.llm.router import llm_router
    
    prompt = f"""
Eres un ingeniero de prompts experto creando la "Identidad de Sistema" para un agente de IA en la plataforma FluxAgent.
El usuario tiene este negocio: "{req.descripcion_negocio}"
Tipo de operación (Agent Type): {req.agent_type}
Tono de personalidad deseado: {req.tono}

Crea unas instrucciones en PRIMERA PERSONA para este agente ("Eres un asistente...").
El resultado debe ser únicamente el texto del prompt, directo y sin introducciones.

DEBES INCLUIR OBLIGATORIAMENTE LAS SIGUIENTES REGLAS DE GOBERNANZA AL FINAL:
- Nunca inventes precios o stock; consulta siempre la herramienta de Catálogo (check_availability).
- Si detectas frustración en el usuario, solicita intervención humana inmediatamente.
- No realices reembolsos ni cambios de configuración de cuenta, indica que esos procesos son manuales.

Haz que el prompt sea profesional, conciso y listo para copiarse y pegarse.
"""
    try:
        resultado = await llm_router.generate(
            messages=[{"role": "user", "content": prompt}],
            model="qwen2.5:3b", # Usamos el local por defecto
            temperature=0.7
        )
        texto = resultado if isinstance(resultado, str) else resultado.get("content", "")
        return {"instructions": texto.strip()}
    except Exception as e:
        logger.error(f"Error generating identity: {e}")
        raise HTTPException(status_code=500, detail="Error al generar identidad")

# =============================================================================
# GET /api/v1/agents — Lista agentes del tenant
# =============================================================================

@router.get("", summary="Lista todos los agentes IA del tenant")
async def list_agents(
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion),
) -> List[AgentResponse]:
    """Retorna la lista de agentes configurados del tenant actual."""
    await configurar_rls(db, UUID(usuario.tenant_id))
    
    result = await db.execute(
        text("""
            SELECT a.id, a.nombre, a.area, a.descripcion, a.genero, a.humor, a.personalidad,
                   a.idioma, a.tono, a.coleccion_rag, a.tipo_negocio, a.objetivo, a.instrucciones,
                   a.modelo, a.temperatura, a.max_tokens, a.canales,
                   a.horario_inicio, a.horario_fin, a.dias_atencion, a.mensaje_fuera_horario,
                   a.script_ventas, a.agent_type, a.specialty, a.system_prompt, a.estado, a.creado_en, a.actualizado_en,
                   COUNT(kc.id) as knowledge_base_size,
                   MAX(kc.creado_en) as last_sync_at
            FROM agents a
            LEFT JOIN knowledge_chunks kc ON kc.agent_id = a.id
            WHERE a.tenant_id = :tenant_id
            GROUP BY a.id, a.nombre, a.area, a.descripcion, a.genero, a.humor, a.personalidad,
                     a.idioma, a.tono, a.coleccion_rag, a.tipo_negocio, a.objetivo, a.instrucciones,
                     a.modelo, a.temperatura, a.max_tokens, a.canales,
                     a.horario_inicio, a.horario_fin, a.dias_atencion, a.mensaje_fuera_horario,
                     a.script_ventas, a.agent_type, a.specialty, a.system_prompt, a.estado, a.creado_en, a.actualizado_en
            ORDER BY a.nombre ASC
        """),
        {"tenant_id": usuario.tenant_id}
    )
    
    agentes = []
    for row in result.fetchall():
        agentes.append(AgentResponse(
            id=str(row.id),
            nombre=row.nombre,
            area=row.area,
            descripcion=row.descripcion,
            genero=row.genero,
            humor=row.humor,
            personalidad=row.personalidad,
            idioma=row.idioma,
            tono=row.tono,
            coleccion_rag=row.coleccion_rag,
            tipo_negocio=row.tipo_negocio,
            objetivo=row.objetivo,
            instrucciones=row.instrucciones,
            modelo=row.modelo,
            temperatura=row.temperatura,
            max_tokens=row.max_tokens,
            canales=row.canales or [],
            horario_inicio=str(row.horario_inicio) if row.horario_inicio else None,
            horario_fin=str(row.horario_fin) if row.horario_fin else None,
            dias_atencion=row.dias_atencion,
            mensaje_fuera_horario=row.mensaje_fuera_horario,
            script_ventas=row.script_ventas if hasattr(row, 'script_ventas') else None,
            agent_type=row.agent_type,
            specialty=row.specialty,
            system_prompt=row.system_prompt,
            estado=row.estado,
            creado_en=str(row.creado_en),
            actualizado_en=str(row.actualizado_en),
            knowledge_base_size=row.knowledge_base_size or 0,
            last_sync_at=str(row.last_sync_at) if row.last_sync_at else None
        ))
    
    return agentes


# =============================================================================
# POST /api/v1/agents — Crear nuevo agente
# =============================================================================

@router.post("", summary="Crea un nuevo agente IA", status_code=status.HTTP_201_CREATED)
async def create_agent(
    datos: AgentCreate,
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Crea un nuevo agente con configuración personalizada."""
    await configurar_rls(db, UUID(usuario.tenant_id))
    
    # Verificar límite de agentes según el plan
    result_plan = await db.execute(
        text("SELECT max_agentes FROM tenants WHERE id = :tid"),
        {"tid": usuario.tenant_id}
    )
    plan_row = result_plan.fetchone()
    max_agentes = plan_row.max_agentes if plan_row else 1
    
    result_count = await db.execute(
        text("SELECT COUNT(*) FROM agents WHERE tenant_id = :tid"),
        {"tid": usuario.tenant_id}
    )
    current_count = result_count.scalar() or 0
    
    if current_count >= max_agentes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Has alcanzado el límite de {max_agentes} agentes de tu plan. Upgrade para más."
        )
    
    nuevo_id = uuid4()
    dias_array = datos.dias_atencion if datos.dias_atencion is not None else ["lunes", "martes", "miercoles", "jueves", "viernes"]
    canales_array = datos.canales if datos.canales is not None else ["web_chat"]
    
    # Generar prompt completo usando plantillas pre-cargadas
    def generate_system_prompt(datos):
        """Generar prompt completo usando plantillas pre-cargadas."""
        
        base_prompts = {
            'sales': {
                'intro': f"Eres un vendedor experto especializado en {datos.specialty or 'ventas generales'}.",
                'main': "Tu objetivo es guiar al cliente hacia una compra exitosa.",
                'style': f"Eres {datos.tono}, profesional y servicial."
            },
            'support': {
                'intro': f"Eres un especialista en soporte técnico especializado en {datos.specialty or 'soporte general'}.",
                'main': "Tu objetivo es resolver problemas de manera eficiente y satisfacer al cliente.",
                'style': f"Eres {datos.tono}, paciente y servicial."
            },
            'bookings': {
                'intro': f"Eres un asistente de reservas especializado en {datos.specialty or 'gestión de reservas'}.",
                'main': "Tu objetivo es ayudar a los clientes a programar y gestionar sus citas.",
                'style': f"Eres {datos.tono}, organizado y amigable."
            },
            'custom': {
                'intro': f"Eres {datos.nombre}, un asistente experto especializado en {datos.specialty or 'asistencia general'}.",
                'main': "Tu objetivo es proporcionar el mejor servicio posible según las necesidades del cliente.",
                'style': f"Eres {datos.tono}, adaptable y profesional."
            }
        }
        
        prompt_config = base_prompts.get(datos.agent_type, base_prompts['sales'])
        
        system_prompt = f"""
{prompt_config['intro']}

## TU ESTILO:
{prompt_config['style']}

## TU OBJETIVO:
{prompt_config['main']}

## INSTRUCCIONES ESPECÍFICAS:
{datos.system_prompt or 'Ayuda al cliente de manera eficiente y profesional.'}

## DIRECTRICES DE COMUNICACIÓN:
- Mantén siempre un tono {datos.tono}
- Sé claro y conciso en tus respuestas
- Adapta tu comunicación según las necesidades del cliente
- Ofrece soluciones prácticas y útiles
"""
        
        return system_prompt.strip()
    
    # Generar prompt dinámico
    final_prompt = generate_system_prompt(datos)
    
    # Mapear datos del frontend a la estructura unificada de la BD
    area_mapeada = {
        'sales': 'Ventas',
        'support': 'Soporte', 
        'bookings': 'Reservas',
        'custom': 'General'
    }.get(datos.agent_type, 'General')
    
    genero_mapeado = 'femenino'  # Valor por defecto consistente
    
    # Generar script de ventas base
    def generate_sales_script(agent_type):
        """Generar script de ventas según el tipo de agente."""
        
        scripts_base = {
            'sales': {
                "fases": ["contacto", "calificacion", "presentacion", "cierre", "seguimiento"],
                "reglas": ["siempre saludar primero", "identificar necesidades", "presentar beneficios", "pedir acción"],
                "scripts": {
                    "contacto": "Hola, soy {nombre}. ¿En qué puedo ayudarte hoy?",
                    "calificacion": "Para poder ayudarte mejor, ¿podrías contarme más sobre lo que buscas?",
                    "presentacion": "Basado en lo que me comentas, te recomiendo...",
                    "cierre": "¿Te gustaría proceder con esta opción?",
                    "seguimiento": "Gracias por tu interés. ¿Hay algo más en lo que pueda ayudarte?"
                },
                "escalacion": {"enabled": True, "keywords": ["gerente", "supervisor", "queja"]}
            },
            'support': {
                "fases": ["recepcion", "diagnostico", "solucion", "verificacion", "cierre"],
                "reglas": ["escuchar activamente", "identificar problema", "ofrecer solución", "confirmar resolución"],
                "scripts": {
                    "recepcion": "Hola, soy {nombre}. Entiendo que necesitas ayuda con...",
                    "diagnostico": "Vamos a identificar el problema. ¿Cuándo ocurrió?",
                    "solucion": "Para solucionar esto, te recomiendo...",
                    "verificacion": "¿Podrías confirmar si el problema está resuelto?",
                    "cierre": "Gracias por tu paciencia. ¿Hay algo más en lo que pueda ayudarte?"
                },
                "escalacion": {"enabled": True, "keywords": ["urgente", "emergencia", "gerente"]}
            },
            'bookings': {
                "fases": ["bienvenida", "disponibilidad", "confirmacion", "recordatorio", "cierre"],
                "reglas": ["verificar disponibilidad", "confirmar detalles", "enviar recordatorio", "confirmar cita"],
                "scripts": {
                    "bienvenida": "Hola, soy {nombre}. ¿En qué puedo ayudarte con tu reserva?",
                    "disponibilidad": "Voy a verificar la disponibilidad para ti...",
                    "confirmacion": "Tengo disponibilidad en los siguientes horarios...",
                    "recordatorio": "Te enviaré un recordatorio antes de tu cita.",
                    "cierre": "Tu cita está confirmada. ¿Hay algo más que necesites?"
                },
                "escalacion": {"enabled": false, "keywords": []}
            },
            'custom': {
                "fases": ["contacto", "comprension", "accion", "seguimiento"],
                "reglas": ["escuchar activamente", "comprender necesidades", "proporcionar ayuda", "verificar satisfacción"],
                "scripts": {
                    "contacto": "Hola, soy {nombre}. ¿En qué puedo ayudarte?",
                    "comprension": "Entiendo que necesitas ayuda con...",
                    "accion": "Para ayudarte, voy a...",
                    "seguimiento": "¿Hay algo más en lo que pueda asistirte?"
                },
                "escalacion": {"enabled": True, "keywords": ["ayuda adicional", "supervisor"]}
            }
        }
        
        return scripts_base.get(agent_type, scripts_base['sales'])
        
    await db.execute(
        text("""
            INSERT INTO agents (
                id, tenant_id, nombre, area, descripcion, genero, humor, personalidad,
                idioma, tono, coleccion_rag, tipo_negocio, objetivo, instrucciones,
                modelo, temperatura, max_tokens, canales,
                horario_inicio, horario_fin, dias_atencion, mensaje_fuera_horario,
                script_ventas, agent_type, specialty, system_prompt, estado
            ) VALUES (
                :id, :tid, :nombre, :area, :desc, :gen, :hum, :pers,
                :idioma, :tono, :coleccion, :tipo, :objetivo, :instr,
                :modelo, :temp, :tokens, :canales,
                :hora_ini, :hora_fin, :dias, :msg_fuera,
                :script_ventas, :agent_type, :specialty, :system_prompt, 'activo'
            )
        """),
        {
            "id": str(nuevo_id),
            "tid": usuario.tenant_id,
            "nombre": datos.nombre.strip(),
            "area": area_mapeada,
            "desc": datos.descripcion,
            "gen": genero_mapeado,
            "hum": datos.humor,
            "pers": datos.personalidad,
            "idioma": datos.idioma,
            "tono": datos.tono,
            "coleccion": datos.coleccion_rag,
            "tipo": datos.tipo_negocio,
            "objetivo": datos.objetivo,
            "instr": datos.instrucciones,
            "modelo": datos.modelo,
            "temp": datos.temperatura,
            "tokens": datos.max_tokens,
            "canales": canales_array,
            "hora_ini": parse_time(datos.horario_inicio),
            "hora_fin": parse_time(datos.horario_fin),
            "dias": dias_array,
            "msg_fuera": datos.mensaje_fuera_horario,
            "script_ventas": json.dumps(datos.script_ventas) if datos.script_ventas else json.dumps(generate_sales_script(datos.agent_type)),
            "agent_type": datos.agent_type,
            "specialty": datos.specialty,
            "system_prompt": final_prompt,
        }
    )
    await db.commit()
    
    logger.info(f"Agente creado: {datos.nombre} | tenant={usuario.tenant_id} | area={datos.area}")
    
    return {
        "mensaje": "Agente creado correctamente",
        "agente_id": str(nuevo_id)
    }


# =============================================================================
# GET /api/v1/agents/{agent_id} — Obtener agente específico
# =============================================================================

@router.get("/{agent_id}", summary="Obtiene un agente específico")
async def get_agent(
    agent_id: UUID,
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion),
) -> AgentResponse:
    await configurar_rls(db, UUID(usuario.tenant_id))
    
    result = await db.execute(
        text("""
            SELECT id, nombre, area, descripcion, genero, humor, personalidad,
                   idioma, tono, coleccion_rag, tipo_negocio, objetivo, instrucciones,
                   modelo, temperatura, max_tokens, canales,
                   horario_inicio, horario_fin, dias_atencion, mensaje_fuera_horario,
                   script_ventas, agent_type, specialty, system_prompt, estado, creado_en, actualizado_en
            FROM agents
            WHERE id = :aid AND tenant_id = :tid
        """),
        {"aid": str(agent_id), "tid": usuario.tenant_id}
    )
    
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    return AgentResponse(
        id=str(row.id),
        nombre=row.nombre,
        area=row.area,
        descripcion=row.descripcion,
        genero=row.genero,
        humor=row.humor,
        personalidad=row.personalidad,
        idioma=row.idioma,
        tono=row.tono,
        coleccion_rag=row.coleccion_rag,
        tipo_negocio=row.tipo_negocio,
        objetivo=row.objetivo,
        instrucciones=row.instrucciones,
        modelo=row.modelo,
        temperatura=row.temperatura,
        max_tokens=row.max_tokens,
        canales=row.canales or [],
        horario_inicio=str(row.horario_inicio) if row.horario_inicio else None,
        horario_fin=str(row.horario_fin) if row.horario_fin else None,
        dias_atencion=row.dias_atencion or [],
        mensaje_fuera_horario=row.mensaje_fuera_horario,
        script_ventas=row.script_ventas if hasattr(row, 'script_ventas') else None,
        agent_type=row.agent_type,
        specialty=row.specialty,
        system_prompt=row.system_prompt,
        estado=row.estado,
        creado_en=str(row.creado_en),
        actualizado_en=str(row.actualizado_en),
    )


# =============================================================================
# PATCH /api/v1/agents/{agent_id} — Actualizar agente
# =============================================================================

@router.patch("/{agent_id}", summary="Actualiza la configuración de un agente")
async def update_agent(
    agent_id: UUID,
    datos: AgentUpdate,
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Actualiza la configuración de un agente existente."""
    await configurar_rls(db, UUID(usuario.tenant_id))
    
    # Verificar que el agente exista
    result_check = await db.execute(
        text("SELECT nombre FROM agents WHERE id = :aid AND tenant_id = :tid"),
        {"aid": str(agent_id), "tid": usuario.tenant_id}
    )
    if not result_check.fetchone():
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    updates = []
    params = {"aid": str(agent_id), "tid": usuario.tenant_id}
    
    campos = {
        "nombre": datos.nombre,
        "area": datos.area,
        "descripcion": datos.descripcion,
        "genero": datos.genero,
        "humor": datos.humor,
        "personalidad": datos.personalidad,
        "idioma": datos.idioma,
        "tono": datos.tono,
        "coleccion_rag": datos.coleccion_rag,
        "tipo_negocio": datos.tipo_negocio,
        "objetivo": datos.objetivo,
        "instrucciones": datos.instrucciones,
        "modelo": datos.modelo,
        "temperatura": datos.temperatura,
        "max_tokens": datos.max_tokens,
        "mensaje_fuera_horario": datos.mensaje_fuera_horario,
        "agent_type": datos.agent_type,
        "specialty": datos.specialty,
        "system_prompt": datos.system_prompt,
    }
    
    for campo, valor in campos.items():
        if valor is not None:
            db_campo = "coleccion_rag" if campo == "coleccion_rag" else campo
            updates.append(f"{db_campo} = :{campo}")
            params[campo] = valor
    
    if datos.canales is not None:
        updates.append("canales = :canales")
        params["canales"] = datos.canales
    
    if datos.dias_atencion is not None:
        updates.append("dias_atencion = :dias_atencion")
        params["dias_atencion"] = datos.dias_atencion
    
    if datos.horario_inicio is not None:
        updates.append("horario_inicio = :horario_inicio")
        params["horario_inicio"] = parse_time(datos.horario_inicio)
    
    if datos.horario_fin is not None:
        updates.append("horario_fin = :horario_fin")
        params["horario_fin"] = parse_time(datos.horario_fin)
    
    if datos.estado is not None and datos.estado in ("entrenando", "activo", "pausado", "archivado"):
        updates.append("estado = :estado")
        params["estado"] = datos.estado
        
    if datos.script_ventas is not None:
        updates.append("script_ventas = :script_ventas")
        params["script_ventas"] = json.dumps(datos.script_ventas)
    
    if not updates:
        return {"mensaje": "No hay cambios para aplicar"}
    
    query = f"UPDATE agents SET {', '.join(updates)} WHERE id = :aid AND tenant_id = :tid"
    await db.execute(text(query), params)
    await db.commit()
    
    logger.info(f"Agente actualizado: {agent_id} | tenant={usuario.tenant_id}")
    
    return {"mensaje": "Agente actualizado correctamente"}


# =============================================================================
# POST /api/v1/agents/{agent_id}/avatar — Subir Avatar del Agente
# =============================================================================

@router.post("/{agent_id}/avatar", summary="Sube un avatar para el agente")
async def upload_agent_avatar(
    agent_id: UUID,
    file: UploadFile = File(...),
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Sube un avatar y actualiza el campo en script_ventas."""
    await configurar_rls(db, UUID(usuario.tenant_id))
    
    # Check if agent exists
    result_check = await db.execute(
        text("SELECT script_ventas FROM agents WHERE id = :aid AND tenant_id = :tid"),
        {"aid": str(agent_id), "tid": usuario.tenant_id}
    )
    row = result_check.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
        
    # Save file
    file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else 'png'
    # Siempre guardaremos como webp para máxima compresión
    new_filename = f"avatar_{agent_id}_{uuid4().hex[:8]}.webp"
    file_path = os.path.join("uploads", "avatars", new_filename)
    
    try:
        # Optimizar imagen con Pillow
        image_data = await file.read()
        image = Image.open(BytesIO(image_data))
        
        # Redimensionar manteniendo proporción (Max 800x800)
        image.thumbnail((800, 800), Image.Resampling.LANCZOS)
        
        # Convertir a RGB para evitar problemas con paletas
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
            
        # Guardar comprimido como WEBP
        image.save(file_path, 'WEBP', quality=80, optimize=True)
        
    except Exception as e:
        logger.error(f"Error optimizando imagen del avatar, usando guardado directo: {e}")
        # Fallback a guardado directo si falla Pillow
        new_filename = f"avatar_{agent_id}_{uuid4().hex[:8]}.{file_ext}"
        file_path = os.path.join("uploads", "avatars", new_filename)
        file.file.seek(0)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
    # Public URL
    # In production, this should include the domain. For now, relative/static path.
    avatar_url = f"/uploads/avatars/{new_filename}"
    
    # Update script_ventas JSON
    script_ventas = row.script_ventas or {}
    script_ventas["avatar"] = avatar_url
    
    await db.execute(
        text("UPDATE agents SET script_ventas = :script_ventas WHERE id = :aid AND tenant_id = :tid"),
        {
            "script_ventas": json.dumps(script_ventas),
            "aid": str(agent_id),
            "tid": usuario.tenant_id
        }
    )
    await db.commit()
    
    logger.info(f"Avatar actualizado para agente {agent_id}: {avatar_url}")
    return {"mensaje": "Avatar subido correctamente", "avatar_url": avatar_url}


# =============================================================================
# DELETE /api/v1/agents/{agent_id} — Eliminar agente
# =============================================================================

@router.delete("/{agent_id}", summary="Elimina un agente")
async def delete_agent(
    agent_id: UUID,
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Elimina un agente (no elimina el conocimiento asociado)."""
    await configurar_rls(db, UUID(usuario.tenant_id))
    
    result = await db.execute(
        text("DELETE FROM agents WHERE id = :aid AND tenant_id = :tid RETURNING id"),
        {"aid": str(agent_id), "tid": usuario.tenant_id}
    )
    
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    await db.commit()
    
    logger.info(f"Agente eliminado: {agent_id} | tenant={usuario.tenant_id}")
    
    return {"mensaje": "Agente eliminado correctamente"}


# =============================================================================
# POST /api/v1/agents/{agent_id}/test — Probar agente
# =============================================================================

@router.post("/{agent_id}/test", summary="Prueba un agente con un mensaje")
async def test_agent(
    agent_id: UUID,
    mensaje: dict,
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Envía un mensaje de prueba al agente y retorna la respuesta."""
    await configurar_rls(db, UUID(usuario.tenant_id))
    
    # Obtener configuración del agente
    result = await db.execute(
        text("""
            SELECT nombre, instrucciones, modelo, temperatura, max_tokens, personalidad
            FROM agents WHERE id = :aid AND tenant_id = :tid
        """),
        {"aid": str(agent_id), "tid": usuario.tenant_id}
    )
    
    agent = result.fetchone()
    if not agent:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    # Aquí iría la llamada a Ollama con el prompt del agente
    # Por ahora retornamos una respuesta de prueba
    return {
        "agente": agent.nombre,
        "mensaje": mensaje.get("mensaje", ""),
        "respuesta": f"Esta es una respuesta de prueba del agente {agent.nombre}. La integración con Ollama completaría la respuesta real.",
        "modelo": agent.modelo,
    }