# 🏢 VENTACORE AI: FLUX-AGENT-V2 - DOCUMENTACIÓN MAESTRA Y RECUPERACIÓN (DISASTER RECOVERY)

> **Versión:** 2.1.0 (V2 Master - Actualizada Integralmente)
> **Fecha de Compilación:** 02 Mayo 2026
> **Proyecto:** SaaS Multi-Tenant de Agentes de Ventas con IA Local (Segunda Generación)
> **Directorio Raíz:** `/home/mister/flux-agent-v2`

Este documento es la **fuente de la verdad** del proyecto. Contiene toda la información necesaria para comprender la arquitectura, el código, el diseño, los flujos y, sobre todo, **cómo levantar el proyecto desde cero** en caso de pérdida total.

---

## 📋 ÍNDICE

1. [Arquitectura y Puertos V2](#1-arquitectura-y-puertos-v2)
2. [Estructura del Proyecto y Stack Tecnológico](#2-estructura-del-proyecto-y-stack-tecnologico)
3. [Cómo Levantar el Proyecto desde 0 (Disaster Recovery)](#3-cómo-levantar-el-proyecto-desde-0-disaster-recovery)
4. [Arquitectura de Portales y Roles](#4-arquitectura-de-portales-y-roles)
5. [Módulos del Super Admin (NOC)](#5-módulos-del-super-admin-noc)
6. [Módulos del Dashboard Cliente](#6-módulos-del-dashboard-cliente)
7. [Nuevo Módulo: Wizard de Ingesta RAG (6 Pasos)](#7-nuevo-módulo-wizard-de-ingesta-rag-6-pasos)
8. [Portal Corporativo (Enterprise)](#8-portal-corporativo-enterprise)
9. [Sistema de Autenticación y Seguridad (RLS)](#9-sistema-de-autenticacion-y-seguridad-rls)
10. [APIs, WebSockets y Routers del Backend](#10-apis-websockets-y-routers-del-backend)
11. [Base de Datos (Esquema Completo)](#11-base-de-datos-esquema-completo)
12. [Credenciales Maestras](#12-credenciales-maestras)
13. [Registro de Fallos Críticos y Resoluciones](#13-registro-de-fallos-criticos-y-resoluciones)
14. [Resumen de Implementación y Fases](#14-resumen-de-implementacion-y-fases)

---

## 1. ARQUITECTURA Y PUERTOS V2

A diferencia de la V1, **Flux-Agent V2** corre en un entorno completamente aislado para no interferir con las operaciones antiguas. Utiliza un monorepo Dockerizado.

### Mapa de Puertos Asignados (V2)

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| **Frontend (Next.js 16 - React 19)** | `3000`/`4000` | Local: 3000. Servidor: 4000 enlazado al túnel de Cloudflare |
| **Backend (FastAPI)** | `9000` | Internamente 8000 en el contenedor, expuesto como 9000 |
| **Base de Datos (PostgreSQL 16)** | `5434` | Instancia dedicada `fluxagent_v2` con extensión pgvector |
| **Caché (Redis 7)** | `6381` | Caché de sesiones, tokens y broker híbrido para colas |
| **Ollama (IA Local)** | `11434` | Reutiliza el contenedor `flux-ollama` en `fluxagent_network` |
| **Evolution API (WhatsApp)** | `8080` | Conector oficial de mensajería |

El archivo orquestador central es `docker-compose.yml`. Todos los servicios del backend se levantan a través de este archivo.

---

## 2. ESTRUCTURA DEL PROYECTO Y STACK TECNOLÓGICO

### Stack Tecnológico
- **Frontend**: Next.js 16 (App Router), React 19, Tailwind CSS, Lucide React, Zod + React Hook Form.
- **Backend**: Python 3.11, FastAPI, SQLAlchemy (Async), asyncpg, BackgroundTasks (Diseño Celery-Ready).
- **IA y RAG**: pgvector (PostgreSQL), Ollama (Modelos open source locales), OpenAI (Fallback).

### Árbol de Directorios Core
```text
/home/mister/flux-agent-v2/
├── docker-compose.yml           # Orquestador del backend V2
├── init-db.sql                  # Script maestro de la base de datos
├── master-v2.md                 # ESTE DOCUMENTO
├── frontend/                    # Aplicación Web Next.js 16
│   ├── src/app/
│   │   ├── page.tsx             # Landing Page
│   │   ├── login/, register/    # Autenticación y onboarding
│   │   ├── dashboard/           # Dashboard Cliente
│   │   │   ├── layout.tsx       # Menú lateral adaptativo por rol
│   │   │   ├── crm/              # CRM & Leads
│   │   │   ├── config/           # Configuración del agente
│   │   │   ├── entrenamiento/    # Wizard RAG de 6 Pasos (Base de Conocimiento)
│   │   │   ├── inventario/       # Catálogo de productos
│   │   │   ├── chat/             # Chat en Vivo
│   │   │   ├── equipo/           # Gestión de usuarios del tenant
│   │   │   └── facturacion/      # Facturación y Plan
│   │   ├── superadmin/           # Panel NOC
│   │   └── portal/               # Portal Corporativo (Enterprise)
│   └── package.json              # Dependencias
└── src/                         # Backend FastAPI
    ├── main.py                   # Entrypoint del API + Limiter Custom
    ├── auth.py                   # Lógica JWT y dependencias
    ├── config.py                 # Configuración global
    ├── database.py               # Conexión a PostgreSQL + RLS
    ├── core/
    │   └── task_runner.py        # Híbrido BackgroundTasks/Celery para Ingesta
    ├── agents/
    │   ├── base_agent.py         # Agente base
    │   └── sales_agent.py        # Agente de ventas
    ├── routers/
    │   ├── auth_router.py        # Autenticación
    │   ├── users_router.py       # Gestión de usuarios
    │   ├── agents_router.py      # Múltiples agentes IA
    │   ├── leads_router.py       # CRM & Leads
    │   ├── products_router.py    # Inventario
    │   ├── stats_router.py       # Estadísticas
    │   ├── whatsapp_router.py    # WhatsApp
    │   ├── webhooks_router.py    # Webhooks
    │   ├── admin_router.py       # Super Admin
    │   └── payments_router.py    # Pagos y facturación
    └── services/
        └── ingestion.py          # Ingesta de documentos RAG
```

---

## 3. CÓMO LEVANTAR EL PROYECTO DESDE 0 (DISASTER RECOVERY)

Para recuperar todo el sistema en caso de caída total, ejecutar los siguientes pasos en estricto orden:

### Paso 1: Clonar e Inicializar Base de Datos Backend
Asegúrate de tener Docker instalado.
```bash
cd /home/mister/flux-agent-v2
docker compose down -v  # Solo si necesitas limpiar un entorno corrupto
docker compose up -d --build
```

*Verificar que `fluxv2-backend` responda en el puerto 9000.*

### Paso 2: Compilación y Despliegue del Frontend
El frontend **NO DEBE** levantarse en el puerto 3000 si se usa en el servidor. Debe forzarse al puerto **4000** para respetar el proxy inverso.
```bash
cd /home/mister/flux-agent-v2/frontend
rm -rf .next node_modules package-lock.json # Limpieza obligatoria post-caída
npm install
pkill -f "next-server" || true
nohup npm run dev -- -p 4000 > frontend.log 2>&1 &
```

### Paso 3: Verificar Estado de Servicios
```bash
# Health Check del Backend
curl http://localhost:9000/health
# Prueba Frontend
curl http://localhost:4000/login
```

---

## 4. ARQUITECTURA DE PORTALES Y ROLES

El sistema cuenta con **5 portales diferenciados** según el tipo de usuario:

| # | Portal | Ruta | Acceso | Propósito |
|---|--------|------|--------|-----------|
| 1 | **Landing Page** | `/` | Público | Presentación, features, pricing |
| 2 | **Registro** | `/register` | Público | Crear cuenta (Individual/Empresa) |
| 3 | **Login** | `/login` | Público | Autenticación universal |
| 4 | **Super Admin** | `/superadmin` | `super_admin` | Gestión de toda la plataforma |
| 5 | **Dashboard Cliente** | `/dashboard` | `admin`, `viewer`, `agente` | Gestión del tenant |
| 6 | **Portal Corporativo** | `/portal` | `admin` (Enterprise) | Experiencia white-label |

### Roles y Permisos
| Rol | Portal | Permisos |
|-----|--------|----------|
| `super_admin` | `/superadmin/**` | Acceso total a toda la plataforma |
| `admin` | `/dashboard/**` + `/portal` | Control total del tenant |
| `viewer` | `/dashboard/*` (menú reducido) | Solo lectura |
| `agente` | `/dashboard/chat`, `/dashboard/crm` | Solo operativa (leads asignados) |

### Registro Dual
El formulario de registro soporta dos flujos:
- **Individual:** `/register?tipo=individual` (Nombre, Email, Plan).
- **Empresa (Marca Blanca):** `/register?tipo=empresa` (Requiere nombre de empresa y color de marca).

---

## 5. MÓDULOS DEL SUPER ADMIN (NOC)
*(Disponible en `/superadmin`)*

- **Dashboard NOC (`/superadmin`)**: KPIs globales, MRR, uptime.
- **Tenants HQ (`/superadmin/tenants`)**: Creación, suspensión e impersonación de tenants.
- **Planes y Billing (`/superadmin/billing`)**: Planes (Starter, Pro, Enterprise), historial, Gateways.
- **Staff del Sistema (`/superadmin/staff`)**: Soporte técnico y auditores NOC.
- **Modelos IA (`/superadmin/modelos`)**: Gestión de tokens (OpenAI, Ollama locales).
- **Agentes Globales (`/superadmin/agentes`)**: Plantillas de agentes y Prompts.
- **Tickets de Soporte (`/superadmin/tickets`)**: Bandeja y SLA.
- **Gateways (`/superadmin/gateways`)**: Instancias Evolution API y Webhooks.
- **Logs y Auditoría (`/superadmin/logs`)**: Logs en tiempo real filtrados por INFO/WARN/ERROR.
- **Terminal (`/superadmin/terminal`)**: Consola de emergencia y Health Checks.

---

## 6. MÓDULOS DEL DASHBOARD CLIENTE
*(Disponible en `/dashboard`)*

### Menú Admin (Completo)
- **Panel de Resumen** (`/dashboard`) - KPIs y gráficos
- **CRM & Leads** (`/dashboard/crm`) - Gestión de contactos y pipeline
- **Estrategia de Ventas** (`/dashboard/script`) - Reglas y comportamiento del agente IA
- **Entrenamiento RAG** (`/dashboard/entrenamiento`) - Wizard de Ingesta
- **Mi Inventario** (`/dashboard/inventario`) - Catálogo de productos
- **Conectores** (`/dashboard/conectores`) - WhatsApp, APIs
- **Chat en Vivo** (`/dashboard/chat`) - Conversaciones y Handoff
- **Mi Equipo** (`/dashboard/equipo`) - Gestión de usuarios
- **Facturación** (`/dashboard/facturacion`) - Plan y pagos

### Menú Viewer / Agente
El menú es dinámico y oculta la configuración, RAG, y facturación para roles inferiores.

---

## 7. NUEVO MÓDULO: WIZARD DE INGESTA RAG (6 PASOS)

Para evitar que los usuarios rompan el sistema cargando archivos mal formateados, el módulo de **Entrenamiento** (`/dashboard/entrenamiento`) fue rediseñado con un flujo estricto e interactivo de 6 pasos.

### Los 6 Pasos del Wizard:
1. **Selección de Fuente:** Archivo local (CSV, PDF, Excel), URL Web Scraping o Conexión a BD.
2. **Carga y Validación:** Zona *Drag & Drop* interactiva, cálculo real de peso (`formatFileSize`).
3. **Mapeo de Columnas:** Asignación inteligente de datos.
4. **Sincronización:** Definición de tareas periódicas.
5. **Procesamiento en Vivo (WebSockets):** Barra de progreso bidireccional conectada a FastAPI. Muestra fases: `parsing`, `chunking`, `embedding`, `indexing`.
6. **Validación (Buscador RAG):** Input de búsqueda para que el cliente pruebe la IA haciendo una pregunta.

### Mejoras Técnicas del Wizard:
- **Validación Asincrónica (Zod):** React Hook Form valida las etapas sin bloquear los botones de retorno.
- **TaskRunner Híbrido:** El backend implementa un patrón `Celery-Ready`. Actualmente usa `BackgroundTasks` de FastAPI (por eficiencia MVP), permitiendo migrar a Celery cambiando el flag `use_celery`.

---

## 8. PORTAL CORPORATIVO (ENTERPRISE)

El portal (`/portal`) es exclusivo para clientes del plan **Enterprise** con marca blanca:

### Características
- **Theming dinámico** - Logo y colores personalizados
- **Múltiples agentes IA** - Por área/departamento
- **Branding completo** - Color primario, secundaria, dominio propio
- **Seguridad Enterprise** - 2FA obligatorio, IP whitelist, políticas de contraseñas

---

## 9. SISTEMA DE AUTENTICACIÓN Y SEGURIDAD (RLS)

### JWT (JSON Web Tokens)
- Tokens firmados con HS256, expiración default 60 mins.
- Payload incluye: `sub`, `tenant_id`, `rol`, `nombre`, `plan`

### Row Level Security (RLS)
- PostgreSQL RLS asegura el aislamiento entre tenants.
- Variable de sesión `app.current_tenant_id` inyectada en FastAPI.
- Políticas en tablas: `usuarios`, `agents`, `knowledge_chunks`, `conversaciones`, `mensajes`, `canales_config`.

### Limiter / Rate Limiting Proxy Support
- Limitador personalizado (`limiter_get_remote_address`) en `main.py` lee `X-Forwarded-For` para evitar baneos si se usa Cloudflare o un balanceador de carga.

---

## 10. APIS, WEBSOCKETS Y ROUTERS DEL BACKEND

### Routers Implementados

| Router | Prefijo | Descripción |
|--------|---------|-------------|
| `auth_router` | `/api/v1/auth` | Login, registro, refresh |
| `users_router` | `/api/v1/users` | CRUD de usuarios del tenant |
| `agents_router` | `/api/v1/agents` | Múltiples agentes IA |
| `leads_router` | `/api/v1/leads` | CRM y leads |
| `products_router` | `/api/v1/products` | Inventario |
| `stats_router` | `/api/v1/stats` | Estadísticas y KPIs |
| `whatsapp_router` | `/api/v1/whatsapp` | WhatsApp (webhook, QR, status) |
| `webhooks_router` | `/api/v1/webhooks` | Webhooks entrantes |
| `admin_router` | `/api/v1/admin` | Super Admin |
| `payments_router` | `/api/v1/payments` | Pagos, facturas, cupones |
| `ingest_router` | `/api/v1/ingest` | RAG Wizard y WebSockets |

### Endpoints Principales

```python
# Autenticación
POST /api/v1/auth/register    # Registro con plan y branding
POST /api/v1/auth/login       # Login con JWT
POST /api/v1/auth/refresh     # Renovar token
GET  /api/v1/auth/me          # Perfil del usuario

# Usuarios del tenant
GET    /api/v1/users           # Listar usuarios
POST   /api/v1/users           # Crear usuario
PATCH  /api/v1/users/{id}      # Editar usuario
DELETE /api/v1/users/{id}      # Eliminar usuario

# Agentes IA
GET    /api/v1/agents            # Listar agentes
POST   /api/v1/agents            # Crear agente
GET    /api/v1/agents/{id}       # Ver agente
PATCH  /api/v1/agents/{id}       # Editar agente
DELETE /api/v1/agents/{id}       # Eliminar agente
POST   /api/v1/agents/{id}/test  # Probar agente

# Chat
POST /api/v1/chat                # Chat completo (respuesta única)
POST /api/v1/chat/stream         # Chat con streaming SSE

# RAG / Conocimiento / Wizard
GET    /api/v1/knowledge         # Listar documentos indexados
POST   /api/v1/ingest/start      # Subir archivo al Wizard RAG
WS     /ws/ingestion/{tenant_id} # WebSockets: Barra de progreso en vivo
DELETE /api/v1/knowledge/{name}  # Eliminar fuente

# Pagos
GET  /api/v1/payments/subscription    # Ver suscripción
POST /api/v1/payments/subscription    # Crear suscripción
GET  /api/v1/payments/invoices        # Listar facturas
POST /api/v1/payments/coupons         # Crear cupón (Super Admin)
POST /api/v1/payments/coupons/validate# Validar cupón
```

---

## 11. BASE DE DATOS (ESQUEMA COMPLETO)

### Extensiones Requeridas
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";  -- pgvector
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

### Tablas Principales

```sql
-- Tenants (Empresas/Clientes)
tenants:
  - id (UUID, PK)
  - nombre_empresa (VARCHAR)
  - email_contacto (VARCHAR, UNIQUE)
  - plan (VARCHAR) -- starter, pro, enterprise
  - estado (VARCHAR) -- activo, suspendido, cancelado
  - max_agentes, max_mensajes_mes, max_instancias_whatsapp
  - color_primario (VARCHAR) -- Para branding
  - branding_config (JSONB)
  - dominio_personalizado (VARCHAR)

-- Usuarios (del tenant)
usuarios:
  - id (UUID, PK)
  - tenant_id (UUID, FK)
  - email (VARCHAR, UNIQUE)
  - password_hash (VARCHAR)
  - nombre (VARCHAR)
  - rol (VARCHAR) -- super_admin, admin, viewer, agente
  - estado (VARCHAR)

-- Agentes IA (múltiples por tenant)
agents:
  - id (UUID, PK)
  - tenant_id (UUID, FK)
  - nombre (VARCHAR)
  - area (VARCHAR) -- ventas, soporte, rrhh, etc.
  - descripcion (TEXT)
  - genero, humor, personalidad (VARCHAR, TEXT)
  - coleccion_rag (VARCHAR) -- Colección de conocimiento
  - modelo, temperatura, max_tokens
  - canales (TEXT[])
  - horario_inicio, horario_fin (TIME)
  - mensaje_fuera_horario (TEXT)
  - estado (VARCHAR) -- entrenando, activo, pausado

-- Conocimiento (RAG)
knowledge_chunks:
  - id (UUID, PK)
  - tenant_id (UUID, FK)
  - agent_id (UUID, FK)
  - contenido (TEXT)
  - fuente_nombre (VARCHAR)
  - fuente_tipo (VARCHAR)
  - embedding (VECTOR(768))

-- Conversaciones y Mensajes
conversaciones:
  - id, tenant_id, agent_id
  - lead_externo_id (VARCHAR)
  - canal (VARCHAR) -- whatsapp, web_chat, etc.
  - estado, sentimiento, venta_cerrada, valor_venta
  - tokens_entrada, tokens_salida

mensajes:
  - id, conversacion_id, tenant_id
  - rol (VARCHAR) -- usuario, asistente, sistema
  - contenido (TEXT)
  - tokens (INT)

-- Canales (WhatsApp, etc.)
canales_config:
  - id, tenant_id, agent_id
  - canal (VARCHAR) -- whatsapp, telegram, instagram, web_chat
  - instancia_nombre (VARCHAR)
  - token_acceso, webhook_url (TEXT)
  - estado (VARCHAR)

-- Suscripciones y Facturas
subscriptions:
  - id, tenant_id, plan, estado
  - monto, moneda, periodo
  - fecha_inicio, fecha_proxima_renovacion

invoices:
  - id, tenant_id, subscription_id
  - numero, fecha_emision, fecha_vencimiento
  - monto, estado

coupons:
  - id, codigo, tipo_descuento, valor
  - valido_hasta, uso_maximo, uso_actual
```

---

## 12. CREDENCIALES MAESTRAS

Todas las cuentas iniciales han sido aseguradas con bcrypt (`$2b$12$...`).
**Contraseña universal temporal para desarrollo:** `Admin2026!`

| Rol | Email | Propósito |
|-----|-------|-----------|
| **Super Admin** | `admin@fluxagent.com` | Acceso total al NOC y plataformas. |
| **Admin Cliente** | `admin@labodegaec.com` | Propietario del tenant LaBodegaEC. |
| **Admin Cliente** | `maria@empresa-c.com` | Propietario del tenant Empresa C. |
| **Viewer** | `demo@labodegaec.com` | Empleado de solo lectura. |
| **Agente** | `agente@labodegaec.com` | Usuario operativo. |

---

## 13. REGISTRO DE FALLOS CRÍTICOS Y RESOLUCIONES

Este apartado histórico documenta errores profundos y cómo se resolvieron, para evitar repetir bugs en futuras actualizaciones.

1. **Caída 500 por Borrado de Caché `.next` en Vivo:**
   - **Problema:** Al limpiar caché de Next.js (`rm -rf .next`) mientras `npm run dev` corría, el sistema colapsaba devolviendo "Internal Server Error" globalmente.
   - **Solución:** Protocolo de reinicio en frío. Nunca borrar caché en caliente. Interrumpir proceso (`Ctrl+C`), eliminar `.next` y reiniciar `npm run dev`.

2. **Error de Tipado Zod en Formulario Wizard:**
   - **Problema:** Conflictos de inferencia de tipo entre `z.record(z.string())`, `.default(false)` de Zod y la expectativa de `React Hook Form`, causando "puntos rojos" y bloqueos de build en TypeScript.
   - **Solución:** Reemplazo por validaciones estrictas tipo `z.boolean().optional()` permitiendo validación limpia y AST correcto.

3. **Interbloqueo de Validación en Pasos de React (Step 1 a 2):**
   - **Problema:** `superRefine` de Zod evaluaba globalmente. Al dar "Siguiente" en el paso 1, pedía el archivo del paso 2 ocultamente y trancaba el flujo.
   - **Solución:** Eliminación del `superRefine` global y manejo manual asíncrono en `useIngestionWizard.ts`.

4. **Conflicto de Dependencias React 19 y Puertos (3000 vs 4000):**
   - **Problema:** Kanban crasheaba por `react-beautiful-dnd` y el proxy no enganchaba.
   - **Solución:** Migración a `@hello-pangea/dnd` y forzado de puerto con `-p 4000`.

5. **Bloqueo del Proxy en Rate Limiting (Cloudflare):**
   - **Problema:** Limitador de FastAPI bloqueaba al proxy pensando que era spammer.
   - **Solución:** Override con `limiter_get_remote_address` leyendo la cabecera `X-Forwarded-For`.

---

## 14. RESUMEN DE IMPLEMENTACIÓN Y FASES

### ✅ FASE 1: Core Funcional
- [x] Landing Page corregida
- [x] Register Dual (Individual/Empresa)
- [x] Portal Corporativo (/portal)
- [x] Gestión de Usuarios del Tenant
- [x] Middleware de Roles y RLS
- [x] Menús diferenciados por rol

### ✅ FASE 2: Super Admin Completo
- [x] Billing & Planes
- [x] Staff NOC
- [x] Logs & Auditoría
- [x] Terminal de Emergencia

### ✅ FASE 3: Enterprise / Marca Blanca
- [x] Múltiples Agentes IA por área
- [x] **NUEVO:** RAG Avanzado (Wizard de 6 Pasos interactivos, Drag&Drop, WebSockets)
- [x] Branding & Personalización
- [x] Seguridad Enterprise

### ✅ FASE 4: Monetización
- [x] Integración Mercado Pago
- [x] Facturas PDF
- [x] Cupones y Descuentos
- [x] Facturación en Dashboard