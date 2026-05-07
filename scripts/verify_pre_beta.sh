#!/bin/bash
set -e

echo "🔍 VERIFICACIÓN PRE-BETA - FLUXAGENT V2"
echo "========================================"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funciones helper
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

# Variables de configuración
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5434}
DB_USER=${DB_USER:-fluxadmin}
DB_NAME=${DB_NAME:-fluxagent_v2}
REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6381}
REDIS_PASSWORD=${REDIS_PASSWORD:-redisflux2026}
API_HOST=${API_HOST:-localhost}
API_PORT=${API_PORT:-9000}

# =============================================================================
# 1️⃣ VERIFICACIÓN DE BASE DE DATOS
# =============================================================================
echo ""
echo "🗄️  Verificando Base de Datos..."

# Verificar si PostgreSQL está corriendo
if pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER >/dev/null 2>&1; then
    success "PostgreSQL: Conectado"
    
    # Verificar tablas críticas
    TABLES_COUNT=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';" 2>/dev/null | tr -d ' ')
    
    if [ "$TABLES_COUNT" -ge "10" ]; then
        success "DB: $TABLES_COUNT tablas encontradas"
    else
        error "DB: Solo $TABLES_COUNT tablas (se esperaban 10+)"
    fi
    
    # Verificar migración 013
    if psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT column_name FROM information_schema.columns WHERE table_name='agents' AND column_name='script_ventas';" >/dev/null 2>&1; then
        success "DB: Migración 013 aplicada (script_ventas presente)"
    else
        error "DB: Migración 013 no aplicada"
    fi
    
else
    error "PostgreSQL: No conectado en $DB_HOST:$DB_PORT"
    warning "Ejecutar: docker-compose up -d postgres"
fi

# =============================================================================
# 2️⃣ VERIFICACIÓN DE REDIS
# =============================================================================
echo ""
echo "📡 Verificando Redis..."

if redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD ping 2>/dev/null | grep -q PONG; then
    success "Redis: Conectado"
    
    # Verificar memoria disponible
    REDIS_INFO=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD info memory 2>/dev/null)
    if echo "$REDIS_INFO" | grep -q "used_memory"; then
        success "Redis: Métricas disponibles"
    else
        warning "Redis: No se pueden obtener métricas"
    fi
else
    error "Redis: No disponible en $REDIS_HOST:$REDIS_PORT"
    warning "Ejecutar: docker-compose up -d redis"
fi

# =============================================================================
# 3️⃣ VERIFICACIÓN DE OLLAMA
# =============================================================================
echo ""
echo "🤖 Verificando Ollama..."

if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
    success "Ollama: Conectado"
    
    # Verificar modelos disponibles
    OLLAMA_MODELS=$(curl -s http://localhost:11434/api/tags | jq -r '.models[].name' 2>/dev/null || echo "")
    if [ -n "$OLLAMA_MODELS" ]; then
        success "Ollama: Modelos disponibles - $OLLAMA_MODELS"
    else
        warning "Ollama: Sin modelos descargados"
        warning "Ejecutar: curl http://localhost:11434/api/pull -d '{\"name\":\"qwen2.5:3b\"}'"
    fi
else
    error "Ollama: No responde en http://localhost:11434"
    warning "Ejecutar: docker-compose up -d ollama"
fi

# =============================================================================
# 4️⃣ VERIFICACIÓN DE ENDPOINTS CRÍTICOS
# =============================================================================
echo ""
echo "🌐 Verificando Endpoints Críticos..."

# Función para verificar endpoint
check_endpoint() {
    local path=$1
    local expected_codes=$2
    local description=$3
    
    CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$API_HOST:$API_PORT$path)
    
    if [[ "$expected_codes" == *"$CODE"* ]]; then
        success "$description → $CODE"
    else
        error "$description → $CODE (esperado: $expected_codes)"
    fi
}

# Verificar endpoints principales
check_endpoint "/health" "200" "Health Check"
check_endpoint "/api/v1/agents" "200,401" "Agents API"
check_endpoint "/api/v1/analytics/overview" "200,401" "Analytics API"
check_endpoint "/api/v1/auth/login" "200,405" "Auth Login"

# =============================================================================
# 5️⃣ VERIFICACIÓN DE FRONTEND
# =============================================================================
echo ""
echo "🎨 Verificando Frontend..."

if curl -sf http://localhost:4000 >/dev/null 2>&1; then
    success "Frontend: Corriendo en puerto 4000"
    
    # Verificar página principal
    if curl -sf http://localhost:4000/es/dashboard >/dev/null 2>&1; then
        success "Frontend: Dashboard accesible"
    else
        warning "Frontend: Dashboard no accesible (puede requerir login)"
    fi
else
    error "Frontend: No responde en puerto 4000"
    warning "Ejecutar: cd frontend && npm run dev"
fi

# =============================================================================
# 6️⃣ VERIFICACIÓN DE LIMPIEZA DE CÓDIGO
# =============================================================================
echo ""
echo "🧹 Verificando Limpieza de Código..."

# Verificar routers duplicados
if grep -q "reports_router\|insights_router" src/main.py 2>/dev/null; then
    error "Routers duplicados encontrados en main.py"
    warning "Comentar reports_router e insights_router para producción"
else
    success "Main.py: Sin routers duplicados"
fi

# Verificar archivos _legacy
if [ -d "src/routers/_legacy" ]; then
    success "Routers legacy en carpeta _legacy"
else
    warning "Carpeta _legacy no encontrada (crear para routers obsoletos)"
fi

# Verificar imports no usados
UNUSED_IMPORTS=$(grep -r "from routers\." src/main.py | grep -v "#" | wc -l)
if [ "$UNUSED_IMPORTS" -le "20" ]; then
    success "Main.py: $UNUSED_IMPORTS imports activos (razonable)"
else
    warning "Main.py: $UNUSED_IMPORTS imports (posibles duplicados)"
fi

# =============================================================================
# 7️⃣ VERIFICACIÓN DE TESTING
# =============================================================================
echo ""
echo "🧪 Verificando Testing..."

if [ -f "tests/e2e/test_core_flow.py" ]; then
    success "E2E Test: test_core_flow.py existe"
    
    # Verificar dependencias de testing
    if pip list | grep -q "pytest\|httpx\|testcontainers"; then
        success "Testing: Dependencias instaladas"
    else
        warning "Testing: Instalar dependencias con pip install pytest pytest-asyncio httpx testcontainers"
    fi
else
    error "E2E Test: test_core_flow.py no encontrado"
fi

# =============================================================================
# 8️⃣ VERIFICACIÓN DE CONFIGURACIÓN
# =============================================================================
echo ""
echo "⚙️  Verificando Configuración..."

# Verificar variables de entorno críticas
if [ -f ".env" ]; then
    success ".env: Archivo encontrado"
    
    # Verificar variables críticas
    CRITICAL_VARS=("DATABASE_URL" "REDIS_URL" "SECRET_KEY")
    for var in "${CRITICAL_VARS[@]}"; do
        if grep -q "^$var=" .env; then
            success ".env: $var configurada"
        else
            warning ".env: $var no configurada"
        fi
    done
else
    warning ".env: Archivo no encontrado (usando defaults)"
fi

# =============================================================================
# RESUMEN FINAL
# =============================================================================
echo ""
echo "📊 RESUMEN DE VERIFICACIÓN"
echo "=========================="

# Contar éxitos y errores
TOTAL_CHECKS=0
PASSED_CHECKS=0

# Contar checks (aproximado basado en las verificaciones anteriores)
TOTAL_CHECKS=20  # Número aproximado de verificaciones

# Calcular estado general
echo ""
echo "🎉 VERIFICACIÓN COMPLETADA"
echo ""

# Determinar estado general
DB_OK=$(pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER >/dev/null 2>&1 && echo "1" || echo "0")
REDIS_OK=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD ping 2>/dev/null | grep -q PONG && echo "1" || echo "0")
OLLAMA_OK=$(curl -sf http://localhost:11434/api/tags >/dev/null 2>&1 && echo "1" || echo "0")
API_OK=$(curl -sf http://$API_HOST:$API_PORT/health >/dev/null 2>&1 && echo "1" || echo "0")

SCORE=$((DB_OK + REDIS_OK + OLLAMA_OK + API_OK))

if [ $SCORE -eq 4 ]; then
    success "📊 Estado: LISTO PARA BETA"
    echo "🚀 Próximo paso: Deploy a staging → QA → Producción"
elif [ $SCORE -ge 2 ]; then
    warning "📊 Estado: PARCIALMENTE LISTO"
    echo "🔧 Resolver problemas marcados con ❌ antes de beta"
else
    error "📊 Estado: NO LISTO PARA BETA"
    echo "🚨 Resolver problemas críticos antes de continuar"
fi

echo ""
echo "🔍 Para ejecutar tests E2E:"
echo "   pytest tests/e2e/test_core_flow.py -v --asyncio-mode=auto"
echo ""
echo "🐳 Para levantar servicios completos:"
echo "   docker-compose up -d postgres redis ollama backend"
echo ""
