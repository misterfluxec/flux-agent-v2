"""
Ollama SOP Prompting Engine (Sprint C.2 - Fortress Path v2.6)
=============================================================
Construye system prompts optimizados que OBLIGAN a los modelos
locales de Ollama a adherirse estrictamente al SOP cargado.

Principio: El modelo no puede inventar pasos. Solo puede ejecutar
los definidos en el SOP o escalar al siguiente nivel.
"""
from typing import Optional, List
from domain.meta_agent import SOP, SOPStep, BaseRole


class SOPPromptBuilder:
    """
    Construye system prompts estructurados para modelos Ollama.
    Garantiza adherencia estricta al SOP activo.
    """

    @staticmethod
    def build_system_prompt(role: BaseRole, sop: Optional[SOP] = None) -> str:
        """
        Genera el system prompt base para un rol dado.
        Si hay un SOP activo, lo inyecta como mandato estructurado.
        """
        header = f"""## ROL ASIGNADO: {role.name}
{role.profile}

### TUS OBJETIVOS:
{chr(10).join(f'- {g}' for g in role.goals)}

### RESTRICCIONES ABSOLUTAS:
{chr(10).join(f'- {c}' for c in role.constraints)}
"""

        sop_block = ""
        if sop:
            sop_block = SOPPromptBuilder.build_sop_block(sop)

        enforcement = """
### PROTOCOLO DE COMPORTAMIENTO (OBLIGATORIO):
1. SIEMPRE seguir los pasos del procedimiento en orden exacto.
2. NUNCA saltarte un paso ni inventar acciones no definidas.
3. Si un paso falla, ejecutar el protocolo de falla definido para ese paso.
4. Si la solicitud está fuera del alcance del procedimiento, responder:
   "Esta solicitud requiere derivación a un especialista."
5. Responder siempre en el idioma del cliente.
6. Ser conciso, profesional y orientado a resultados.
"""

        return header + sop_block + enforcement

    @staticmethod
    def build_sop_block(sop: SOP) -> str:
        """Convierte un SOP en un bloque de instrucciones para el prompt."""
        lines = [
            f"\n### PROCEDIMIENTO ACTIVO: {sop.name} (v{sop.version})",
            f"**Descripción**: {sop.description}",
            "\n**PASOS A SEGUIR EN ESTE ORDEN ESTRICTO:**",
        ]
        for step in sorted(sop.steps, key=lambda s: s.order):
            lines.append(f"\n**Paso {step.order}**: {step.instruction}")
            if step.required_action:
                lines.append(f"  - Acción requerida: `{step.required_action}`")
            lines.append(f"  - Criterio de éxito: {step.validation_criteria}")
            lines.append(f"  - Si falla: {step.failure_protocol}")

        lines.append("\n**IMPORTANTE**: No procedas al siguiente paso hasta completar el anterior.")
        return "\n".join(lines)

    @staticmethod
    def build_step_prompt(step: SOPStep, context: dict) -> str:
        """
        Genera el prompt para un paso específico del SOP,
        inyectando el contexto actual del negocio.
        """
        ctx_lines = [f"- {k}: {v}" for k, v in context.items()]
        return f"""Estás ejecutando el **Paso {step.order}** del procedimiento activo.

**Instrucción**: {step.instruction}
**Criterio de éxito**: {step.validation_criteria}
**Protocolo si falla**: {step.failure_protocol}

**Contexto actual del negocio**:
{chr(10).join(ctx_lines)}

Ejecuta este paso y reporta el resultado. Si no puedes completarlo,
activa el protocolo de falla indicado. NO avances al siguiente paso por tu cuenta."""

    @staticmethod
    def build_exception_prompt(failed_step: SOPStep, error_description: str) -> str:
        """
        Prompt especial para manejar excepciones fuera del SOP estándar.
        Activa el modo de razonamiento crítico (CAMEL Layer hook).
        """
        return f"""⚠️ EXCEPCIÓN DETECTADA EN PASO {failed_step.order}

**Error**: {error_description}
**Paso fallido**: {failed_step.instruction}
**Protocolo estándar**: {failed_step.failure_protocol}

El protocolo estándar no es suficiente para resolver esta situación.
Activa el modo de RAZONAMIENTO CRÍTICO:
1. Identifica la causa raíz del problema.
2. Propón una solución dentro de tus capacidades de rol.
3. Si está fuera de tu alcance, propón derivación a: [ESPECIALISTA REQUERIDO].
4. Documenta tu razonamiento completo.

¿Cuál es tu análisis y recomendación?"""
