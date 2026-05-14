from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import random

logger = logging.getLogger(__name__)

class FeatureFlag(BaseModel):
    name: str
    enabled_for_tenants: List[str] = []
    enabled_for_countries: List[str] = []
    rollout_percentage: int = 0  # 0 to 100

class FeatureFlagManager:
    """
    Gestiona el despliegue progresivo de nuevas capacidades (ej. nuevos modelos LLM, 
    nuevos debates) sin requerir despliegues completos.
    """
    
    def __init__(self):
        # In memory for now, to be backed by Redis or DB
        self._flags: Dict[str, FeatureFlag] = {}

    def set_flag(self, flag: FeatureFlag):
        """Configura un flag en el sistema."""
        self._flags[flag.name] = flag
        logger.debug(f"[FeatureFlag] Flag {flag.name} updated: rollout={flag.rollout_percentage}%")

    def is_enabled(self, flag_name: str, tenant_id: str = None, country_code: str = None) -> bool:
        """
        Verifica si una feature está encendida considerando:
        1. Tenant específico (ej. Beta testers)
        2. País (ej. Lanzamiento escalonado en MX)
        3. Porcentaje aleatorio (Canary releases)
        """
        flag = self._flags.get(flag_name)
        if not flag:
            return False # Default secure: disable if unknown

        # 1. Exact match for tenant
        if tenant_id and tenant_id in flag.enabled_for_tenants:
            return True

        # 2. Exact match for country
        if country_code and country_code in flag.enabled_for_countries:
            return True

        # 3. Rollout percentage (Canary)
        # En producción real se hace hash(tenant_id) % 100 para que sea consistente
        if flag.rollout_percentage > 0:
            if tenant_id:
                # Hash determinista para el mismo tenant
                hash_val = sum(ord(c) for c in str(tenant_id)) % 100
                if hash_val < flag.rollout_percentage:
                    return True
            else:
                # Random si no hay tenant
                if random.randint(0, 99) < flag.rollout_percentage:
                    return True

        return False
