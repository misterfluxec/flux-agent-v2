from typing import List, Dict, Any, Callable, Awaitable
from pydantic import BaseModel, Field

class GraphNode(BaseModel):
    """
    Define un nodo dentro del ExecutionGraph.
    Ahora actúa solo como una unidad de ejecución; las transiciones se definen en GraphEdge.
    """
    id: str = Field(..., description="Identificador único del nodo")
    handler_name: str = Field(..., description="Nombre del handler o función a ejecutar")
