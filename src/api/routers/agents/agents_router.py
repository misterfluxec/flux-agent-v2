# =============================================================================
# FLUXAGENT V2 — ROUTER DE AGENTES IA
# =============================================================================
# Gestión de múltiples agentes IA por tenant
# CRUD completo + configuración de personality y model
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
    name: str
    area: Optional[str] = None
    description: Optional[str] = None
    gender: str = "femenino"
    mood: str = "profesional"
    personality: Optional[str] = None
    language: str = "Español (Ecuador)"
    tone: str = "profesional"
    rag_collection: Optional[str] = None
    business_type: Optional[str] = None
    objective: Optional[str] = None
    instructions: Optional[str] = None
    model: str = "qwen2.5:3b"
    temperature: float = 0.7
    max_tokens: int = 512
    channels: List[str] = ["web_chat"]
    schedule_start: Optional[str] = None
    schedule_end: Optional[str] = None
    service_days: Optional[List[str]] = None
    off_hours_message: Optional[str] = None
    sales_script: Optional[Dict[str, Any]] = None
    agent_type: str = "sales"
    specialty: Optional[str] = None
    system_prompt: Optional[str] = None

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    area: Optional[str] = None
    description: Optional[str] = None
    gender: Optional[str] = None
    mood: Optional[str] = None
    personality: Optional[str] = None
    language: Optional[str] = None
    tone: Optional[str] = None
    rag_collection: Optional[str] = None
    business_type: Optional[str] = None
    objective: Optional[str] = None
    instructions: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    channels: Optional[List[str]] = None
    schedule_start: Optional[str] = None
    schedule_end: Optional[str] = None
    service_days: Optional[List[str]] = None
    off_hours_message: Optional[str] = None
    sales_script: Optional[Dict[str, Any]] = None
    agent_type: Optional[str] = None
    specialty: Optional[str] = None
    system_prompt: Optional[str] = None

class AgentResponse(BaseModel):
    id: str
    name: str
    area: Optional[str] = None
    description: Optional[str] = None
    gender: str
    mood: str
    personality: Optional[str] = None
    language: str
    tone: str
    rag_collection: Optional[str] = None
    business_type: Optional[str] = None
    objective: Optional[str] = None
    instructions: Optional[str] = None
    model: str
    temperature: float
    max_tokens: int
    channels: List[str]
    schedule_start: Optional[str] = None
    schedule_end: Optional[str] = None
    service_days: Optional[List[str]] = None
    off_hours_message: Optional[str] = None
    sales_script: Optional[Dict[str, Any]] = None
    agent_type: str
    specialty: Optional[str] = None
    system_prompt: Optional[str] = None
    status: str
    created_at: str
    updated_at: str
    knowledge_base_size: int = 0
    last_sync_at: Optional[str] = None


class GenerateIdentityRequest(BaseModel):
    descripcion_negocio: str
    agent_type: str
    tone: str

@router.post("/generate-identity", summary="Genera instructions de sistema óptimas usando IA")
async def generate_identity(
    req: GenerateIdentityRequest,
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    from core.llm.router import llm_router
    
    prompt = f"""
Eres un ingeniero de prompts experto creando la "Identidad de Sistema" para un agente de IA en la plataforma FluxAgent.
El usuario tiene este negocio: "{req.descripcion_negocio}"
Tipo de operación (Agent Type): {req.agent_type}
Tono de personality deseado: {req.tone}

Crea unas instructions en PRIMERA PERSONA para este agente ("Eres un asistente...").
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
            SELECT a.id, a.name, a.area, a.description, a.gender, a.mood, a.personality,
                   a.language, a.tone, a.rag_collection, a.business_type, a.objective, a.instructions,
                   a.model, a.temperature, a.max_tokens, a.channels,
                   a.schedule_start, a.schedule_end, a.service_days, a.off_hours_message,
                   a.sales_script, a.agent_type, a.specialty, a.system_prompt, a.status, a.created_at, a.updated_at,
                   COUNT(kc.id) as knowledge_base_size,
                   MAX(kc.creado_en) as last_sync_at
            FROM agents a
            LEFT JOIN knowledge_chunks kc ON kc.agent_id = a.id
            WHERE a.tenant_id = :tenant_id
            GROUP BY a.id, a.name, a.area, a.description, a.gender, a.mood, a.personality,
                     a.language, a.tone, a.rag_collection, a.business_type, a.objective, a.instructions,
                     a.model, a.temperature, a.max_tokens, a.channels,
                     a.schedule_start, a.schedule_end, a.service_days, a.off_hours_message,
                     a.sales_script, a.agent_type, a.specialty, a.system_prompt, a.status, a.created_at, a.updated_at
            ORDER BY a.name ASC
        """),
        {"tenant_id": usuario.tenant_id}
    )
    
    agentes = []
    for row in result.fetchall():
        agentes.append(AgentResponse(
            id=str(row.id),
            name=row.name,
            area=row.area,
            description=row.description,
            gender=row.gender,
            mood=row.mood,
            personality=row.personality,
            language=row.language,
            tone=row.tone,
            rag_collection=row.rag_collection,
            business_type=row.business_type,
            objective=row.objective,
            instructions=row.instructions,
            model=row.model,
            temperature=row.temperature,
            max_tokens=row.max_tokens,
            channels=row.channels or [],
            schedule_start=str(row.schedule_start) if row.schedule_start else None,
            schedule_end=str(row.schedule_end) if row.schedule_end else None,
            service_days=row.service_days,
            off_hours_message=row.off_hours_message,
            sales_script=row.sales_script if hasattr(row, 'sales_script') else None,
            agent_type=row.agent_type,
            specialty=row.specialty,
            system_prompt=row.system_prompt,
            status=row.status,
            created_at=str(row.created_at),
            updated_at=str(row.updated_at),
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
        text("SELECT max_agents FROM tenants WHERE id = :tid"),
        {"tid": usuario.tenant_id}
    )
    plan_row = result_plan.fetchone()
    max_agents = plan_row.max_agents if plan_row else 1
    
    result_count = await db.execute(
        text("SELECT COUNT(*) FROM agents WHERE tenant_id = :tid"),
        {"tid": usuario.tenant_id}
    )
    current_count = result_count.scalar() or 0
    
    if current_count >= max_agents:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Has alcanzado el límite de {max_agents} agentes de tu plan. Upgrade para más."
        )
    
    nuevo_id = uuid4()
    dias_array = datos.service_days if datos.service_days is not None else ["lunes", "martes", "miercoles", "jueves", "viernes"]
    canales_array = datos.channels if datos.channels is not None else ["web_chat"]
    
    # Generar prompt completo usando plantillas pre-cargadas
    def generate_system_prompt(datos):
        """Generar prompt completo usando plantillas pre-cargadas."""
        
        base_prompts = {
            'sales': {
                'intro': f"Eres un vendedor experto especializado en {datos.specialty or 'ventas generales'}.",
                'main': "Tu objective es guiar al cliente hacia una compra exitosa.",
                'style': f"Eres {datos.tone}, profesional y servicial."
            },
            'support': {
                'intro': f"Eres un especialista en soporte técnico especializado en {datos.specialty or 'soporte general'}.",
                'main': "Tu objective es resolver problemas de manera eficiente y satisfacer al cliente.",
                'style': f"Eres {datos.tone}, paciente y servicial."
            },
            'bookings': {
                'intro': f"Eres un asistente de reservas especializado en {datos.specialty or 'gestión de reservas'}.",
                'main': "Tu objective es ayudar a los clientes a programar y gestionar sus citas.",
                'style': f"Eres {datos.tone}, organizado y amigable."
            },
            'custom': {
                'intro': f"Eres {datos.name}, un asistente experto especializado en {datos.specialty or 'asistencia general'}.",
                'main': "Tu objective es proporcionar el mejor servicio posible según las necesidades del cliente.",
                'style': f"Eres {datos.tone}, adaptable y profesional."
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
- Mantén siempre un tone {datos.tone}
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
        """Generar script de ventas según el type de agente."""
        
        scripts_base = {
            'sales': {
                "fases": ["contacto", "calificacion", "presentacion", "cierre", "seguimiento"],
                "reglas": ["siempre saludar primero", "identificar necesidades", "presentar beneficios", "pedir acción"],
                "scripts": {
                    "contacto": "Hola, soy {name}. ¿En qué puedo ayudarte hoy?",
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
                    "recepcion": "Hola, soy {name}. Entiendo que necesitas ayuda con...",
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
                    "bienvenida": "Hola, soy {name}. ¿En qué puedo ayudarte con tu reserva?",
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
                    "contacto": "Hola, soy {name}. ¿En qué puedo ayudarte?",
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
                id, tenant_id, name, area, description, gender, mood, personality,
                language, tone, rag_collection, business_type, objective, instructions,
                model, temperature, max_tokens, channels,
                schedule_start, schedule_end, service_days, off_hours_message,
                sales_script, agent_type, specialty, system_prompt, status
            ) VALUES (
                :id, :tid, :name, :area, :desc, :gen, :hum, :pers,
                :language, :tone, :coleccion, :type, :objective, :instr,
                :model, :temp, :tokens, :channels,
                :hora_ini, :hora_fin, :dias, :msg_fuera,
                :sales_script, :agent_type, :specialty, :system_prompt, 'is_active'
            )
        """),
        {
            "id": str(nuevo_id),
            "tid": usuario.tenant_id,
            "name": datos.name.strip(),
            "area": area_mapeada,
            "desc": datos.description,
            "gen": genero_mapeado,
            "hum": datos.mood,
            "pers": datos.personality,
            "language": datos.language,
            "tone": datos.tone,
            "coleccion": datos.rag_collection,
            "type": datos.business_type,
            "objective": datos.objective,
            "instr": datos.instructions,
            "model": datos.model,
            "temp": datos.temperature,
            "tokens": datos.max_tokens,
            "channels": canales_array,
            "hora_ini": parse_time(datos.schedule_start),
            "hora_fin": parse_time(datos.schedule_end),
            "dias": dias_array,
            "msg_fuera": datos.off_hours_message,
            "sales_script": json.dumps(datos.sales_script) if datos.sales_script else json.dumps(generate_sales_script(datos.agent_type)),
            "agent_type": datos.agent_type,
            "specialty": datos.specialty,
            "system_prompt": final_prompt,
        }
    )
    await db.commit()
    
    logger.info(f"Agente creado: {datos.name} | tenant={usuario.tenant_id} | area={datos.area}")
    
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
            SELECT id, name, area, description, gender, mood, personality,
                   language, tone, rag_collection, business_type, objective, instructions,
                   model, temperature, max_tokens, channels,
                   schedule_start, schedule_end, service_days, off_hours_message,
                   sales_script, agent_type, specialty, system_prompt, status, created_at, updated_at
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
        name=row.name,
        area=row.area,
        description=row.description,
        gender=row.gender,
        mood=row.mood,
        personality=row.personality,
        language=row.language,
        tone=row.tone,
        rag_collection=row.rag_collection,
        business_type=row.business_type,
        objective=row.objective,
        instructions=row.instructions,
        model=row.model,
        temperature=row.temperature,
        max_tokens=row.max_tokens,
        channels=row.channels or [],
        schedule_start=str(row.schedule_start) if row.schedule_start else None,
        schedule_end=str(row.schedule_end) if row.schedule_end else None,
        service_days=row.service_days or [],
        off_hours_message=row.off_hours_message,
        sales_script=row.sales_script if hasattr(row, 'sales_script') else None,
        agent_type=row.agent_type,
        specialty=row.specialty,
        system_prompt=row.system_prompt,
        status=row.status,
        created_at=str(row.created_at),
        updated_at=str(row.updated_at),
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
        text("SELECT name FROM agents WHERE id = :aid AND tenant_id = :tid"),
        {"aid": str(agent_id), "tid": usuario.tenant_id}
    )
    if not result_check.fetchone():
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    updates = []
    params = {"aid": str(agent_id), "tid": usuario.tenant_id}
    
    campos = {
        "name": datos.name,
        "area": datos.area,
        "description": datos.description,
        "gender": datos.gender,
        "mood": datos.mood,
        "personality": datos.personality,
        "language": datos.language,
        "tone": datos.tone,
        "rag_collection": datos.rag_collection,
        "business_type": datos.business_type,
        "objective": datos.objective,
        "instructions": datos.instructions,
        "model": datos.model,
        "temperature": datos.temperature,
        "max_tokens": datos.max_tokens,
        "off_hours_message": datos.off_hours_message,
        "agent_type": datos.agent_type,
        "specialty": datos.specialty,
        "system_prompt": datos.system_prompt,
    }
    
    for campo, valor in campos.items():
        if valor is not None:
            db_campo = "rag_collection" if campo == "rag_collection" else campo
            updates.append(f"{db_campo} = :{campo}")
            params[campo] = valor
    
    if datos.channels is not None:
        updates.append("channels = :channels")
        params["channels"] = datos.channels
    
    if datos.service_days is not None:
        updates.append("service_days = :service_days")
        params["service_days"] = datos.service_days
    
    if datos.schedule_start is not None:
        updates.append("schedule_start = :schedule_start")
        params["schedule_start"] = parse_time(datos.schedule_start)
    
    if datos.schedule_end is not None:
        updates.append("schedule_end = :schedule_end")
        params["schedule_end"] = parse_time(datos.schedule_end)
    
    if datos.status is not None and datos.status in ("entrenando", "is_active", "pausado", "archivado"):
        updates.append("status = :status")
        params["status"] = datos.status
        
    if datos.sales_script is not None:
        updates.append("sales_script = :sales_script")
        params["sales_script"] = json.dumps(datos.sales_script)
    
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
    """Sube un avatar y actualiza el campo en sales_script."""
    await configurar_rls(db, UUID(usuario.tenant_id))
    
    # Check if agent exists
    result_check = await db.execute(
        text("SELECT sales_script FROM agents WHERE id = :aid AND tenant_id = :tid"),
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
    
    # Update sales_script JSON
    sales_script = row.sales_script or {}
    sales_script["avatar"] = avatar_url
    
    await db.execute(
        text("UPDATE agents SET sales_script = :sales_script WHERE id = :aid AND tenant_id = :tid"),
        {
            "sales_script": json.dumps(sales_script),
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
            SELECT name, instructions, model, temperature, max_tokens, personality
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
        "agente": agent.name,
        "mensaje": mensaje.get("mensaje", ""),
        "respuesta": f"Esta es una respuesta de prueba del agente {agent.name}. La integración con Ollama completaría la respuesta real.",
        "model": agent.model,
    }