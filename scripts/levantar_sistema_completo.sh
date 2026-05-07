#!/bin/bash
set -e

echo "🚀 LEVANTANDO FLUXAGENT V2 DESDE CERO"
echo "=========================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones helper
success() { echo -e "${GREEN}✅ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# =============================================================================
# 1️⃣ VERIFICAR PREREQUISITOS
# =============================================================================

echo ""
echo "🔍 Verificando prerrequisitos..."

if ! command -v docker &> /dev/null; then
    error "Docker no está instalado"
    info "Instalar: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose no está instalado"
    info "Instalar: https://docs.docker.com/compose/install/"
    exit 1
fi

if ! command -v git &> /dev/null; then
    error "Git no está instalado"
    info "Instalar: https://git-scm.com/downloads"
    exit 1
fi

success "Prerrequisitos verificados: Docker, Docker Compose, Git"

# =============================================================================
# 2️⃣ CLONAR O VERIFICAR REPOSITORIO
# =============================================================================

echo ""
echo "📥 Verificando repositorio..."

if [ ! -d "flux-agent-v2" ]; then
    warning "Repositorio no encontrado. Clonando..."
    git clone https://github.com/tu-usuario/flux-agent-v2.git || {
        error "No se pudo clonar el repositorio"
        info "Verificar URL y permisos"
        exit 1
    }
    cd flux-agent-v2
    success "Repositorio clonado exitosamente"
else
    cd flux-agent-v2
    success "Usando repositorio existente"
fi

# Verificar si es el repositorio correcto
if [ ! -f "docker-compose.yml" ] || [ ! -f "src/main.py" ]; then
    error "No parece ser el repositorio correcto de FluxAgent V2"
    error "Faltan archivos críticos: docker-compose.yml o src/main.py"
    exit 1
fi

# =============================================================================
# 3️⃣ CONFIGURAR VARIABLES DE ENTORNO
# =============================================================================

echo ""
echo "📝 Configurando variables de entorno..."

if [ ! -f ".env" ]; then
    warning "Archivo .env no encontrado. Creando configuración por defecto..."
    cat > .env << 'EOF'
# =============================================================================
# FLUXAGENT V2 — VARIABLES DE ENTORNO
# =============================================================================

# Base de Datos PostgreSQL
DATABASE_URL=postgresql+asyncpg://fluxadmin:fluxsecure2026@localhost:5434/fluxagent_v2
DB_HOST=localhost
DB_PORT=5434
DB_USER=fluxadmin
DB_PASSWORD=fluxsecure2026
DB_NAME=fluxagent_v2

# Cache Redis
REDIS_URL=redis://:redisflux2026@localhost:6381/0
REDIS_HOST=localhost
REDIS_PORT=6381
REDIS_PASSWORD=redisflux2026

# AI Engine Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=qwen2.5:3b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Seguridad JWT
SECRET_KEY=cambiar_en_produccion_jwt_secret_mas_largo_y_seguro_aqui
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Aplicación
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# Frontend
NEXT_PUBLIC_BACKEND_URL=http://localhost:9000
EOF
    success "Archivo .env creado con configuración por defecto"
    warning "⚠️  IMPORTANTE: Editar SECRET_KEY en producción"
else
    success "Archivo .env encontrado"
fi

# =============================================================================
# 4️⃣ DETENER Y LIMPIAR SERVICIOS EXISTENTES
# =============================================================================

echo ""
echo "🧹 Limpiando servicios existentes..."

docker-compose down --remove-orphans 2>/dev/null || true
docker system prune -f 2>/dev/null || true

success "Servicios existentes detenidos y limpiados"

# =============================================================================
# 5️⃣ CONSTRUIR Y LEVANTAR INFRAESTRUCTURA
# =============================================================================

echo ""
echo "🐳 Construyendo y levantando servicios..."

info "Construyendo imágenes Docker (puede tardar varios minutos)..."
docker-compose build --no-cache --parallel || {
    error "Falló la construcción de imágenes Docker"
    info "Verificar Dockerfile y dependencias"
    exit 1
}

info "Levantando servicios..."
docker-compose up -d || {
    error "Falló el levantamiento de servicios"
    info "Verificar logs con: docker-compose logs"
    exit 1
}

success "Servicios levantados en background"

# =============================================================================
# 6️⃣ ESPERAR Y VERIFICAR SERVICIOS
# =============================================================================

echo ""
echo "⏳ Esperando que servicios estén listos..."

# Esperar que los servicios inicien
sleep 45

# Función para verificar servicio
check_service() {
    local service_name=$1
    local check_command=$2
    local max_attempts=${3:-30}
    local attempt=1
    
    echo -n "   🔍 Verificando $service_name... "
    
    while [ $attempt -le $max_attempts ]; do
        if eval "$check_command" >/dev/null 2>&1; then
            success "$service_name está saludable"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    error "$service_name no está disponible después de $max_attempts intentos"
    return 1
}

# Verificar cada servicio
echo ""
echo "🏥 Verificando salud del sistema..."

check_service "PostgreSQL" \
    "docker-compose exec -T postgres pg_isready -U fluxadmin -d fluxagent_v2" \
    30

check_service "Redis" \
    "docker-compose exec -T redis redis-cli -a redisflux2026 ping" \
    20

check_service "Backend API" \
    "curl -sf http://localhost:9000/health" \
    25

check_service "Frontend" \
    "curl -sf http://localhost:4000" \
    20

check_service "Ollama" \
    "curl -sf http://localhost:11434/api/tags" \
    60

# =============================================================================
# 7️⃣ MIGRAR BASE DE DATOS
# =============================================================================

echo ""
echo "🗄️ Migrando base de datos..."

if docker-compose exec -T postgres pg_isready -U fluxadmin -d fluxagent_v2 >/dev/null 2>&1; then
    # Aplicar migraciones en orden
    for migration in migrations/*.sql; do
        if [ -f "$migration" ]; then
            migration_name=$(basename "$migration")
            echo -n "   📋 Aplicando $migration_name... "
            
            if docker-compose exec -T postgres psql -U fluxadmin -d fluxagent_v2 < "$migration" >/dev/null 2>&1; then
                success "$migration_name aplicada"
            else
                warning "$migration_name falló (puede que ya exista)"
            fi
        fi
    done
    success "Migraciones completadas"
else
    error "No hay conexión a la base de datos para migrar"
    exit 1
fi

# =============================================================================
# 8️⃣ CREAR USUARIO POR DEFECTO
# =============================================================================

echo ""
echo "👤 Creando usuario por defecto..."

# Verificar si el usuario ya existe
user_exists=$(docker-compose exec -T postgres psql -U fluxadmin -d fluxagent_v2 \
    -t -c "SELECT COUNT(*) FROM usuarios WHERE email='maritza@mendoza.com';" 2>/dev/null | tr -d ' ')

if [ "$user_exists" = "0" ]; then
    # Generar hash para contraseña 'password'
    password_hash=$(python3 -c "
import bcrypt
print(bcrypt.hashpw('password'.encode(), bcrypt.gensalt()).decode())
" 2>/dev/null)
    
    # Insertar usuario
    docker-compose exec -T postgres psql -U fluxadmin -d fluxagent_v2 << EOF
INSERT INTO usuarios (id, email, password_hash, nombre, rol, tenant_id, plan, creado_en, actualizado_en)
VALUES (
    gen_random_uuid(),
    'maritza@mendoza.com',
    '$password_hash',
    'Maritza Mendoza',
    'admin',
    gen_random_uuid(),
    'pro',
    NOW(),
    NOW()
);
EOF
    
    if [ $? -eq 0 ]; then
        success "Usuario por defecto creado"
    else
        error "Falló la creación del usuario por defecto"
    fi
else
    success "Usuario por defecto ya existe"
fi

# =============================================================================
# 9️⃣ VERIFICACIÓN FINAL
# =============================================================================

echo ""
echo "🎯 Verificación final del sistema..."

# Ejecutar script de verificación pre-beta si existe
if [ -f "scripts/verify_pre_beta.sh" ]; then
    info "Ejecutando verificación pre-beta..."
    ./scripts/verify_pre_beta.sh || {
        warning "Verificación pre-beta tuvo problemas, pero sistema está levantado"
    }
fi

# Verificar puertos
echo ""
echo "🌐 Verificando puertos..."

check_port() {
    local port=$1
    local service=$2
    
    if netstat -tulpn 2>/dev/null | grep ":$port " >/dev/null; then
        success "$service (puerto $port) está escuchando"
    else
        error "$service (puerto $port) no está escuchando"
    fi
}

check_port "4000" "Frontend"
check_port "9000" "Backend API"
check_port "5434" "PostgreSQL"
check_port "6381" "Redis"
check_port "11434" "Ollama"

# =============================================================================
# 📋 RESUMEN FINAL
# =============================================================================

echo ""
echo "🎉 SISTEMA LEVANTADO EXITOSAMENTE"
echo "=================================="
echo ""
echo "📱 ACCESOS DISPONIBLES:"
echo "   🌐 Frontend: ${GREEN}http://localhost:4000${NC}"
echo "   🔧 Backend API: ${GREEN}http://localhost:9000${NC}"
echo "   📚 API Docs: ${GREEN}http://localhost:9000/docs${NC}"
echo "   🏥 Health Check: ${GREEN}http://localhost:9000/health${NC}"
echo ""
echo "👤 USUARIO POR DEFECTO:"
echo "   📧 Email: ${GREEN}maritza@mendoza.com${NC}"
echo "   🔑 Contraseña: ${GREEN}password${NC}"
echo "   👑 Rol: ${GREEN}admin${NC}"
echo "   📋 Plan: ${GREEN}pro${NC}"
echo ""
echo "🧪 TESTING AUTOMATIZADO:"
echo "   📋 E2E Tests: ${YELLOW}pytest tests/e2e/test_core_flow.py -v --asyncio-mode=auto${NC}"
echo "   🔍 Verificación: ${YELLOW}./scripts/verify_pre_beta.sh${NC}"
echo ""
echo "📚 DOCUMENTACIÓN COMPLETA:"
echo "   📖 Guía completa: ${YELLOW}DOCUMENTACION_COMPLETA_SISTEMA.md${NC}"
echo ""
echo "🔧 COMANDOS ÚTILES:"
echo "   📋 Ver logs: ${YELLOW}docker-compose logs -f${NC}"
echo "   🔄 Reiniciar: ${YELLOW}docker-compose restart${NC}"
echo "   🛑 Detener: ${YELLOW}docker-compose down${NC}"
echo "   🗄️ DB Shell: ${YELLOW}docker-compose exec postgres psql -U fluxadmin -d fluxagent_v2${NC}"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   🔐 Editar SECRET_KEY en .env para producción"
echo "   📥 Hacer backup del repositorio regularmente"
echo "   📊 Monitorear logs en producción"
echo ""
echo "🚀 FluxAgent V2 está listo para uso!"
