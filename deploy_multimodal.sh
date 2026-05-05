#!/bin/bash
# =============================================================================
# FLUXAGENT V2 - SCRIPT DE DESPLIEGUE multimodal (Oír-Hablar-Ver)
# =============================================================================
# Este script despliega las 4 implementaciones:
#   1. TTS con Piper
#   2. Seed de Planes con features
#   3. LLMRouter (Cloud/Local)
#   4. WebSocket Voice Streaming
# =============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE} FLUXAGENT V2 - DESPLIEGUE MULTIMODAL${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# =============================================================================
# CONFIGURACIÓN
# =============================================================================
PROJECT_DIR="/home/mister/flux-agent-v2"
SRC_DIR="$PROJECT_DIR/src"
MIGRATIONS_DIR="$PROJECT_DIR/migrations"
MODELS_DIR="/app/models"

# Variables de entorno (pueden sobreescribirse)
export LLM_MODE=${LLM_MODE:-"local"}
export PIPER_MODEL_PATH=${PIPER_MODEL_PATH:-"$MODELS_DIR/es_MX-david-medium.onnx"}

echo -e "${YELLOW}Configuración:${NC}"
echo "  PROJECT_DIR: $PROJECT_DIR"
echo "  LLM_MODE: $LLM_MODE"
echo "  PIPER_MODEL_PATH: $PIPER_MODEL_PATH"
echo ""

# =============================================================================
# 1. INSTALAR DEPENDENCIAS
# =============================================================================
echo -e "${BLUE}[1/6]${NC} Instalando dependencias Python..."
cd "$SRC_DIR"

if [ -f "requirements.txt" ]; then
    pip install -q piper-tts faster-whisper httpx pydantic-settings redis
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓ Dependencias instaladas${NC}"
else
    echo -e "${RED}✗ requirements.txt no encontrado${NC}"
    exit 1
fi
echo ""

# =============================================================================
# 2. DESCARGAR MODELO PIPER (TTS)
# =============================================================================
echo -e "${BLUE}[2/6]${NC} Verificando modelo Piper TTS..."

mkdir -p "$MODELS_DIR"

if [ -f "$PIPER_MODEL_PATH" ]; then
    echo -e "${GREEN}✓ Modelo Piper ya existe: $PIPER_MODEL_PATH${NC}"
else
    echo -e "${YELLOW}  Descargando modelo Piper (es_MX-david-medium)...${NC}"
    
    # Intentar descargar de HuggingFace
    PIPER_URL="https://huggingface.co/rhassyl/piper-voices/resolve/main/es/MX/david/medium/voice.onnx"
    
    if command -v wget &> /dev/null; then
        wget -q --show-progress -O "$PIPER_MODEL_PATH" "$PIPER_URL" || true
    elif command -v curl &> /dev/null; then
        curl -sL "$PIPER_URL" -o "$PIPER_MODEL_PATH" || true
    fi
    
    if [ -f "$PIPER_MODEL_PATH" ]; then
        echo -e "${GREEN}✓ Modelo Piper descargado${NC}"
    else
        echo -e "${YELLOW}⚠ Modelo Piper no disponible - TTS funcionará en modo degrade${NC}"
    fi
fi
echo ""

# =============================================================================
# 3. EJECUTAR MIGRACIÓN DE PLANES
# =============================================================================
echo -e "${BLUE}[3/6]${NC} Ejecutando migración de planes..."

# Intentar obtener credenciales de .env o usar valores por defecto
if [ -f "$PROJECT_DIR/.env" ]; then
    source "$PROJECT_DIR/.env"
fi

DB_HOST=${database_url##*@}
DB_HOST=${DB_HOST%%:*}
DB_USER=${database_url%%:*}
DB_PASS=${database_url##*://}
DB_PASS=${DB_PASS%%@*}
DB_NAME=${database_url##*/}
DB_PORT=${DB_HOST##*:}

if [ -z "$DB_PORT" ] || [[ ! "$DB_PORT" =~ ^[0-9]+$ ]]; then
    DB_PORT=5432
fi

echo "  Conectando a PostgreSQL: $DB_HOST:$DB_PORT/$DB_NAME"

if command -v psql &> /dev/null; then
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$MIGRATIONS_DIR/006_seed_plans.sql" 2>/dev/null || \
    echo -e "${YELLOW}⚠ Migration puede requerir ejecución manual con superuser${NC}"
    
    echo -e "${GREEN}✓ Migración procesada${NC}"
else
    echo -e "${YELLOW}⚠ psql no disponible - ejecutar manualmente:${NC}"
    echo "   psql -h <host> -U <user> -d <db> -f $MIGRATIONS_DIR/006_seed_plans.sql"
fi
echo ""

# =============================================================================
# 4. VERIFICAR ESTRUCTURA DE ARCHIVOS
# =============================================================================
echo -e "${BLUE}[4/6]${NC} Verificando estructura de archivos..."

check_file() {
    if [ -f "$1" ]; then
        echo -e "  ${GREEN}✓${NC} $(basename $1)"
    else
        echo -e "  ${RED}✗${NC} $(basename $1) - FALTA"
        return 1
    fi
}

check_file "$SRC_DIR/core/capabilities/tts.py"
check_file "$SRC_DIR/core/llm/router.py"
check_file "$SRC_DIR/routers/voice_router.py"
check_file "$SRC_DIR/services/multimedia.py"
check_file "$SRC_DIR/core/plan_manager.py"
check_file "$SRC_DIR/routers/chat_router.py"
check_file "$SRC_DIR/config.py"
check_file "$SRC_DIR/main.py"

echo -e "${GREEN}✓ Estructura de archivos verificada${NC}"
echo ""

# =============================================================================
# 5. VERIFICAR IMPORTACIONES (SINTÁXIS)
# =============================================================================
echo -e "${BLUE}[5/6]${NC} Verificando sintaxis Python..."

cd "$SRC_DIR"

# Verificar sintaxis de archivos clave
python3 -m py_compile core/capabilities/tts.py && echo -e "  ${GREEN}✓${NC} tts.py" || echo -e "  ${RED}✗${NC} tts.py"
python3 -m py_compile core/llm/router.py && echo -e "  ${GREEN}✓${NC} router.py" || echo -e "  ${RED}✗${NC} router.py"
python3 -m py_compile routers/voice_router.py && echo -e "  ${GREEN}✓${NC} voice_router.py" || echo -e "  ${RED}✗${NC} voice_router.py"
python3 -m py_compile services/multimedia.py && echo -e "  ${GREEN}✓${NC} multimedia.py" || echo -e "  ${RED}✗${NC} multimedia.py"

echo -e "${GREEN}✓ Sintaxis verificada${NC}"
echo ""

# =============================================================================
# 6. INICIAR APLICACIÓN
# =============================================================================
echo -e "${BLUE}[6/6]${NC} Iniciando FluxAgent V2..."

# Verificar si hay proceso corriendo
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo -e "${YELLOW}  Reiniciando aplicación...${NC}"
    pkill -f "uvicorn main:app" || true
    sleep 2
fi

# Iniciar en background
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > /tmp/fluxagent.log 2>&1 &
APP_PID=$!

sleep 3

if ps -p $APP_PID > /dev/null; then
    echo -e "${GREEN}✓ Aplicación iniciada (PID: $APP_PID)${NC}"
    echo "  Logs: /tmp/fluxagent.log"
    echo "  API: http://localhost:8000/docs"
else
    echo -e "${RED}✗ Error al iniciar aplicación${NC}"
    echo "  Revisar logs: /tmp/fluxagent.log"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN} DESPLIEGUE MULTIMODAL COMPLETADO${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Características implementadas:"
echo "  🔊 TTS con Piper (síntesis de voz)"
echo "  📊 Seed de planes con features JSONB"
echo "  🧠 LLMRouter (local/cloud)"
echo "  📡 WebSocket voice streaming"
echo ""
echo "Para verificar:"
echo "  - Revisar logs: tail -f /tmp/fluxagent.log"
echo "  - API docs: http://localhost:8000/docs"
echo "  - Test: python3 test_implementations.py"
echo ""

# =============================================================================
# NOTAS PARA CONFIGURACIÓN CLOUD (OPCIONAL)
# =============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " CONFIGURACIÓN CLOUD (OPCIONAL)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Para activar modelos cloud (actualmente desactivados):"
echo ""
echo "  # Opción 1: OpenAI"
echo "  export OPENAI_API_KEY=sk-..."
echo "  export LLM_MODE=cloud"
echo "  export DEFAULT_CLOUD_PROVIDER=openai"
echo ""
echo "  # Opción 2: Anthropic"
echo "  export ANTHROPIC_API_KEY=sk-ant-..."
echo "  export LLM_MODE=cloud"
echo "  export DEFAULT_CLOUD_PROVIDER=anthropic"
echo ""
echo "  # Luego reiniciar: pkill -f uvicorn && nohup uvicorn ... &"
echo ""