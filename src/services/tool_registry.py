from pydantic import BaseModel
from typing import Callable, Type, Dict, Any, Optional
from enum import Enum

class ToolCategory(Enum):
    CRM = "crm"
    INVENTORY = "inventory"
    BILLING = "billing"
    CHANNEL = "channel"
    SYSTEM = "system"

class ToolDefinition(BaseModel):
    name: str
    category: ToolCategory
    description: str
    input_schema: Type[BaseModel]
    handler: Callable
    required_permission: str = "execute_tool"
    is_dangerous: bool = False  # Requiere confirmación humana si es True
