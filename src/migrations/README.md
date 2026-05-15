# Migraciones FluxAgent

Ejecutar en orden numérico contra PostgreSQL.
Cada archivo es idempotente (usa IF NOT EXISTS).

Ejecutar:
  psql $DATABASE_URL -f src/migrations/001_policies_table.sql