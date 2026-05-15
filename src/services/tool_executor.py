import logging
from typing import Dict, Any, Optional
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from domain.tools import ToolDefinition
from core.exceptions import BusinessRuleError

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
        """Exporta las herramientas al formato JSON Schema que espera Ollama/OpenAI."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema.model_json_schema(),
                },
            }
            for tool in self._tools.values()
        ]

    async def execute(
        self,
        name: str,
        payload: dict,
        tenant_id: str,
        db: Optional[AsyncSession] = None,
    ) -> Any:
        """
        Ejecuta una herramienta registrada.

        db: AsyncSession inyectada desde el caller (router / orchestrator).
        Si no se provee, la herramienta se ejecuta sin sesión DB — válido
        para herramientas que no necesitan persistencia.
        """
        try:
            tool = self.get_tool(name)
        except ValueError as e:
            return {"status": "error", "message": str(e)}

        try:
            input_data = tool.input_schema(**payload)
        except ValidationError as e:
            logger.warning(f"Error de validación en {name}: {e}")
            return {"status": "error", "message": f"Parámetros inválidos para {name}: {e}"}

        try:
            result = await tool.handler(input_data, tenant_id, db)
            return {"status": "success", "result": result}
        except BusinessRuleError as e:
            logger.warning(f"Regla de negocio no cumplida en {name}: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"Error interno ejecutando {name}: {e}", exc_info=True)
            return {"status": "error", "message": f"Error interno del sistema: {str(e)}"}
