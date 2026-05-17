# =============================================================================
# FLUXAGENT V2 — REGISTRO DE PLANTILLAS DE AGENTES
# =============================================================================
# Gestión, carga y renderizado de prompts dinámicos.
# Implementa cache y validación de contrato de variables.
# =============================================================================

import os
import yaml
import logging
from typing import Dict, Any, Optional, List
from jinja2 import Environment, FileSystemLoader, select_autoescape, Template
from pydantic import BaseModel, create_model

logger = logging.getLogger(__name__)

class TemplateContract(BaseModel):
    name: str
    version: str
    description: str
    required_variables: List[str]
    defaults: Dict[str, Any] = {}
    model_settings: Dict[str, Any] = {}

class TemplateRegistry:
    """
    Orquestador de plantillas que asegura que cada agente sea creado 
    bajo un contrato estricto de variables y prompts.
    """
    
    def __init__(self, templates_root: str):
        self.root = templates_root
        self.env = Environment(
            loader=FileSystemLoader(templates_root),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self._cache_schemas: Dict[str, TemplateContract] = {}
        self._cache_models: Dict[str, Any] = {} # Modelos Pydantic dinámicos

    def _get_schema_path(self, agent_type: str) -> str:
        return os.path.join(self.root, agent_type, "schema.yaml")

    def _get_template_path(self, agent_type: str) -> str:
        return f"{agent_type}/base.jinja2"

    def load_schema(self, agent_type: str) -> TemplateContract:
        """Carga y cachea el schema de un type de agente."""
        if agent_type in self._cache_schemas:
            return self._cache_schemas[agent_type]
            
        path = self._get_schema_path(agent_type)
        if not os.path.exists(path):
            logger.error(f"Schema no encontrado para type: {agent_type} en {path}")
            raise FileNotFoundError(f"No existe configuración para el type de agente: {agent_type}")
            
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            schema = TemplateContract(**data)
            self._cache_schemas[agent_type] = schema
            return schema

    def validate_input(self, agent_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida que los datos de entrada cumplan con el contrato del schema.
        Aplica valores por defecto si faltan variables opcionales.
        """
        schema = self.load_schema(agent_type)
        
        # Crear model dinámico para validación si no existe en cache
        if agent_type not in self._cache_models:
            fields = {var: (Any, ...) for var in schema.required_variables}
            # Añadir variables con defaults
            for var, default in schema.defaults.items():
                if var not in fields:
                    fields[var] = (Any, default)
            
            self._cache_models[agent_type] = create_model(f"{agent_type.capitalize()}Input", **fields)

        # Validar y retornar datos limpios
        validator = self._cache_models[agent_type]
        validated = validator(**data)
        return validated.model_dump()

    def render(self, agent_type: str, context: Dict[str, Any]) -> str:
        """
        Renderiza la plantilla final inyectando el contexto validado.
        """
        try:
            # Asegurar que el input es válido antes de renderizar
            clean_context = self.validate_input(agent_type, context)
            
            template_path = self._get_template_path(agent_type)
            template = self.env.get_template(template_path)
            
            return template.render(**clean_context).strip()
        except Exception as e:
            logger.error(f"Error renderizando plantilla para {agent_type}: {e}")
            raise RuntimeError(f"Error al generar el prompt del agente: {str(e)}")

    def get_all_types(self) -> List[str]:
        """Retorna todos los tipos de agentes disponibles (carpetas en root)."""
        return [d for d in os.listdir(self.root) if os.path.isdir(os.path.join(self.root, d))]
