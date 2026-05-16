# ADR-0002: Redis singleton pool via app.state

- **Status**: Accepted
- **Date**: 2026-05-14
- **Context**: Crear una conexión Redis por request (`from_url()` en cada
  handler) es costoso y agota el pool bajo carga.
- **Decision**: Un único cliente Redis se crea en el `lifespan` de FastAPI
  y se expone via `request.app.state.redis`. Los módulos que necesitan Redis
  lo reciben como parámetro, nunca lo instancian internamente.
- **Consequences**: PlanManager, PolicyEngine, HITLEngine y OperationalHealthEngine
  reciben `redis` en su constructor o método principal.
- **Do not re-suggest**: Redis.from_url() por request, o Redis global sin pool.
