from langchain.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import asyncio

# Modelos de entrada para las herramientas
class ProductSearchInput(BaseModel):
    query: str = Field(description="Término de búsqueda del producto")
    category: str = Field(default="", description="Categoría opcional")

class PaymentInput(BaseModel):
    amount: float = Field(description="Monto a cobrar")
    currency: str = Field(default="USD", description="Moneda")
    description: str = Field(description="Descripción del pago")

class InventoryInput(BaseModel):
    sku: str = Field(description="SKU del producto")

class AppointmentInput(BaseModel):
    date: str = Field(description="Fecha propuesta (YYYY-MM-DD)")
    time: str = Field(description="Hora propuesta (HH:MM)")
    client_name: str = Field(description="Nombre del cliente")

class OrderStatusInput(BaseModel):
    order_id: str = Field(description="ID del pedido")

# --- Herramientas ---

class SearchProductsTool(BaseTool):
    name = "search_products"
    description = "Busca productos en el catálogo por nombre o categoría."
    args_schema: Type[BaseModel] = ProductSearchInput

    def _run(self, query: str, category: str = "") -> str:
        # TODO: Conectar con tu servicio real de productos (Shopify/WooCommerce)
        # Simulación para ahora:
        return f"Encontrados productos similares a '{query}': Producto A ($100), Producto B ($150)."

    async def _arun(self, query: str, category: str = "") -> str:
        return self._run(query, category)

class GeneratePaymentLinkTool(BaseTool):
    name = "generate_payment_link"
    description = "Genera un link de pago seguro (Stripe/Shopify) para cerrar la venta."
    args_schema: Type[BaseModel] = PaymentInput

    def _run(self, amount: float, currency: str, description: str) -> str:
        # TODO: Integrar con Stripe API o Shopify Payment API
        link = f"https://pay.tuempresa.com/checkout?amt={amount}&curr={currency}&desc={description}"
        return f"Link de pago generado: {link}"

    async def _arun(self, amount: float, currency: str, description: str) -> str:
        return self._run(amount, currency, description)

class CheckInventoryTool(BaseTool):
    name = "check_inventory"
    description = "Verifica stock disponible de un producto por SKU."
    args_schema: Type[BaseModel] = InventoryInput

    def _run(self, sku: str) -> str:
        # TODO: Conectar con inventario real
        return f"SKU {sku}: 15 unidades disponibles. (Stock bajo: <5)"

    async def _arun(self, sku: str) -> str:
        return self._run(sku)

class ScheduleAppointmentTool(BaseTool):
    name = "schedule_appointment"
    description = "Agenda una cita o demo con el cliente."
    args_schema: Type[BaseModel] = AppointmentInput

    def _run(self, date: str, time: str, client_name: str) -> str:
        # TODO: Conectar con Google Calendar o Calendly
        return f"Cita agendada para {client_name} el {date} a las {time}. Se envió confirmación."

    async def _arun(self, date: str, time: str, client_name: str) -> str:
        return self._run(date, time, client_name)

class GetOrderStatusTool(BaseTool):
    name = "get_order_status"
    description = "Consulta el estado de envío de un pedido."
    args_schema: Type[BaseModel] = OrderStatusInput

    def _run(self, order_id: str) -> str:
        # TODO: Conectar con API de envíos
        return f"Pedido {order_id}: En tránsito. Llegada estimada: 2 días."

    async def _arun(self, order_id: str) -> str:
        return self._run(order_id)

# Lista de herramientas para exportar
SALES_TOOLS = [
    SearchProductsTool(),
    GeneratePaymentLinkTool(),
    CheckInventoryTool(),
    ScheduleAppointmentTool(),
    GetOrderStatusTool()
]
