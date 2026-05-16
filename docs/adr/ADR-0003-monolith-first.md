# ADR-0003: Monolito primero — sin microservicios

- **Status**: Accepted
- **Date**: 2026-05-14
- **Context**: FluxAgent está en etapa de product-market fit. Separar en
  microservicios antes de tener carga real añade complejidad operacional sin
  beneficio medible.
- **Decision**: Un único proceso FastAPI con workers Dramatiq en paralelo.
  Los módulos se desacoplan via seams (interfaces) internos, no via red.
  EventBus es in-process, no un broker externo.
- **Consequences**: Despliegue simple (docker-compose). Escalado vertical
  primero. Dramatiq workers escalan horizontalmente como procesos separados
  del mismo codebase.
- **Do not re-suggest**: Separar PolicyEngine, HITLEngine o AgentRegistry
  en servicios independientes hasta tener > 10k tenants activos.
