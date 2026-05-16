# ADR-0005: PolicyEngine con cache en memoria por tenant:tool

- **Status**: Accepted
- **Date**: 2026-05-15
- **Context**: El PolicyEngine evalúa reglas en cada Tool invocation.
  Consultar PostgreSQL por cada invocación añadiría 10-50ms de latencia
  con carga concurrente.
- **Decision**: `PolicyEngine` mantiene un cache en memoria (`dict[str, list[PolicyRule]]`)
  keyed por `tenant_id:tool_name`. El cache se invalida al crear o modificar
  una regla via `create_rule()`. La regla default-allow tiene `priority=1`
  (mínimo válido por el esquema Pydantic).
- **Consequences**: Cache no es distribuido — en multi-instancia, cada
  instancia tiene su propio cache. Aceptable hasta escalar horizontalmente.
  Tiempo de convergencia: hasta el próximo restart o `create_rule()`.
- **Do not re-suggest**: Redis como cache para PolicyEngine hasta tener
  multi-instancia real. Cache persistente entre restarts.
