from pydantic import BaseModel
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ActionPolicy(BaseModel):
    """
    Política estricta que gobierna una acción operativa (Fase 5A).
    """
    action_name: str
    requires_approval: bool = True
    allowed_roles: List[str]
    max_per_hour_per_tenant: int = 50
    audit_required: bool = True
    description: str

class ActionGovernanceRegistry:
    """
    Registro central de gobernanza de acciones operacionales.
    Si una acción sugerida por IA no está aquí, el HITL Engine la bloquea.
    """
    
    _policies: Dict[str, ActionPolicy] = {}

    @classmethod
    def register(cls, policy: ActionPolicy):
        if policy.action_name in cls._policies:
            raise ValueError(f"Action Policy {policy.action_name} is already registered.")
        cls._policies[policy.action_name] = policy

    @classmethod
    def get_policy(cls, action_name: str) -> Optional[ActionPolicy]:
        return cls._policies.get(action_name)

    @classmethod
    def can_user_execute(cls, action_name: str, user_roles: List[str]) -> bool:
        """Verifica si el usuario (humano) tiene permiso para aprobar/ejecutar esta acción."""
        policy = cls.get_policy(action_name)
        if not policy:
            logger.error(f"Action {action_name} attempted but not found in Governance Registry.")
            return False
            
        # Para sysadmins, siempre es True.
        if "sysadmin" in user_roles:
            return True
            
        # Verificar intersección de roles
        has_permission = any(role in policy.allowed_roles for role in user_roles)
        
        if not has_permission:
            logger.warning(f"User with roles {user_roles} denied execution of {action_name}.")
            
        return has_permission


# ==========================================
# CORE OPERATIONAL ACTIONS (Fase 5A Bootstrap)
# ==========================================

ActionGovernanceRegistry.register(ActionPolicy(
    action_name="REPLAY_WEBHOOK",
    requires_approval=True,
    allowed_roles=["operations_admin", "senior_support", "ai_operator"],
    max_per_hour_per_tenant=100,
    audit_required=True,
    description="Forzar reintento de un evento fallido desde el Outbox."
))

ActionGovernanceRegistry.register(ActionPolicy(
    action_name="RELEASE_RESERVATION",
    requires_approval=True,
    allowed_roles=["operations_admin", "inventory_manager", "ai_operator"],
    max_per_hour_per_tenant=20,
    audit_required=True,
    description="Forzar la liberación de inventario bloqueado por una reserva fantasma."
))

ActionGovernanceRegistry.register(ActionPolicy(
    action_name="SYNC_CONNECTOR",
    requires_approval=True,
    allowed_roles=["operations_admin", "ai_operator"],
    max_per_hour_per_tenant=5,
    audit_required=True,
    description="Forzar sincronización inmediata de un conector (ERP/Shopify)."
))

# ── Commerce ──────────────────────────────────────────
ActionGovernanceRegistry.register(ActionPolicy(
    action_name="ISSUE_REFUND",
    requires_approval=True,
    allowed_roles=["operations_admin", "finance_manager",
                   "ai_operator"],
    max_per_hour_per_tenant=30,
    audit_required=True,
    description="Emitir reembolso a un cliente. "
                "Toda reversión financiera requiere aprobación.",
))

ActionGovernanceRegistry.register(ActionPolicy(
    action_name="CANCEL_ORDER",
    requires_approval=True,
    allowed_roles=["operations_admin", "senior_support",
                   "ai_operator"],
    max_per_hour_per_tenant=50,
    audit_required=True,
    description="Cancelar una orden confirmada y liberar inventario.",
))

ActionGovernanceRegistry.register(ActionPolicy(
    action_name="APPLY_DISCOUNT",
    requires_approval=False,
    allowed_roles=["sales_agent", "operations_admin",
                   "ai_operator"],
    max_per_hour_per_tenant=200,
    audit_required=True,
    description="Aplicar descuento a una cotización o pedido.",
))

ActionGovernanceRegistry.register(ActionPolicy(
    action_name="OVERRIDE_PRICE",
    requires_approval=True,
    allowed_roles=["operations_admin", "finance_manager"],
    max_per_hour_per_tenant=20,
    audit_required=True,
    description="Sobrescribir precio de catálogo manualmente. "
                "Solo roles financieros senior.",
))

# ── Operaciones ────────────────────────────────────────
ActionGovernanceRegistry.register(ActionPolicy(
    action_name="ESCALATE_AGENT",
    requires_approval=False,
    allowed_roles=["sales_agent", "senior_support",
                   "operations_admin", "ai_operator"],
    max_per_hour_per_tenant=500,
    audit_required=True,
    description="Escalar conversación de IA a operador humano.",
))

ActionGovernanceRegistry.register(ActionPolicy(
    action_name="SEND_BULK_MESSAGE",
    requires_approval=True,
    allowed_roles=["operations_admin", "marketing_manager"],
    max_per_hour_per_tenant=5,
    audit_required=True,
    description="Enviar mensaje masivo a segmento de clientes. "
                "Límite estricto anti-spam.",
))

ActionGovernanceRegistry.register(ActionPolicy(
    action_name="MODIFY_AGENT_PROMPT",
    requires_approval=True,
    allowed_roles=["operations_admin", "ai_operator"],
    max_per_hour_per_tenant=10,
    audit_required=True,
    description="Modificar el prompt base o instrucciones de un agente. "
                "Cambios de comportamiento requieren revisión.",
))

ActionGovernanceRegistry.register(ActionPolicy(
    action_name="EXPORT_CUSTOMER_DATA",
    requires_approval=True,
    allowed_roles=["operations_admin", "compliance_officer"],
    max_per_hour_per_tenant=3,
    audit_required=True,
    description="Exportar datos de clientes. "
                "GDPR/LATAM compliance — máxima restricción.",
))
