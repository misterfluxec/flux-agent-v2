from pydantic import BaseModel, Field
from typing import Optional, Literal

class ProductCapabilities(BaseModel):
    """
    Define el comportamiento operativo del producto. El Motor de Negocio lee esto, no el 'type'.
    """
    requires_inventory: bool = Field(default=False, description="¿Se debe gestionar stock?")
    requires_shipping: bool = Field(default=False, description="¿Requiere logística de envío?")
    requires_appointment: bool = Field(default=False, description="¿Requiere agendar cita?")
    
    # Campos condicionales (opcionales, dependientes de los flags de arriba)
    duration_minutes: Optional[int] = Field(default=None, ge=15, description="Duración del servicio en minutos")
    stock_quantity: Optional[int] = Field(default=None, ge=0, description="Cantidad actual en stock")
    resource_type: Optional[Literal['human', 'room', 'equipment']] = Field(default=None)

    # Para suscripciones (futuro)
    is_subscription: bool = Field(default=False)
    subscription_cycle: Optional[Literal['monthly', 'yearly']] = Field(default=None)
    
    class Config:
        extra = 'forbid' # Bloquear campos extra para seguridad
