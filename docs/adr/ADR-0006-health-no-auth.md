# ADR-0006: Health checks sin autenticación en /health/live y /health/ready

- **Status**: Accepted
- **Date**: 2026-05-16
- **Context**: Docker necesita hacer probes de liveness/readiness al backend.
  El endpoint `/api/v1/health/operational` requiere JWT — Docker no puede
  obtener un token. Los probes fallarían siempre.
- **Decision**: Dos endpoints sin auth:
  - `GET /health/live` — solo verifica que el proceso está vivo. Siempre 200.
  - `GET /health/ready` — verifica Postgres (bloqueante) + Redis (bloqueante)
    + Ollama (no-bloqueante, degraded-safe). Retorna 503 si DB o Redis fallan.
  El endpoint operacional con métricas de negocio sigue requiriendo JWT.
- **Consequences**: Cualquier proceso en la misma red puede acceder a /health/*.
  Aceptable porque no expone datos sensibles — solo status booleanos.
- **Do not re-suggest**: JWT en health checks de infraestructura. Ollama como
  dependencia bloqueante para readiness.
