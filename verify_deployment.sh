#!/bin/bash
# =============================================================================
# FLUXAGENT V2 - VERIFICACIÓN POST-DESPLIEGUE
# =============================================================================

echo "========================================"
echo " VERIFICACIÓN POST-DESPLIEGUE"
echo "========================================"
echo ""

PASS=0
FAIL=0

check() {
    if [ $? -eq 0 ]; then
        echo "  ✅ $1"
        ((PASS++))
    else
        echo "  ❌ $1"
        ((FAIL++))
    fi
}

# 1. Verificar que el servicio está corriendo
echo "[1/8] Verificando servicio backend..."
curl -s http://localhost:9000/docs > /dev/null 2>&1
check "Backend responding"

# 2. Verificar conexión a PostgreSQL
echo "[2/8] Verificando PostgreSQL..."
pg_isready -h localhost -p 5434 -U fluxadmin > /dev/null 2>&1
check "PostgreSQL disponible"

# 3. Verificar conexión a Redis
echo "[3/8] Verificando Redis..."
redis-cli -h localhost -p 6381 -a redisflux2026 ping > /dev/null 2>&1
check "Redis disponible"

# 4. Verificar tablas de planes
echo "[4/8] Verificando tablas de planes..."
psql -h localhost -p 5434 -U fluxadmin -d fluxagent_v2 -t -c "SELECT COUNT(*) FROM plans;" > /dev/null 2>&1
check "Tabla plans existe"

# 5. Verificar features en tenants
echo "[5/8] Verificando features en tenants..."
psql -h localhost -p 5434 -U fluxadmin -d fluxagent_v2 -t -c "SELECT COUNT(*) FROM tenants WHERE features IS NOT NULL;" > /dev/null 2>&1
check "Tenants tienen features"

# 6. Verificar endpoint de modelos
echo "[6/8] Verificando endpoint de modelos..."
curl -s http://localhost:9000/api/v1/admin/models > /dev/null 2>&1
check "Endpoint /admin/models"

# 7. Verificar WebSocket voice
echo "[7/8] Verificando endpoint WebSocket..."
curl -s -I "http://localhost:9000/api/v1/voice/stream/test/test" > /dev/null 2>&1
check "Endpoint /voice/stream"

# 8. Verificar config LLM
echo "[8/8] Verificando configuración LLM..."
grep -q "llm_mode" /home/mister/flux-agent-v2/src/config.py
check "Config LLM presente"

echo ""
echo "========================================"
echo " RESULTADOS: $PASS ✅ | $FAIL ❌"
echo "========================================"

if [ $FAIL -eq 0 ]; then
    echo ""
    echo "🎉 ¡Despliegue exitoso!"
    exit 0
else
    echo ""
    echo "⚠️  Revisar errores arriba"
    exit 1
fi