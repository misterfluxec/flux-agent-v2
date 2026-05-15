# Tech Debt Tracker — FluxAgent Enterprise Refactor

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

## Registrado en
- Paso 1.4 — 2026-05-14

## Prioridad Media (deuda arquitectónica)
- [ ] `social_auth.py` y `unified_oauth.py` comparten lógica
      `code → token → userinfo` duplicada. Extraer a `OAuth2Helper`
      compartido. (Paso 2.1 — aplazado por scope)
