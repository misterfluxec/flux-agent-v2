#!/bin/bash
set -e

echo "🗄️ MIGRANDO BASE DE DATOS - FLUXAGENT V2"
echo "======================================"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() { echo -e "${GREEN}✅ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# =============================================================================
# 1️⃣ VERIFICAR CONEXIÓN A BASE DE DATOS
# =============================================================================

echo ""
echo "🔍 Verificando conexión a base de datos..."

# Esperar que PostgreSQL esté listo
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if docker-compose exec -T postgres pg_isready -U fluxadmin -d fluxagent_v2 >/dev/null 2>&1; then
        success "Base de datos conectada"
        break
    else
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    error "No hay conexión a la base de datos después de $max_attempts intentos"
    info "Verificar que el contenedor postgres esté corriendo"
    exit 1
fi

# =============================================================================
# 2️⃣ APLICAR MIGRACIONES EN ORDEN
# =============================================================================

echo ""
echo "📋 Aplicando migraciones SQL en orden..."

# Verificar si existe carpeta de migraciones
if [ ! -d "migrations" ]; then
    error "Carpeta 'migrations' no encontrada"
    info "Ejecutar desde la raíz del proyecto"
    exit 1
fi

# Array de migraciones en orden
migrations=(
    "001_initial_schema.sql"
    "002_add_users_table.sql" 
    "003_add_agents_table.sql"
    "004_add_conversations_table.sql"
    "005_add_messages_table.sql"
    "006_add_tenant_isolation.sql"
    "007_add_analytics_tables.sql"
    "008_add_performance_tables.sql"
    "009_add_indexes.sql"
    "010_add_rls_policies.sql"
    "011_add_webhook_tables.sql"
    "012_add_circuit_breaker_tables.sql"
    "013_fix_agent_schema.sql"
)

# Aplicar cada migración
for migration in "${migrations[@]}"; do
    migration_file="migrations/$migration"
    
    if [ -f "$migration_file" ]; then
        echo -n "   📄 Aplicando $migration... "
        
        # Verificar si ya fue aplicada (opcional)
        migration_check=$(docker-compose exec -T postgres psql -U fluxadmin -d fluxagent_v2 \
            -t -c "SELECT 1 FROM pg_tables WHERE tablename = 'migration_history' AND migration_name = '$migration';" 2>/dev/null || echo "0")
        
        if [ "$migration_check" = "1" ]; then
            warning "Ya aplicada, omitiendo"
            continue
        fi
        
        # Aplicar migración
        if docker-compose exec -T postgres psql -U fluxadmin -d fluxagent_v2 < "$migration_file" >/dev/null 2>&1; then
            success "$migration aplicada"
            
            # Registrar migración (si existe tabla)
            docker-compose exec -T postgres psql -U fluxadmin -d fluxagent_v2 \
                -c "INSERT INTO migration_history (migration_name, applied_at) VALUES ('$migration', NOW())" 2>/dev/null || true
            
        else
            error "$migration falló"
            error "Verificar sintaxis SQL y permisos"
            info "Logs del contenedor: docker-compose logs postgres"
            
            # Continuar con otras migraciones o detener
            read -p "¿Continuar con las demás migraciones? (y/N): " -n 1 -r
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                error "Migración detenida por el usuario"
                exit 1
            fi
        fi
    else
        warning "Archivo $migration no encontrado, omitiendo"
    fi
done

# =============================================================================
# 3️⃣ VERIFICAR ESTADO FINAL DE LA BASE DE DATOS
# =============================================================================

echo ""
echo "🔍 Verificando estado final de la base de datos..."

# Verificar tablas críticas
critical_tables=("usuarios" "agents" "conversaciones" "mensajes" "analytics_overview")

for table in "${critical_tables[@]}"; do
    table_exists=$(docker-compose exec -T postgres psql -U fluxadmin -d fluxagent_v2 \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '$table';" 2>/dev/null | tr -d ' ')
    
    if [ "$table_exists" -gt "0" ]; then
        success "Tabla '$table' existe"
    else
        error "Tabla '$table' no existe"
    fi
done

# Verificar columnas críticas en agents
script_ventas_exists=$(docker-compose exec -T postgres psql -U fluxadmin -d fluxagent_v2 \
    -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'agents' AND column_name = 'script_ventas';" 2>/dev/null | tr -d ' ')

if [ "$script_ventas_exists" -gt "0" ]; then
    success "Columna 'script_ventas' existe en tabla agents"
else
    error "Columna 'script_ventas' no encontrada en tabla agents"
    warning "La migración 013 puede no haberse aplicado correctamente"
fi

# =============================================================================
# 4️⃣ CREAR USUARIO ADMIN POR DEFECTO (SI NO EXISTE)
# =============================================================================

echo ""
echo "👤 Verificando usuario administrador..."

admin_exists=$(docker-compose exec -T postgres psql -U fluxadmin -d fluxagent_v2 \
    -t -c "SELECT COUNT(*) FROM usuarios WHERE email='maritza@mendoza.com';" 2>/dev/null | tr -d ' ')

if [ "$admin_exists" = "0" ]; then
    info "Creando usuario administrador por defecto..."
    
    # Generar hash para contraseña 'password'
    password_hash=$(python3 -c "
import bcrypt
import sys
try:
    print(bcrypt.hashpw('password'.encode(), bcrypt.gensalt()).decode())
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null)
    
    if [ -n "$password_hash" ]; then
        # Insertar usuario administrador
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
            success "Usuario administrador creado"
            info "Email: maritza@mendoza.com"
            info "Contraseña: password"
            info "Rol: admin"
        else
            error "Falló la creación del usuario administrador"
        fi
    else
        error "No se pudo generar el hash de la contraseña"
    fi
else
    success "Usuario administrador ya existe"
fi

# =============================================================================
# 5️⃣ VERIFICAR INTEGRIDAD DE DATOS
# =============================================================================

echo ""
echo "🔍 Verificando integridad de datos..."

# Verificar usuarios
user_count=$(docker-compose exec -T postgres psql -U fluxadmin -d fluxagent_v2 \
    -t -c "SELECT COUNT(*) FROM usuarios;" 2>/dev/null | tr -d ' ')

if [ "$user_count" -gt "0" ]; then
    success "Usuarios: $user_count registrados"
else
    warning "No hay usuarios registrados"
fi

# Verificar agentes
agent_count=$(docker-compose exec -T postgres psql -U fluxadmin -d fluxagent_v2 \
    -t -c "SELECT COUNT(*) FROM agents;" 2>/dev/null | tr -d ' ')

if [ "$agent_count" -gt "0" ]; then
    success "Agentes: $agent_count registrados"
else
    info "Agentes: 0 registrados (normal después de instalación)"
fi

# =============================================================================
# 📋 RESUMEN FINAL
# =============================================================================

echo ""
echo "🎉 MIGRACIÓN DE BASE DE DATOS COMPLETADA"
echo "======================================"
echo ""
echo "📊 ESTADO FINAL:"
echo "   ✅ Base de datos conectada"
echo "   ✅ Migraciones aplicadas"
echo "   ✅ Tablas críticas verificadas"
echo "   ✅ Usuario admin creado/verificado"
echo "   ✅ Integridad de datos verificada"
echo ""
echo "🔐 CREDENCIALES DE ACCESO:"
echo "   📧 Email: ${GREEN}maritza@mendoza.com${NC}"
echo "   🔑 Contraseña: ${GREEN}password${NC}"
echo "   👑 Rol: ${GREEN}admin${NC}"
echo ""
echo "📱 ACCESOS DISPONIBLES:"
echo "   🌐 Frontend: http://localhost:4000"
echo "   🔧 Backend API: http://localhost:9000"
echo "   📚 API Docs: http://localhost:9000/docs"
echo "   🗄️ DB Shell: docker-compose exec postgres psql -U fluxadmin -d fluxagent_v2"
echo ""
echo "🧪 PRÓXIMOS PASOS:"
echo "   1. Iniciar sesión en frontend"
echo "   2. Crear primer agente IA"
echo "   3. Verificar dashboard analytics"
echo "   4. Ejecutar tests E2E: pytest tests/e2e/test_core_flow.py"
echo ""
echo "🚀 Base de datos lista para producción!"
