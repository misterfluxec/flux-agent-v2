from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

class PaymentGatewayInterface(ABC):
    @abstractmethod
    async def create_payment_link(self, order_id: str, amount: float, currency: str, description: str, tenant_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un enlace o preferencia de pago.
        Debe retornar un dict con al menos 'init_point' (la URL a la que redirigir al usuario).
        """
        pass

    @abstractmethod
    async def process_webhook(self, payload: Dict[str, Any], headers: Dict[str, str], tenant_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un webhook y verifica firmas/seguridad.
        Debe retornar un dict normalizado con:
        - status: 'approved' | 'rejected' | 'pending'
        - order_id: str
        - payment_id: str
        - payment_method: str
        """
        pass

    @abstractmethod
    async def refund_payment(self, payment_id: str, amount: float, tenant_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reembolsa un pago parcial o total.
        """
        pass
