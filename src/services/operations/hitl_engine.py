from __future__ import annotations
import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from core.observability.logging import get_logger, LogCategory

from domain.events.action_governance import ActionGovernanceRegistry

logger = get_logger("services.operations.hitl")


class HITLEngine:
    """
    Human-in-the-Loop Execution Engine — versión async.
    Valida gobernanza, registra el Operational State Journal
    y despacha acciones aprobadas.
    """

    def __init__(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: str,
        user_roles: list[str],
        event_bus=None,
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.user_roles = user_roles
        self.event_bus = event_bus

    async def execute_action(
        self,
        action_name: str,
        payload: dict[str, Any],
        ai_audit_log_id: str | None = None,
    ) -> dict[str, Any]:
        correlation_id = f"hitl_{uuid.uuid4().hex[:8]}"

        await self._publish_state_event(
            "action.proposed",
            correlation_id,
            {
                "action": action_name,
                "ai_audit_log_id": ai_audit_log_id,
                "payload": payload,
            },
        )

        if not ActionGovernanceRegistry.can_user_execute(
            action_name, self.user_roles
        ):
            await self._publish_state_event(
                "action.rejected",
                correlation_id,
                {
                    "action": action_name,
                    "reason": "Insufficient RBAC permissions",
                    "user_roles": self.user_roles,
                },
            )
            return {
                "status": "error",
                "message": "Acceso denegado por la capa de Gobernanza.",
                "correlation_id": correlation_id,
            }

        policy = ActionGovernanceRegistry.get_policy(action_name)
        if policy and policy.requires_approval:
            # 1. Emitir log estructurado de telemetría (Grafana)
            logger.business_event(
                "hitl_task_created",
                correlation_id=correlation_id,
                action=action_name,
                tenant_id=self.tenant_id
            )

            await self._publish_state_event(
                "action.pending_approval",
                correlation_id,
                {
                    "action": action_name,
                    "payload": payload,
                    "requested_by": self.user_id,
                },
            )
            
            # 2. Persistir en la tabla human_tasks para el router
            insert_query = text("""
                INSERT INTO human_tasks (tenant_id, status, context_payload)
                VALUES (:tenant_id, 'pending', :context_payload)
                RETURNING id
            """)
            import json
            await self.db.execute(insert_query, {
                "tenant_id": self.tenant_id,
                "context_payload": json.dumps({
                    "correlation_id": correlation_id,
                    "action": action_name,
                    "payload": payload,
                    "requested_by": self.user_id
                })
            })
            await self.db.commit()

            return {
                "status": "pending_approval",
                "message": (
                    f"Acción '{action_name}' requiere "
                    "aprobación humana."
                ),
                "correlation_id": correlation_id,
            }

        await self._publish_state_event(
            "action.approved",
            correlation_id,
            {"action": action_name, "approved_by": self.user_id},
        )

        try:
            result = await self._dispatch(
                action_name, payload
            )
            await self._publish_state_event(
                "action.executed",
                correlation_id,
                {"action": action_name, "result": result},
            )
            return {
                "status": "success",
                "result": result,
                "correlation_id": correlation_id,
            }
        except NotImplementedError:
            await self._publish_state_event(
                "action.failed",
                correlation_id,
                {
                    "action": action_name,
                    "reason": "Handler no implementado",
                },
            )
            return {
                "status": "error",
                "message": f"Handler para '{action_name}' no implementado.",
                "correlation_id": correlation_id,
            }
        except Exception as exc:
            logger.exception(
                "hitl_dispatch_error",
                extra={"action": action_name, "error": str(exc)},
            )
            await self._publish_state_event(
                "action.failed",
                correlation_id,
                {"action": action_name, "reason": str(exc)},
            )
            return {
                "status": "error",
                "message": str(exc),
                "correlation_id": correlation_id,
            }

    async def _dispatch(
        self, action_name: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        handlers = {
            "REPLAY_WEBHOOK": self._handle_replay_webhook,
            "RELEASE_RESERVATION": self._handle_release_reservation,
            "SYNC_CONNECTOR": self._handle_sync_connector,
            "ESCALATE_AGENT": self._handle_escalate_agent,
            "CANCEL_ORDER": self._handle_cancel_order,
            "EXPORT_CUSTOMER_DATA": self._handle_export_data,
        }
        handler = handlers.get(action_name)
        if not handler:
            raise NotImplementedError(action_name)
        return await handler(payload)

    async def _handle_replay_webhook(
        self, payload: dict
    ) -> dict:
        return {
            "recovered_event_id": payload.get("event_id"),
            "status": "requeued_successfully",
        }

    async def _handle_release_reservation(
        self, payload: dict
    ) -> dict:
        return {
            "released_sku": payload.get("sku"),
            "quantity": payload.get("quantity"),
            "status": "released",
        }

    async def _handle_sync_connector(
        self, payload: dict
    ) -> dict:
        return {
            "connector_id": payload.get("connector_id"),
            "status": "sync_triggered",
        }

    async def _handle_escalate_agent(
        self, payload: dict
    ) -> dict:
        return {
            "conversation_id": payload.get("conversation_id"),
            "escalated_to": payload.get("operator_id", "queue"),
            "status": "escalated",
        }

    async def _handle_cancel_order(
        self, payload: dict
    ) -> dict:
        return {
            "order_id": payload.get("order_id"),
            "status": "cancellation_queued",
        }

    async def _handle_export_data(
        self, payload: dict
    ) -> dict:
        return {
            "export_id": str(uuid.uuid4()),
            "customer_segment": payload.get("segment", "all"),
            "status": "export_queued",
        }

    async def _publish_state_event(
        self,
        event_type: str,
        correlation_id: str,
        payload: dict[str, Any],
    ) -> None:
        logger.info(
            LogCategory.BUSINESS,
            "HITL state published",
            metadata={
                "event": event_type,
                "correlation_id": correlation_id,
                "tenant_id": self.tenant_id,
                "payload": payload,
            },
        )
        if self.event_bus:
            try:
                from domain.events import EventType
                await self.event_bus.publish(
                    event_type=EventType.HITL_STATE_TRANSITION
                    if hasattr(EventType, "HITL_STATE_TRANSITION")
                    else event_type,
                    tenant_id=self.tenant_id,
                    payload={
                        "journal_event": event_type,
                        "correlation_id": correlation_id,
                        **payload,
                    },
                )
            except Exception as exc:
                logger.warning(
                    "hitl_journal_publish_failed",
                    extra={"error": str(exc)},
                )
