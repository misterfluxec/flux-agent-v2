from typing import Dict, Any, Type
from services.payments.base import PaymentGatewayInterface
from services.payments.mercadopago_provider import MercadoPagoProvider

class PaymentFactory:
    _providers: Dict[str, Type[PaymentGatewayInterface]] = {
        "mercadopago": MercadoPagoProvider,
        # "payphone": PayPhoneProvider, # Para futuras expansiones
        # "stripe": StripeProvider,
    }

    @classmethod
    def get_provider(cls, provider_name: str) -> PaymentGatewayInterface:
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Proveedor de pagos no soportado: {provider_name}")
        return provider_class()
