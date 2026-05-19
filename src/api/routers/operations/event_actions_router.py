"""
Event Actions Router

Endpoints para las acciones operacionales del Operations Dashboard:
  - ACK (acknowledge, snooze, resolve)
  - Assignment (assign_to, claim)
  - Tagging (add/remove tags)

Estos convierten el event_log de "log de auditoría" a "cola de trabajo operacional".
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timezone, timedelta
import logging

from database import obtener_sesion
from auth import PayloadToken, get_usuario_actual

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/events", tags=["events", "operations"])

VALID_ACK_STATES = {"unresolved", "acknowledged", "snoozed", "resolved"}


# =============================================================================
# Modelos de request
# =============================================================================

class AckRequest(BaseModel):
    state: str = Field(..., description="unresolved | acknowledged | snoozed | resolved")
    snooze_minutes: Optional[int] = Field(
        default=None,
        description="Requerido si state='snoozed'. Minutos hasta re-aparición."
    )


class AssignRequest(BaseModel):
    assigned_to: Optional[str] = Field(default=None, description="UUID del usuario asignado")
    assigned_team: Optional[str] = Field(default=None, description="Nombre del equipo")


class TagRequest(BaseModel):
    add: List[str] = Field(default_factory=list)
    remove: List[str] = Field(default_factory=list)


# =============================================================================
# Helpers
# =============================================================================

async def _get_event_or_404(event_id: str, tenant_id: str, db: AsyncSession) -> dict:
    """Verifica que el evento existe y pertenece al tenant."""
    result = await db.execute(text("""
        SELECT event_id, ack_state, assigned_to, assigned_team, tags
        FROM event_log
        WHERE event_id = :event_id AND tenant_id = :tenant_id
        LIMIT 1
    """), {"event_id": event_id, "tenant_id": tenant_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return dict(row._mapping)


# =============================================================================
# Endpoints
# =============================================================================

@router.patch("/{event_id}/ack")
async def acknowledge_event(
    event_id: str,
    body: AckRequest,
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion)
):
    """
    Cambia el status de ACK de un evento.
    - acknowledged: el operador lo vio y lo toma en cuenta
    - snoozed: pospuesto por N minutos (requiere snooze_minutes)
    - resolved: cerrado, no requiere más acción
    - unresolved: re-abrir
    """
    if body.state not in VALID_ACK_STATES:
        raise HTTPException(status_code=422, detail=f"Estado inválido. Use: {VALID_ACK_STATES}")

    if body.state == "snoozed" and not body.snooze_minutes:
        raise HTTPException(status_code=422, detail="snooze_minutes es requerido para status 'snoozed'")

    await _get_event_or_404(event_id, str(usuario.tenant_id), db)

    now = datetime.now(tz=timezone.utc)
    snooze_until = (now + timedelta(minutes=body.snooze_minutes)) if body.state == "snoozed" else None

    await db.execute(text("""
        UPDATE event_log
        SET
            ack_state    = :state,
            acked_by     = :acked_by,
            acked_at     = :acked_at,
            snooze_until = :snooze_until,
            resolved_at  = CASE WHEN :state = 'resolved' THEN :now ELSE resolved_at END
        WHERE event_id = :event_id AND tenant_id = :tenant_id
    """), {
        "state":        body.state,
        "acked_by":     str(usuario.id) if body.state != "unresolved" else None,
        "acked_at":     now if body.state != "unresolved" else None,
        "snooze_until": snooze_until,
        "now":          now,
        "event_id":     event_id,
        "tenant_id":    str(usuario.tenant_id),
    })
    await db.commit()

    return {
        "event_id": event_id,
        "ack_state": body.state,
        "acked_at": now.isoformat(),
        "snooze_until": snooze_until.isoformat() if snooze_until else None,
    }


@router.patch("/{event_id}/assign")
async def assign_event(
    event_id: str,
    body: AssignRequest,
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion)
):
    """
    Asigna un evento a un usuario o equipo.
    Si assigned_to es el propio usuario que llama, se considera un 'claim'.
    """
    await _get_event_or_404(event_id, str(usuario.tenant_id), db)

    now = datetime.now(tz=timezone.utc)
    is_claim = body.assigned_to == str(getattr(usuario, "id", ""))

    await db.execute(text("""
        UPDATE event_log
        SET
            assigned_to   = :assigned_to,
            assigned_team = :assigned_team,
            claimed_at    = :claimed_at,
            ack_state     = CASE WHEN ack_state = 'unresolved' THEN 'acknowledged' ELSE ack_state END
        WHERE event_id = :event_id AND tenant_id = :tenant_id
    """), {
        "assigned_to":   body.assigned_to,
        "assigned_team": body.assigned_team,
        "claimed_at":    now if is_claim else None,
        "event_id":      event_id,
        "tenant_id":     str(usuario.tenant_id),
    })
    await db.commit()

    return {
        "event_id":     event_id,
        "assigned_to":  body.assigned_to,
        "assigned_team": body.assigned_team,
        "claimed": is_claim,
        "claimed_at": now.isoformat() if is_claim else None,
    }


@router.patch("/{event_id}/tags")
async def update_event_tags(
    event_id: str,
    body: TagRequest,
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion)
):
    """
    Agrega o elimina tags de un evento.
    Los tags permiten filtros, búsquedas y automations futuras.
    """
    event = await _get_event_or_404(event_id, str(usuario.tenant_id), db)

    current_tags: List[str] = list(event.get("tags") or [])
    # Agregar nuevos (sin duplicar)
    updated = list(dict.fromkeys(current_tags + body.add))
    # Eliminar los marcados para remove
    updated = [t for t in updated if t not in body.remove]

    await db.execute(text("""
        UPDATE event_log
        SET tags = :tags
        WHERE event_id = :event_id AND tenant_id = :tenant_id
    """), {
        "tags":      updated,
        "event_id":  event_id,
        "tenant_id": str(usuario.tenant_id),
    })
    await db.commit()

    return {"event_id": event_id, "tags": updated}


@router.get("/priority-queue")
async def get_priority_queue(
    limit: int = 20,
    tags: Optional[str] = None,  # Filtrar por tag: "vip,sla-risk"
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion)
):
    """
    Cola priorizada de eventos sin resolver, ordenada por priority_score DESC.
    Alimenta la vista 'Priority Queue' del Operations Dashboard.
    """
    tag_filter = ""
    params = {"tenant_id": str(usuario.tenant_id), "limit": limit}

    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            tag_filter = "AND tags @> :tags"
            params["tags"] = tag_list

    result = await db.execute(text(f"""
        SELECT event_id, event_type, aggregate_type, aggregate_id,
               severity, priority_score, business_impact, tags,
               occurred_at, ack_state, assigned_to, assigned_team
        FROM event_log
        WHERE tenant_id = :tenant_id
          AND ack_state IN ('unresolved', 'acknowledged')
          {tag_filter}
        ORDER BY priority_score DESC, occurred_at DESC
        LIMIT :limit
    """), params)

    items = []
    for row in result.fetchall():
        items.append({
            "event_id":       row.event_id,
            "type":           row.event_type,
            "aggregate":      {"type": row.aggregate_type, "id": str(row.aggregate_id)},
            "severity":       row.severity,
            "priority_score": row.priority_score,
            "business_impact": row.business_impact,
            "tags":           list(row.tags or []),
            "occurred_at":    row.occurred_at.isoformat() if row.occurred_at else None,
            "ack_state":      row.ack_state,
            "assigned_to":    str(row.assigned_to) if row.assigned_to else None,
            "assigned_team":  row.assigned_team,
        })

    return items
