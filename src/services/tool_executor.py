import logging
from typing import Dict, Any, Callable
from pydantic import ValidationError
from domain.tools import ToolDefinition
from core.exceptions import BusinessRuleError
from database import SesionLocal

logger = logging.getLogger(__name__)

class ToolExecutor:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        self._tools[tool.name] = tool
        logger.info(f"Registrada herramienta: {tool.name}")

    def get_tool(self, name: str) -> ToolDefinition:
        if name not in self._tools:
            raise ValueError(f"Herramienta {name} no registrada")
        return self._tools[name]
        
    def get_all_tools_schema(self) -> list:
        # Exporta las herramientas al formato JSON Schema que espera Ollama/OpenAI
        schemas = []
        for tool in self._tools.values():
            schema = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema.model_json_schema()
                }
            }
            schemas.append(schema)
        return schemas

    async def execute(self, name: str, payload: dict, tenant_id: str) -> Any:
        try:
            tool = self.get_tool(name)
        except ValueError as e:
            return {"status": "error", "message": str(e)}

        try:
            # Validación con Pydantic v2
            input_data = tool.input_schema(**payload)
        except ValidationError as e:
            logger.warning(f"Error de validación en {name}: {e}")
            return {"status": "error", "message": f"Parámetros inválidos para {name}: {e}"}

        try:
            # Ejecutar con base de datos real (inyección de sesión)
            async with SesionLocal() as db:
                async with db.begin():
                    result = await tool.handler(input_data, tenant_id, db)
                    return {"status": "success", "result": result}
        except BusinessRuleError as e:
            logger.warning(f"Regla de negocio no cumplida en {name}: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"Error interno ejecutando {name}: {e}", exc_info=True)
            return {"status": "error", "message": f"Error interno del sistema: {str(e)}"}
