# ADR-0004: ActionGovernanceRegistry como registro central de políticas de acción

- **Status**: Accepted
- **Date**: 2026-05-15
- **Context**: Múltiples módulos necesitaban decidir si una acción operativa
  (ISSUE_REFUND, CANCEL_ORDER, etc.) requiere aprobación humana. Sin un
  registro central, esta lógica se duplicaría en cada módulo.
- **Decision**: `ActionGovernanceRegistry` es el único lugar donde se definen
  los `ActionPolicy` objetos. Si una acción no está registrada ahí, el
  `HITLEngine` la bloquea automáticamente. `sysadmin` es el único rol que
  bypasea cualquier política.
- **Consequences**: Añadir una nueva acción operativa = una sola línea en
  `action_governance.py`. El HITLEngine y los tests de gobernanza no cambian.
- **Do not re-suggest**: Lógica de aprobación hardcoded en routers o services.
  Roles de aprobación en variables de entorno.
