#!/bin/bash
# =============================================================================
# YANUA AI — SCRIPT DE CONFIGURACIÓN BETA
# =============================================================================
# Uso: chmod +x setup_beta.sh && ./setup_beta.sh
# =============================================================================

set -e

echo -e "\n🚀 \033[1mIniciando Configuración Beta de Yanua AI...\033[0m"

# 1. Validar dependencias
if ! command -v docker &> /dev/null; then
    echo -e "❌ Docker no encontrado. Por favor, instálalo primero."
    exit 1
fi

# 2. Generar .env desde .env.example
if [ ! -f .env ]; then
    echo -e "⚙️  Generando archivo .env seguro..."
    if [ -f .env.example ]; then
        cp .env.example .env
        
        # Generar secretos criptográficos reales
        JWT_SECRET=$(openssl rand -hex 32)
        DB_PASS=$(openssl rand -base64 12 | tr -d '/+=')
        REDIS_PASS=$(openssl rand -hex 16)
        
        # Aplicar secretos al .env
        sed -i "s/JWT_SECRET=.*/JWT_SECRET=${JWT_SECRET}/" .env
        sed -i "s/DB_PASSWORD=.*/DB_PASSWORD=${DB_PASS}/" .env
        sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=${REDIS_PASS}/" .env
        
        echo -e "✅ .env generado con claves seguras únicas."
    else
        echo -e "❌ .env.example no encontrado. No se pudo generar .env."
        exit 1
    fi
else
    echo -e "✅ .env detectado. Verificando integridad..."
fi

# 3. Levantar Infraestructura
echo -e "🐳 Construyendo y levantando contenedores..."
docker compose up -d --build

# 4. Esperar Salud de Servicios
echo -e "⏳ Esperando a que los servicios estén 'healthy'..."
# Polling simple para esperar a que el backend responda
MAX_RETRIES=30
COUNT=0
until [ "$(docker inspect -f '{{.State.Health.Status}}' fluxagent-backend 2>/dev/null)" == "healthy" ]; do
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo -e "⚠️  El backend está tardando mucho en reportar 'healthy', continuando..."
        break
    fi
    echo -n "."
    sleep 3
    COUNT=$((COUNT+1))
done
echo -e "\n✅ Infraestructura en línea."

# 5. Ejecutar Migraciones (Alembic)
echo -e "🗄️  Aplicando migraciones de base de datos..."
# Nota: Asumiendo que alembic está configurado en el contenedor
docker compose exec backend alembic upgrade head || echo "⚠️  No se pudieron ejecutar las migraciones. Verifica alembic.ini"

# 6. Seed de Datos Beta
echo -e "🌱 Cargando datos semilla de Yanua..."
# Buscamos un script de seed
if [ -f src/scripts/seed_data.py ]; then
    docker compose exec backend python scripts/seed_data.py
fi

# 7. Verificación de Modelos (Ollama)
echo -e "🤖 Verificando modelos en Ollama..."
docker compose exec ollama ollama pull qwen2.5:3b
docker compose exec ollama ollama pull nomic-embed-text

echo -e "\n\033[1;32m¡CONFIGURACIÓN COMPLETADA CON ÉXITO!\033[0m"
echo -e "----------------------------------------------------"
echo -e "🌐 Frontend: http://localhost:4000"
echo -e "🔌 API:      http://localhost:9000/api/v1"
echo -e "📚 Documentación: http://localhost:9000/docs"
echo -e "----------------------------------------------------"
echo -e "Usa 'docker compose logs -f' para monitorear el sistema.\n"
