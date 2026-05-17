from pydantic import BaseModel, Field
from typing import Optional

class GraphEdge(BaseModel):
    """
    Define una transición (borde) entre dos nodos del ExecutionGraph.
    Desacopla la lógica de transición del nodo en sí.
    """
    source: str = Field(..., description="ID del nodo origen")
    target: str = Field(..., description="ID del nodo destino")
    condition: Optional[str] = Field(None, description="Condición de resultado que debe cumplir el source para activar este edge (ej: 'success')")
    priority: int = Field(default=0, description="Prioridad de evaluación. Mayor priority se evalúa antes.")
    timeout_ms: Optional[int] = Field(None, description="Timeout específico para esta transición")
    compensation_handler: Optional[str] = Field(None, description="Handler de compensación si la transición o el target fallan")
