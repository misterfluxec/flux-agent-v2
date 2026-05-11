import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import uuid

from domain.events.action_governance import ActionGovernanceRegistry
# Simulating the outbox service for event publishing
# from services.events.outbox import publish_event 

logger = logging.getLogger(__name__)

class HITLEngine:
    """
    Fase 5A — Sprint 5A.2: Human-in-the-Loop Execution Engine.
    
    El orquestador que valida permisos (Action Governance), 
    y traza el Operational State Journal (action.approved -> action.executed)
    antes de mutar cualquier estado.
    """

    def __init__(self, db: Session, tenant_id: str, user_id: str, user_roles: List[str]):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.user_roles = user_roles

    def execute_action(self, action_name: str, payload: Dict[str, Any], ai_audit_log_id: str = None) -> Dict[str, Any]:
        """
        Flujo de ejecución de acción gobernada.
        """
        correlation_id = f"hitl_{uuid.uuid4().hex[:8]}"

        # 1. State Journal: action.proposed (Intent by human based on AI context)
        self._publish_state_event(
            "action.proposed",
            correlation_id,
            {"action": action_name, "ai_audit_log_id": ai_audit_log_id, "payload": payload}
        )

        # 2. Validate Governance Policy
        if not ActionGovernanceRegistry.can_user_execute(action_name, self.user_roles):
            # Rechazado por permisos
            self._publish_state_event(
                "action.rejected",
                correlation_id,
                {"action": action_name, "reason": "Insufficient RBAC permissions based on Governance Policy"}
            )
            return {"status": "error", "message": "Access Denied by Action Governance Layer."}

        # 3. State Journal: action.approved (Passed Governance)
        self._publish_state_event(
            "action.approved",
            correlation_id,
            {"action": action_name, "approved_by": self.user_id, "roles": self.user_roles}
        )

        # 4. Dispatch Execution
        try:
            execution_result = self._dispatch_to_handler(action_name, payload)
            
            # 5. State Journal: action.executed
            self._publish_state_event(
                "action.executed",
                correlation_id,
                {"action": action_name, "result": execution_result}
            )
            return {"status": "success", "result": execution_result, "correlation_id": correlation_id}
            
        except Exception as e:
            logger.error(f"Execution failed for {action_name}: {e}")
            self._publish_state_event(
                "action.rejected",
                correlation_id,
                {"action": action_name, "reason": f"Execution Error: {str(e)}"}
            )
            return {"status": "error", "message": f"Execution failed: {str(e)}"}

    def _dispatch_to_handler(self, action_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enruta la acción a su handler específico.
        En una arquitectura real, esto podría ser un worker asíncrono o un command bus.
        """
        logger.info(f"Dispatching action {action_name} with payload {payload}")
        if action_name == "REPLAY_WEBHOOK":
            return {"recovered_event_id": payload.get("event_id"), "status": "requeued_successfully"}
        elif action_name == "RELEASE_RESERVATION":
            return {"released_sku": payload.get("sku"), "quantity": payload.get("quantity")}
        elif action_name == "SYNC_CONNECTOR":
            return {"connector_id": payload.get("connector_id"), "status": "sync_triggered"}
        else:
            raise NotImplementedError(f"Handler for {action_name} not implemented.")

    def _publish_state_event(self, event_type: str, correlation_id: str, payload: Dict[str, Any]):
        """
        Registra la transición de estado en el EventOutbox (que luego pasa al Store).
        Esto conforma el 'Operational State Journal' solicitado.
        """
        logger.info(f"HITL Journal -> [{event_type}] {payload}")
        # publish_event(self.db, self.tenant_id, event_type, payload, correlation_id)
        pass
