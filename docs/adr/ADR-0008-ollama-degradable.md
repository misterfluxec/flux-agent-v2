# ADR-0008: Ollama como dependencia degradable (no-bloqueante)

- **Status**: Accepted
- **Date**: 2026-05-16
- **Context**: Ollama puede tardar varios minutos en cargar modelos al inicio.
  Si el readiness check bloquea en Ollama, el backend no levanta hasta que
  Ollama esté listo, bloqueando la disponibilidad de toda la API.
- **Decision**: Ollama es una dependencia `degraded-safe`:
  - El readiness check reporta `ollama: degraded` si no responde, pero el
    endpoint retorna 200 (ready) de todas formas.
  - Solo Postgres y Redis son dependencias bloqueantes para readiness.
  - Las rutas que necesitan Ollama manejan su propia lógica de fallback.
- **Consequences**: El backend puede recibir requests de autenticación,
  governance y health aunque Ollama no esté listo. Las Conversations que
  requieren LLM retornan error específico de "LLM no disponible".
- **Do not re-suggest**: Hacer Ollama bloqueante en readiness.
  Esperar a Ollama en el lifespan de FastAPI.
