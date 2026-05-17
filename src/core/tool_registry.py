from domain.tools import ToolDefinition, ToolCategory
from services.tools.commerce_tools import (
    CheckAvailabilityInput, CreateQuoteInput, CreateOrderInput,
    check_availability, create_quote, create_order
)

TOOL_CHECK_AVAILABILITY = ToolDefinition(
    name="check_availability",
    category=ToolCategory.COMMERCE,
    description="Verifica stock y disponibilidad de slots en tiempo real",
    input_schema=CheckAvailabilityInput,
    handler=check_availability,
    is_dangerous=False
)

TOOL_CREATE_QUOTE = ToolDefinition(
    name="create_quote",
    category=ToolCategory.COMMERCE,
    description="Genera cotización formal con cálculo financiero y link público",
    input_schema=CreateQuoteInput,
    handler=create_quote,
    is_dangerous=True
)

TOOL_CREATE_ORDER = ToolDefinition(
    name="create_order",
    category=ToolCategory.COMMERCE,
    description="Crea sort_order de venta validando cotización o ítems directos",
    input_schema=CreateOrderInput,
    handler=create_order,
    is_dangerous=True
)

COMMERCE_TOOLS = [TOOL_CHECK_AVAILABILITY, TOOL_CREATE_QUOTE, TOOL_CREATE_ORDER]
