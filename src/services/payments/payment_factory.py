from typing import Dict, Any, Type
from services.payments.base import PaymentGatewayInterface
from services.payments.mercadopago_provider import MercadoPagoProvider
from services.payments.payphone_provider import PayPhoneProvider

class PaymentFactory:
    _providers: Dict[str, Type[PaymentGatewayInterface]] = {
        "mercadopago": MercadoPagoProvider,
        "payphone": PayPhoneProvider,
        # "stripe": StripeProvider,
    }

    @classmethod
    def get_provider(cls, provider_name: str) -> PaymentGatewayInterface:
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Proveedor de pagos no soportado: {provider_name}")
        return provider_class()
