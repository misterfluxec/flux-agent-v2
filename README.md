# 🤖 Yanua AI — Enterprise Sales Platform (FluxAgent V2)

**Estado:** Beta Premium 🚀  
**Arquitectura:** Local-First, RAG-Powered, Multi-Tenant  
**Stack:** FastAPI, Next.js, PostgreSQL (pgvector), Ollama, Redis

---

## 🏗️ Arquitectura del Sistema
Yanua AI utiliza un motor de **Generación Aumentada por Recuperación (RAG)** de alto rendimiento:
- **Cerebro (LLM):** `qwen2.5:3b` vía Ollama (Optimizado para razonamiento rápido).
- **Memoria Semántica:** `nomic-embed-text` indexado en `pgvector`.
- **Ingesta:** Pipeline automático para Google Sheets, Excel y CSV.
- **Seguridad:** Aislamiento total por Tenant, contraseñas bcrypt y JWT rotativo.

---

## 🚀 Instalación Rápida (Beta)

### Requisitos
- Docker & Docker Compose v2+
- Mínimo 16GB RAM (32GB recomendado para i7)
- 10GB de espacio en disco para modelos de IA

### Despliegue en 1 paso
```bash
git clone https://github.com/tudominio/flux-agent-v2.git
cd flux-agent-v2
chmod +x setup_beta.sh
./setup_beta.sh
```

El script se encargará de:
1. Generar un entorno `.env` seguro con claves únicas.
2. Levantar toda la infraestructura (DB, Redis, Ollama, API, Web).
3. Aplicar migraciones de base de datos.
4. Descargar los modelos de IA necesarios.

---

## 🔌 Acceso
- **Aplicación Web:** [http://localhost:4000](http://localhost:4000)
- **API Swagger:** [http://localhost:9000/docs](http://localhost:9000/docs)
- **Ollama Engine:** [http://localhost:11434](http://localhost:11434)

---

## 🧪 Comandos Útiles

### Ver logs en tiempo real
```bash
docker compose logs -f
```

### Reiniciar un servicio
```bash
docker compose restart backend
```

### Ejecutar Tests E2E
```bash
docker compose exec backend python tests/e2e/test_data_ingestion_flow.py
```

---

## 🔒 Seguridad
- **JWT_SECRET:** Generado automáticamente por el script de setup. Nunca lo compartas.
- **Base de Datos:** No expone el puerto 5432 en redes públicas (usa puerto 5434 en localhost).
- **Aislamiento:** Cada Tenant tiene su propia `tenant_id` que filtra todas las queries de SQL y Vectores.

---

© 2026 Yanua AI - Todos los derechos reservados.
