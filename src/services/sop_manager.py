import json
import os
import logging
from typing import Dict, List, Optional
from src.domain.meta_agent import SOP, SOPStep, BaseRole, ActionCategory, AgentAction

logger = logging.getLogger(__name__)

class SOPManager:
    """
    Gestor de Procedimientos Estándar de Operación (SOPs) y Roles.
    Permite cargar y validar la gobernanza de los agentes.
    """
    def __init__(self, storage_path: str = "src/config/sops"):
        self.storage_path = storage_path
        self.roles: Dict[str, BaseRole] = {}
        self.sops: Dict[str, SOP] = {}
        
        # Crear directorio si no existe
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

    def register_role(self, role: BaseRole):
        self.roles[role.id] = role
        logger.info(f"[SOPManager] Rol registrado: {role.name}")

    def register_sop(self, sop: SOP):
        self.sops[sop.id] = sop
        logger.info(f"[SOPManager] SOP registrado: {sop.name} (v{sop.version})")

    def get_sop_for_role(self, role_id: str, trigger: str) -> Optional[SOP]:
        role = self.roles.get(role_id)
        if not role:
            return None
        
        for sop_id in role.assigned_sops:
            sop = self.sops.get(sop_id)
            if sop and any(t in trigger.lower() for t in sop.trigger_conditions):
                return sop
        return None

    def create_default_sales_sop(self) -> SOP:
        """SOP de ejemplo para Ventas en LATAM."""
        sop = SOP(
            name="Calificación y Cierre de Venta EC/CO",
            version="1.0",
            description="Procedimiento para calificar un lead y llevarlo al checkout.",
            trigger_conditions=["comprar", "precio", "pedido", "orden"],
            steps=[
                SOPStep(
                    order=1,
                    instruction="Verificar identidad del cliente y saludar profesionalmente.",
                    validation_criteria="Cliente identificado en DB.",
                    failure_protocol="Solicitar datos básicos (nombre/email)."
                ),
                SOPStep(
                    order=2,
                    instruction="Consultar disponibilidad de producto en catálogo.",
                    required_action="get_catalog_item",
                    validation_criteria="Producto existe y tiene stock.",
                    failure_protocol="Ofrecer alternativas similares."
                ),
                SOPStep(
                    order=3,
                    instruction="Generar link de pago o pre-orden.",
                    required_action="create_draft_order",
                    validation_criteria="Orden creada en el ERP.",
                    failure_protocol="Informar error técnico y solicitar espera."
                )
            ]
        )
        return sop
