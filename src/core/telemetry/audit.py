# =============================================================================
# FLUXAGENT V2 — REGISTRO DE AUDITORÍA (BUSINESS)
# =============================================================================
# Registro inmutable en DB de acciones críticas para el usuario final.
# =============================================================================

import logging
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)

class AuditRegistry:
    """
    Gestiona la persistencia de eventos de auditoría en la base de datos.
    Diseñado para ser consumido por el Frontend (Historial de Auditoría).
    """
    
    @staticmethod
    async def record(
        db: AsyncSession,
        tenant_id: UUID,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        status: str = "success",
        details: Dict[str, Any] = {},
        correlation_id: Optional[str] = None
    ):
        """
        Inserta un registro de auditoría. Respeta RLS automáticamente.
        """
        try:
            from .context import get_correlation_id
            cid = correlation_id or get_correlation_id()
            
            await db.execute(
                text("""
                    INSERT INTO auditoria (
                        tenant_id, accion, tipo_recurso, id_recurso, 
                        status, detalles, correlation_id, creado_at
                    ) VALUES (
                        :tid, :acc, :trec, :rid, :est, :det, :cid, :cat
                    )
                """),
                {
                    "tid": tenant_id,
                    "acc": action,
                    "trec": resource_type,
                    "rid": resource_id,
                    "est": status,
                    "det": json.dumps(details),
                    "cid": cid,
                    "cat": datetime.utcnow()
                }
            )
            # Nota: El commit lo debe manejar la transacción padre para consistencia atómica
            logger.debug(f"Audit record: {action} on {resource_type} ({status})")
            
        except Exception as e:
            # No bloqueamos el proceso principal si falla la auditoría, solo logueamos
            logger.error(f"Fallo al registrar auditoría: {e}")

import json
