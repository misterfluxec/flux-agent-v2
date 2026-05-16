# Tech Debt Tracker — FluxAgent Enterprise Refactor

## Prioridad Alta (seguridad)
- [ ] governance /approval/respond publica evento sin 
      verificar que correlation_id existe en estado 
      PENDING en DB. Añadir validación previa para 
      prevenir inyección de eventos huérfanos.

## Prioridad Alta (bloquean escala async)
- [ ] 4 servicios usan `with SessionLocal() as db` síncrono — 
      bloquean el event loop bajo carga:
      - payment_reconciliation_engine.py
      - reservation_engine.py  
      - customer_timeline_aggregator.py
      - event_outbox_dispatcher.py
      FIX: Convertir a `async with AsyncSession` o mover a workers Dramatiq

- [ ] 20 archivos con `from sqlalchemy.orm import Session` 
      como type hint incorrecto (son async en runtime)
      FIX: Cambiar import a AsyncSession en cada uno

## Prioridad Media (deuda arquitectónica)
- [ ] social_auth.py y unified_oauth.py comparten lógica
      code→token→userinfo duplicada. Extraer a OAuth2Helper
      compartido. (Paso 2.1 — aplazado)

- [ ] `check_plan_limits` decorator usa inspección de nombre 
      de función (frágil). Reemplazar por 
      `@requires_capability("create_agent")` explícito.

- [ ] `rate_limit/rules.py` aún tiene `plan_limits` local.
      Migrar `get_tenant_specific_rules()` para usar 
      `PlanManager` (requiere pasar redis+db al middleware).
- Paso 1.4 — 2026-05-14

## Prioridad Media (deuda arquitectónica)
- [ ] `social_auth.py` y `unified_oauth.py` comparten lógica
      `code → token → userinfo` duplicada. Extraer a `OAuth2Helper`
      compartido. (Paso 2.1 — aplazado por scope)

## Prioridad Baja (optimización)
- [ ] enterprise_router /ledger/balance usa SUM() manual.
      LedgerService ya tiene vista materializada customer_balances.
      Migrar para usar el servicio directamente.
