from domain.events.registry import EventRegistry

class ReplaySafetyEnforcer:
    """
    Fase 4B — Sprint 4B.3: Replay Safety Enforcement.
    
    Actúa como un gatekeeper antes de permitir cualquier operación de replay
    desde el DLQ & Retry Center. 
    Verifica contra la "constitución" del EventRegistry.
    """

    @staticmethod
    def assert_replay_safe(event_type: str) -> bool:
        """
        Verifica si un evento es seguro para ser reintentado.
        Lanza excepción si viola la política.
        """
        definition = EventRegistry.get_definition(event_type)
        if not definition:
            # Eventos no registrados no pueden ser reintentados por seguridad
            raise ValueError(f"Replay rejected: Event '{event_type}' is not registered in EventRegistry.")
        
        if not definition.replayable:
            raise ValueError(
                f"Replay rejected: Event '{event_type}' is explicitly marked as NON_REPLAYABLE "
                f"due to its failure_type ({definition.failure_type.value}). "
                "Manual intervention is required."
            )
            
        return True
