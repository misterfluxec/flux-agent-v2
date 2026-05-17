# =============================================================================
# FLUXAGENT V2 — DOCKERFILE DEL BACKEND
# =============================================================================
# Multi-stage build para minimizar el tamaño de la imagen final.
# Stage 1: Instalar dependencias con uv (gestor rápido de paquetes Python)
# Stage 2: Imagen de producción ligera
# =============================================================================

# --- Stage 1: Builder ---
FROM python:3.12-slim AS builder

WORKDIR /build

# Instalar uv para gestión rápida de dependencias
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copiar solo requirements para aprovechar el cache de Docker
COPY requirements.txt .

# Instalar dependencias en un directorio separado (sin instalar en sistema)
RUN uv pip install --system --no-cache -r requirements.txt


# --- Stage 2: Producción ---
FROM python:3.12-slim

# Metadatos de la imagen
LABEL maintainer="FluxAgent Team"
LABEL version="2.0.0"
LABEL description="FluxAgent V2 Backend - FastAPI + SQLAlchemy Async"

# Instalar ffmpeg para procesamiento de audio (faster-whisper)
RUN apt-get update && apt-get install -y ffmpeg espeak && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad y asignarle un home directory para caché (e.g. HuggingFace)
RUN groupadd -r fluxuser && useradd -r -m -d /home/fluxuser -g fluxuser fluxuser

WORKDIR /app

# Copiar dependencias instaladas desde el builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar código fuente
COPY . /app
RUN ln -s /app /app/src

# Crear carpeta de uploads y asignar permisos
RUN mkdir -p /app/uploads && chown -R fluxuser:fluxuser /app

# Variables de entorno del contenedor
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Cambiar al usuario no-root
USER fluxuser

# Puerto de la aplicación
EXPOSE 8000

# Healthcheck interno del contenedor
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Comando de inicio con uvicorn en modo producción
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
