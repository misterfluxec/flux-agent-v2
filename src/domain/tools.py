from enum import Enum
from typing import Callable, Any, Type
from pydantic import BaseModel

class ToolCategory(str, Enum):
    COMMERCE = "commerce"
    CRM = "crm"
    SUPPORT = "support"
    UTILITY = "utility"

class ToolDefinition(BaseModel):
    name: str
    category: ToolCategory
    description: str
    input_schema: Type[BaseModel]
    handler: Callable
    is_dangerous: bool = False
