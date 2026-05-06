#!/bin/bash
set -e

echo "🔊 Instalando dependencias de voz (Open Source)..."

# 1. Actualizar pip
./venv/bin/pip install --upgrade pip

# 2. Instalar Pipecat core
./venv/bin/pip install pipecat-ai

# 3. Instalar extras con manejo de errores
for extra in silero ollama piper; do
    echo "→ Instalando pipecat-ai[$extra]..."
    ./venv/bin/pip install "pipecat-ai[$extra]" || {
        echo "⚠️  Falló $extra, continuando..."
    }
done

# 4. Whisper: usar faster-whisper (más ligero)
echo "→ Instalando faster-whisper (optimizado para CPU)..."
./venv/bin/pip install "faster-whisper"

# 5. Dependencias de WebSocket para FastAPI
./venv/bin/pip install "websockets==11.0.3" "uvicorn[standard]"

echo "✅ Instalación completada."
