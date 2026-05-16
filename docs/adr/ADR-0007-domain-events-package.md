# ADR-0007: domain/events/ como paquete, no módulo plano

- **Status**: Accepted
- **Date**: 2026-05-16
- **Context**: Existía una colisión entre `src/domain/events.py` (módulo plano)
  y `src/domain/events/` (directorio con submódulos). Python resolvía la
  importación de forma ambigua dependiendo del intérprete y del PYTHONPATH.
- **Decision**: `domain/events.py` fue movido a `domain/events/__init__.py`.
  Todo lo que estaba en el módulo plano es ahora el contenido del `__init__`
  del paquete. Los submódulos (e.g., `action_governance`) viven como archivos
  dentro del directorio.
- **Consequences**: `from domain.events import X` sigue funcionando.
  `from domain.events.action_governance import ActionGovernanceRegistry`
  también funciona. Sin ambigüedad.
- **Do not re-suggest**: Volver al módulo plano. Crear nuevos módulos planos
  que colisionen con directorios del mismo nombre.
