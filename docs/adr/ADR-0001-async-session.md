# ADR-0001: Async-First — AsyncSession en todo el pipeline operativo

- **Status**: Accepted
- **Date**: 2026-05-14
- **Context**: El servidor usa FastAPI con event loop único. Cualquier llamada
  síncrona a la DB (`SessionLocal()`) bloquea el loop bajo carga.
- **Decision**: Todo acceso a PostgreSQL en el path de request usa
  `AsyncSession` de SQLAlchemy. Los workers Dramatiq pueden usar sesiones
  síncronas porque corren en threads separados.
- **Consequences**: 4 servicios legacy (payment_reconciliation, reservation,
  customer_timeline, outbox_dispatcher) aún usan `SessionLocal` síncrono —
  registrado en TECH_DEBT.md como prioridad alta.
- **Do not re-suggest**: Volver a sesiones síncronas en routers o services.
