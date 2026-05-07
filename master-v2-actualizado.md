# 🏢 FLUXAGENT V2 - DOCUMENTACIÓN MAESTRA ACTUALIZADA

> **Versión:** 2.2.0 (Estado Real - 06 Mayo 2026)
> **Fecha de Actualización:** 06 Mayo 2026
> **Proyecto:** SaaS Multi-Tenant de Agentes de Ventas con IA Local
> **Directorio Raíz:** `/home/mister/flux-agent-v2`

Este documento refleja el **estado actual real** del sistema basado en análisis directo del código y configuración activa.

---

## 📋 ÍNDICE

1. [Estado Actual del Sistema](#1-estado-actual-del-sistema)
2. [Arquitectura y Componentes](#2-arquitectura-y-componentes)
3. [Credenciales y Acceso](#3-credenciales-y-acceso)
4. [API Endpoints Disponibles](#4-api-endpoints-disponibles)
5. [Base de Datos Actual](#5-base-de-datos-actual)
6. [Flujos de Autenticación](#6-flujos-de-autenticación)
7. [Configuración de Servicios](#7-configuración-de-servicios)
8. [Issues y Soluciones](#8-issues-y-soluciones)

---

## 1. ESTADO ACTUAL DEL SISTEMA

### ✅ **Servicios Operativos**
- **Backend API**: http://localhost:9000 (FastAPI)
- **Frontend**: http://localhost:4000 (Next.js 16)
- **PostgreSQL**: localhost:5434 (pgvector habilitado)
- **Redis**: localhost:6381 (Cache y colas)
- **Ollama**: Deshabilitado temporalmente (conflicto puerto 11434)

### 🔧 **Stack Tecnológico Real**
```
Backend: Python 3.11, FastAPI 0.115.0, SQLAlchemy 2.0.36
Frontend: Next.js 16.2.4, React 19.2.4, TypeScript 5
Database: PostgreSQL 16 + pgvector, Redis 7
IA: Ollama (qwen2.5:3b, nomic-embed-text) - Temporalmente offline
Infra: Docker Compose, puertos mapeados
```

---

## 2. ARQUITECTURA Y COMPONENTES

### **Estructura de Routers (25 módulos)**
```
/src/routers/
├── auth_router.py          # Autenticación (login, register, JWT)
├── admin_router.py         # Super Admin (tenants, planes, modelos)
├── agents_router.py        # Gestión de agentes IA
├── users_router.py         # Gestión de usuarios del tenant
├── leads_router.py         # CRM y leads
├── products_router.py      # Catálogo de productos
├── stats_router.py         # Estadísticas y KPIs
├── whatsapp_router.py      # WhatsApp integration
├── webhooks_router.py      # Webhooks entrantes
├── payments_router.py      # Pagos y facturación
├── ingest_router.py        # RAG y data ingestion
├── voice_router.py         # Voz y TTS/STT
├── channels_router.py      # Canales de comunicación
├── quota_router.py         # Cuotas y límites
├── sync_router.py          # Sincronización de datos
├── upload_router.py        # Subida de archivos
├── oauth_sync_router.py    # Sincronización OAuth
├── whatsapp_cloud_router.py # WhatsApp Cloud API
├── whatsapp_health_router.py # Health checks WhatsApp
└── ... (módulos adicionales)
```

### **Componentes Core**
```
/src/core/
├── encryption.py           # Servicios de encriptación
├── llm/router.py          # Router LLM
├── metrics.py             # Métricas Prometheus
├── plan_manager.py        # Gestión de planes
└── task_runner.py         # Ejecución de tareas
```

---

## 3. CREDENCIALES Y ACCESO

### 🔐 **Credenciales Válidas (Estado Real)**
```
Email: admin@fluxagent.com
Password: Admin2026!
Rol: super_admin
Plan: enterprise
Tenant ID: 11111111-1111-1111-1111-111111111111
```

### 🎯 **Flujo de Login Funcional**
```bash
# Login exitoso verificado:
curl -X POST http://localhost:9000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@fluxagent.com", "password": "Admin2026!"}'

# Retorna JWT válido con 60 min de expiración
```

---

## 4. API ENDPOINTS DISPONIBLES

### **Autenticación**
- `POST /api/v1/auth/login` - Login y obtención de JWT
- `GET /api/v1/auth/me` - Perfil del usuario actual
- `POST /api/v1/auth/register` - Registro de nuevos tenants
- `POST /api/v1/auth/refresh` - Renovación de token
- `POST /api/v1/auth/social` - Login social (Google, Microsoft)

### **Administración (Super Admin)**
- `GET /api/v1/admin/tenants` - Gestión de tenants
- `GET /api/v1/admin/models` - Gestión de modelos IA
- `POST /api/v1/admin/models/pull` - Descargar modelos
- `GET /api/v1/admin/sysinfo` - Información del sistema
- `GET /api/v1/admin/tickets` - Tickets de soporte

### **Agentes IA**
- `GET /api/v1/agents` - Listar agentes del tenant
- `POST /api/v1/agents` - Crear nuevo agente
- `GET /api/v1/agents/{agent_id}` - Detalles del agente
- `POST /api/v1/agents/{agent_id}/test` - Probar agente
- `PUT /api/v1/agents/{agent_id}/avatar` - Actualizar avatar

### **Canales y Comunicación**
- `GET /api/v1/channels/health` - Health check de canales
- `GET /api/v1/channels/supported` - Canales soportados
- `POST /api/v1/channels/telegram/webhook` - Webhook Telegram

---

## 5. BASE DE DATOS ACTUAL

### **Tablas Principales Verificadas**
```sql
-- Tenants (Empresas/Clientes)
tenants: id, nombre_empresa, email_contacto, plan, estado, 
         max_agentes, max_mensajes_mes, color_primario, 
         branding_config, dominio_personalizado

-- Usuarios (del tenant)
usuarios: id, tenant_id, email, password_hash, nombre, rol, 
          estado, ultimo_login

-- Agentes IA
agents: id, tenant_id, nombre, area, descripcion, genero, 
        humor, personalidad, coleccion_rag, modelo, 
        temperatura, max_tokens, canales, estado

-- Conocimiento RAG
knowledge_chunks: id, tenant_id, agent_id, contenido, 
                   fuente_nombre, fuente_tipo, embedding

-- Conversaciones
conversaciones: id, tenant_id, agent_id, lead_externo_id, 
                canal, estado, sentimiento, venta_cerrada

-- Canales Configuración
canales_config: id, tenant_id, agent_id, canal, instancia_nombre, 
                token_acceso, webhook_url, estado
```

### **Funciones Críticas**
```sql
-- Función de login (creada y verificada)
CREATE OR REPLACE FUNCTION fn_login_usuario(p_email VARCHAR)
RETURNS TABLE(id UUID, tenant_id UUID, password_hash VARCHAR, 
              nombre VARCHAR, rol VARCHAR, plan VARCHAR, 
              nombre_empresa VARCHAR, estado_tenant VARCHAR);
```

---

## 6. FLUJOS DE AUTENTICACIÓN

### **🔑 Flujo Login Real**
1. **Request**: `POST /api/v1/auth/login` con `{email, password}`
2. **Validación**: Función `fn_login_usuario()` con SECURITY DEFINER
3. **Verificación**: bcrypt hash verification
4. **Token**: JWT con payload `{sub, tenant_id, rol, nombre, plan, exp}`
5. **Response**: `{access_token, usuario: {...}}`

### **🛡️ Seguridad Implementada**
- **JWT Tokens**: HS256 con expiración 60 minutos
- **Row Level Security**: Políticas por tenant_id
- **Password Hash**: bcrypt con salt rounds 12
- **RLS Context**: `app.current_tenant_id` inyectado por request

---

## 7. CONFIGURACIÓN DE SERICIOS

### **Docker Compose (Estado Real)**
```yaml
services:
  postgres:     # localhost:5434 → 5432
    image: pgvector/pgvector:pg16
    healthcheck: pg_isready
    
  redis:        # localhost:6381 → 6379  
    image: redis:7-alpine
    command: redis-server --requirepass redisflux2026
    
  backend:      # localhost:9000 → 8000
    build: ./src
    depends_on: [postgres, redis]
    
  frontend:     # localhost:4000 → 3000
    build: ./frontend
    depends_on: [backend]
    
  ollama:       # localhost:11434 (temporalmente offline)
    image: ollama/ollama:latest
```

### **Variables de Entorno Críticas**
```bash
DATABASE_URL=postgresql://fluxadmin:fluxsecure2026@postgres:5432/fluxagent_v2
REDIS_URL=redis://:redisflux2026@redis:6379/0
JWT_SECRET=cambiar_en_produccion_jwt_secret
OLLAMA_BASE_URL=http://ollama:11434
NEXT_PUBLIC_API_URL=http://localhost:9000/api/v1
```

---

## 8. ISSUES Y SOLUCIONES

### ✅ **Problemas Resueltos**
1. **Error `fn_login_usuario` no existente**
   - **Solución**: Creada función SQL con SECURITY DEFINER
   - **Estado**: ✅ Funcional

2. **Password hash placeholder**
   - **Solución**: Actualizado con bcrypt hash real
   - **Estado**: ✅ Funcional

3. **Import Pipeline en voice_pipeline_service**
   - **Solución**: Corregidos imports condicionales
   - **Estado**: ✅ Backend estable

4. **Login no redirige en frontend**
   - **Causa**: Backend caído por errores de importación
   - **Solución**: Backend restaurado y funcional
   - **Estado**: ✅ Login API funciona

### ⚠️ **Issues Pendientes**
1. **Ollama Service Offline**
   - **Problema**: Conflicto puerto 11434 con proceso local
   - **Impacto**: Funciones IA locales no disponibles
   - **Solución**: Matar proceso local o cambiar puerto

2. **Frontend URL Configuration**
   - **Problema**: Frontend apunta a `https://api.labodegaec.com`
   - **Impacto**: Login desde frontend puede fallar
   - **Solución**: Actualizar NEXT_PUBLIC_API_URL

---

## 🚀 **PRÓXIMOS PASOS**

### **Inmediato (Hoy)**
1. **Habilitar Ollama**: Resolver conflicto de puerto
2. **Actualizar Frontend Config**: Apuntar a localhost:9000
3. **Probar Flujo Completo**: Login → Dashboard

### **Corto Plazo (Esta Semana)**
1. **Crear Usuarios de Prueba**: Admin, Viewer, Agente
2. **Probar Multi-Tenant**: Crear nuevo tenant
3. **Validar RAG Flow**: Ingesta y consulta

### **Mediano Plazo (Próximo Mes)**
1. **Actualizar Documentación**: Master-V2 con estado real
2. **Crear Scripts de Setup**: Automatizar despliegue
3. **Implementar Monitoring**: Métricas y alertas

---

## 📞 **CONTACTO Y SOPORTE**

- **Backend Health**: http://localhost:9000/health
- **API Endpoints**: http://localhost:9000/openapi.json
- **Logs Tiempo Real**: `docker compose logs -f backend`
- **DB Access**: `docker compose exec postgres psql -U fluxadmin -d fluxagent_v2`

---

**Última Actualización**: 06 Mayo 2026 - 03:25 UTC  
**Estado**: ✅ Sistema funcional con login operativo  
**Prioridad**: Habilitar Ollama y configurar frontend local
