from enum import StrEnum

class AgentExecutionState(StrEnum):
    """
    Estados deterministas de la máquina de estados del Agente.
    Permite persistencia formal, replay y trazabilidad de los flujos del grafo.
    """
    RECEIVED = "RECEIVED"                  # Evento recibido
    SOP_RUNNING = "SOP_RUNNING"            # Evaluando paso del SOP actual
    TOOL_SELECTION = "TOOL_SELECTION"      # LLM decide (ToolIntent)
    TOOL_EXECUTION = "TOOL_EXECUTION"      # ToolRuntime ejecutando (Guards, etc)
    WAITING_APPROVAL = "WAITING_APPROVAL"  # Pausa: requiere Human-In-The-Loop
    DEBATING = "DEBATING"                  # Error -> CAMEL resolviendo
    RETRYING = "RETRYING"                  # Reintento tras fallo transitorio
    REPLAYING = "REPLAYING"                # Ejecutando replay histórico
    QUARANTINED = "QUARANTINED"            # Puesto en cuarentena por seguridad/riesgo
    HUMAN_HANDOFF = "HUMAN_HANDOFF"        # Escalado irreversible a operador
    COMPLETED = "COMPLETED"                # Flujo terminado con éxito
    FAILED = "FAILED"                      # Flujo roto/imposible recuperar
    CANCELLED = "CANCELLED"                # Flujo abortado intencionalmente
