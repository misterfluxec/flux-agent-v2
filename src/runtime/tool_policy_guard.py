from typing import Optional
from runtime.tool_intent import ToolIntent
from runtime.tool_contract import ToolContract

class PolicyGuardException(Exception):
    pass

class ToolPolicyGuard:
    """
    Valida si el intento de herramienta cumple con las políticas y roles antes de ser considerado.
    """
    
    def __init__(self, role_id: str):
        self.role_id = role_id

    def validate(self, intent: ToolIntent, contract: ToolContract) -> bool:
        """
        Devuelve True si cumple las políticas, lanza PolicyGuardException si no.
        """
        # 1. Validación de Roles
        if contract.allowed_roles:
            if self.role_id not in contract.allowed_roles:
                raise PolicyGuardException(f"Role '{self.role_id}' is not allowed to execute '{contract.id}'.")
                
        # 2. Validación de Montos (Ejemplo)
        if contract.max_amount_allowed is not None:
            amount = intent.extracted_parameters.get("amount")
            if amount is not None:
                try:
                    amount_float = float(amount)
                    if amount_float > contract.max_amount_allowed:
                        raise PolicyGuardException(f"Amount {amount_float} exceeds max allowed {contract.max_amount_allowed} for tool '{contract.id}'.")
                except ValueError:
                    raise PolicyGuardException(f"Invalid amount format: {amount}")
                    
        return True
