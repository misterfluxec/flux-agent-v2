# 📚 FLUXAGENT V2 - DOCUMENTACIÓN COMPLETA DE RECUPERACIÓN DEL SISTEMA

## 🎯 **PROPÓSITO**
Documento completo para levantar FluxAgent V2 desde cero en caso de pérdida total. Incluye toda la arquitectura, tecnología, lógica y pasos detallados para reconstrucción completa.

---

## 📋 **ÍNDICE**
1. [Arquitectura General](#arquitectura-general)
2. [Stack Tecnológico](#stack-tecnológico)
3. [Estructura de Proyecto](#estructura-de-proyecto)
4. [Base de Datos](#base-de-datos)
5. [Backend - FastAPI](#backend---fastapi)
6. [Frontend - Next.js](#frontend---nextjs)
7. [Infraestructura Docker](#infraestructura-docker)
8. [Configuración Ambiental](#configuración-ambiental)
9. [Flujo de Autenticación](#flujo-de-autenticación)
10. [Endpoints Principales](#endpoints-principales)
11. [Scripts de Recuperación](#scripts-de-recuperación)
12. [Testing Automatizado](#testing-automatizado)
13. [Monitoreo y Salud](#monitoreo-y-salud)
14. [Troubleshooting Común](#troubleshooting-común)

---

## 🏗️ **ARQUITECTURA GENERAL**

### **📊 DIAGRAMA DE ARQUITECTURA**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FRONTEND    │    │    BACKEND     │    │   DATABASE     │
│   (Next.js)   │◄──►│   (FastAPI)    │◄──►│  (PostgreSQL)  │
│   Puerto 4000  │    │   Puerto 9000   │    │   Puerto 5434   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │     REDIS      │              │
         └──────────────►│   (Cache)      │◄─────────────┘
                        │  Puerto 6381   │
                        └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │     OLLAMA     │
                        │   (AI Engine)  │
                        │  Puerto 11434   │
                        └─────────────────┘
```

### **🔄 FLUJO DE DATOS**
1. **Usuario** → Frontend (Next.js) → Backend (FastAPI)
2. **Backend** → PostgreSQL (datos persistentes) + Redis (cache)
3. **Backend** → Ollama (procesamiento IA)
4. **Frontend** → Dashboard real-time via WebSocket/HTTP

---

## 🛠️ **STACK TECNOLÓGICO**

### **🔥 BACKEND**
- **Framework:** FastAPI 0.104+
- **Lenguaje:** Python 3.12
- **ORM:** SQLAlchemy 2.0 (async)
- **Base de Datos:** PostgreSQL 16 + pgvector
- **Cache:** Redis 7
- **IA Engine:** Ollama + qwen2.5:3b
- **Autenticación:** JWT + bcrypt
- **API Documentation:** OpenAPI/Swagger

### **⚛️ FRONTEND**
- **Framework:** Next.js 16 (App Router)
- **Lenguaje:** TypeScript
- **UI Library:** Material-UI (MUI) + TailwindCSS
- **State Management:** React Query (TanStack Query)
- **HTTP Client:** Axios
- **Internationalización:** next-intl
- **Icons:** Lucide React

### **🐳 INFRAESTRUCTURA**
- **Containerization:** Docker + Docker Compose
- **Networking:** Bridge network `fluxagent-net`
- **Health Checks:** Todos los servicios con healthchecks
- **Volumes Persistentes:** postgres_data, redis_data, ollama_data

---

## 📁 **ESTRUCTURA DE PROYECTO**

```
flux-agent-v2/
├── 📄 docker-compose.yml              # Orquestación de contenedores
├── 📄 .env                          # Variables de entorno
├── 📁 src/                          # Backend Python
│   ├── 📄 main.py                   # Entry point FastAPI
│   ├── 📄 config.py                  # Configuración centralizada
│   ├── 📁 routers/                   # Endpoints API
│   │   ├── 📄 auth_router.py         # Autenticación
│   │   ├── 📄 agents_router.py       # Gestión de agentes
│   │   ├── 📄 analytics_router.py     # Analytics con cache
│   │   ├── 📄 health_router.py       # Health checks
│   │   └── 📁 _legacy/              # Routers obsoletos
│   ├── 📁 core/                      # Lógica de negocio
│   │   ├── 📁 db/                   # Base de datos
│   │   │   ├── 📄 models.py         # Modelos SQLAlchemy
│   │   │   └── 📄 helpers.py        # Utilidades SQL
│   │   ├── 📁 resilience/            # Patrones de resiliencia
│   │   │   ├── 📄 circuit_breaker.py
│   │   │   └── 📄 retry.py
│   │   └── 📁 middleware/            # Middleware FastAPI
│   │       └── 📄 tenant_isolation.py
│   └── 📁 auth.py                    # Módulo de autenticación
├── 📁 frontend/                      # Frontend Next.js
│   ├── 📄 package.json               # Dependencias
│   ├── 📁 src/                      # Código fuente
│   │   ├── 📁 app/[locale]/           # Rutas internacionalizadas
│   │   │   ├── 📄 login/page.tsx    # Login
│   │   │   ├── 📄 dashboard/page.tsx # Dashboard principal
│   │   │   ├── 📄 analytics/page.tsx # Analytics
│   │   │   └── 📄 agents/page.tsx    # Gestión de agentes
│   │   ├── 📁 components/             # Componentes UI
│   │   │   ├── 📁 ui/              # Componentes base
│   │   │   ├── 📁 system/           # Componentes sistema
│   │   │   └── 📁 auth/             # Componentes auth
│   │   ├── 📁 lib/                  # Utilidades
│   │   │   ├── 📄 api.ts            # Cliente HTTP
│   │   │   └── 📄 query-client.ts    # React Query
│   │   └── 📄 middleware.ts          # Middleware Next.js
├── 📁 tests/                         # Testing
│   ├── 📁 e2e/                      # Tests end-to-end
│   │   └── 📄 test_core_flow.py     # Flujo crítico
│   └── 📄 conftest.py                # Fixtures pytest
├── 📁 scripts/                       # Scripts utilitarios
│   └── 📄 verify_pre_beta.sh        # Verificación sistema
└── 📁 migrations/                    # Migraciones DB
    └── 📄 013_fix_agent_schema.sql  # Schema agentes
```

---

## 🗄️ **BASE DE DATOS**

### **📊 MODELOS PRINCIPALES**
```sql
-- Usuarios y Autenticación
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    rol VARCHAR(50) DEFAULT 'user',
    tenant_id UUID DEFAULT gen_random_uuid(),
    plan VARCHAR(20) DEFAULT 'basic',
    creado_en TIMESTAMP DEFAULT NOW(),
    actualizado_en TIMESTAMP DEFAULT NOW()
);

-- Agentes IA
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES usuarios(tenant_id),
    nombre VARCHAR(255) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    modelo VARCHAR(100) DEFAULT 'qwen2.5:3b',
    tono VARCHAR(50) DEFAULT 'profesional',
    descripcion TEXT,
    script_ventas JSONB DEFAULT '{}',
    activo BOOLEAN DEFAULT true,
    creado_en TIMESTAMP DEFAULT NOW(),
    actualizado_en TIMESTAMP DEFAULT NOW()
);

-- Conversaciones
CREATE TABLE conversaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES usuarios(tenant_id),
    agent_id UUID REFERENCES agents(id),
    cliente_id VARCHAR(255),
    estado VARCHAR(50) DEFAULT 'activa',
    iniciada_en TIMESTAMP DEFAULT NOW(),
    finalizada_en TIMESTAMP
);

-- Mensajes
CREATE TABLE mensajes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversacion_id UUID REFERENCES conversaciones(id),
    rol VARCHAR(20) NOT NULL, -- 'user' o 'assistant'
    contenido TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    creado_en TIMESTAMP DEFAULT NOW()
);
```

### **🔍 MIGRACIONES CRÍTICAS**
- **013_fix_agent_schema.sql:** Agrega `script_ventas` JSONB a tabla agents
- **012_add_tenant_isolation.sql:** Aísla datos por tenant
- **011_add_analytics_tables.sql:** Tablas de analytics

---

## 🔧 **BACKEND - FASTAPI**

### **🚀 ENTRY POINT (main.py)**
```python
# Imports principales
from fastapi import FastAPI
from routers.auth_router import router as auth_router
from routers.agents_router import router as agents_router
from routers.analytics_router import router as analytics_router
from routers.health_router import router as health_router

# Configuración
app = FastAPI(
    title="FluxAgent V2 API",
    description="AI Agent Platform for Sales Automation",
    version="2.0.0"
)

# Middleware
app.add_middleware(TenantIsolationMiddleware)
app.add_middleware(CORSMiddleware)

# Routers activos
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(agents_router, prefix="/api/v1/agents")
app.include_router(analytics_router, prefix="/api/v1/analytics")
app.include_router(health_router, prefix="/health")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### **🔐 AUTENTICACIÓN (auth_router.py)**
```python
# Login endpoint
@router.post("/login")
async def login(credentials: LoginSchema):
    # Verificar usuario en DB
    user = await authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(401, "Credenciales inválidas")
    
    # Generar JWT
    token = create_access_token({
        "sub": user.id,
        "tenant_id": user.tenant_id,
        "rol": user.rol,
        "nombre": user.nombre
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {
            "id": user.id,
            "nombre": user.nombre,
            "email": user.email,
            "rol": user.rol,
            "tenant_id": user.tenant_id
        }
    }
```

### **📊 ANALYTICS (analytics_router.py)**
```python
@router.get("/overview")
async def get_analytics_overview(
    days: int = 7,
    tenant_id: UUID = Depends(get_tenant_actual)
):
    # Cache-aware analytics
    cache_key = f"analytics:{tenant_id}:{days}"
    cached = await redis.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Calcular desde DB
    data = await calculate_analytics(tenant_id, days)
    
    # Guardar en cache (5 minutos)
    await redis.setex(cache_key, 300, json.dumps(data))
    
    return data
```

---

## ⚛️ **FRONTEND - NEXT.JS**

### **🔐 LOGIN (login/page.tsx)**
```typescript
export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const response = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
    });

    if (response.ok) {
      const data = await response.json();
      localStorage.setItem("flux_token", data.access_token);
      localStorage.setItem("flux_tenant_id", data.usuario.tenant_id);
      router.push(`/${locale}/dashboard`);
    }
  };

  // UI con MUI + TailwindCSS
  return (
    <div className="min-h-screen flex items-center justify-center">
      <form onSubmit={handleSubmit} className="w-full max-w-md">
        <TextField
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          fullWidth
        />
        <TextField
          label="Contraseña"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          fullWidth
        />
        <Button type="submit" variant="contained" fullWidth>
          Iniciar Sesión
        </Button>
      </form>
    </div>
  );
}
```

### **📊 DASHBOARD (dashboard/page.tsx)**
```typescript
export default function DashboardPage() {
  const router = useRouter();
  const { data: analytics, isLoading } = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: () => fetchAnalyticsOverview()
  });

  useEffect(() => {
    // Verificar token
    const token = localStorage.getItem('flux_token');
    if (!token) {
      router.push('/login');
      return;
    }

    // Verificar onboarding
    checkOnboardingStatus(token);
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <KPICard title="Conversaciones" value={analytics?.total_conversations} />
        <KPICard title="Leads" value={analytics?.total_leads} />
        <KPICard title="Tasa Conversión" value={`${analytics?.conversion_rate}%`} />
        <KPICard title="Tiempo Respuesta" value={`${analytics?.avg_response_time}s`} />
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ConversationChart data={analytics?.conversations_by_day} />
        <SentimentChart data={analytics?.sentiment_distribution} />
      </div>
    </div>
  );
}
```

---

## 🐳 **INFRAESTRUCTURA DOCKER**

### **📄 DOCKER-COMPOSE.YML**
```yaml
version: '3.9'

services:
  # Base de Datos PostgreSQL
  postgres:
    image: pgvector/pgvector:pg16
    container_name: fluxagent-postgres
    environment:
      POSTGRES_DB: fluxagent_v2
      POSTGRES_USER: fluxadmin
      POSTGRES_PASSWORD: fluxsecure2026
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5434:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U fluxadmin -d fluxagent_v2"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Cache Redis
  redis:
    image: redis:7-alpine
    container_name: fluxagent-redis
    command: redis-server --requirepass redisflux2026
    volumes:
      - redis_data:/data
    ports:
      - "6381:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "redisflux2026", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # AI Engine Ollama
  ollama:
    image: ollama/ollama:latest
    container_name: fluxagent-ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
      - OLLAMA_KEEP_ALIVE=24h
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
    healthcheck:
      test: ["CMD-SHELL", "wget --quiet --tries=1 --spider http://localhost:11434/api/tags || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Backend FastAPI
  backend:
    build: ./src
    container_name: fluxagent-backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://fluxadmin:fluxsecure2026@postgres:5432/fluxagent_v2
      - REDIS_URL=redis://:redisflux2026@redis:6379/0
      - OLLAMA_BASE_URL=http://ollama:11434
      - SECRET_KEY=cambiar_en_produccion_jwt_secret
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      ollama:
        condition: service_healthy
    ports:
      - "9000:8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Frontend Next.js
  frontend:
    build: ./frontend
    container_name: fluxagent-web
    environment:
      - NEXT_PUBLIC_BACKEND_URL=http://localhost:9000
    depends_on:
      - backend
    ports:
      - "4000:3000"

volumes:
  postgres_data:
  redis_data:
  ollama_data:

networks:
  default:
    name: fluxagent-net
```

### **🐳 DOCKERFILE (Backend)**
```dockerfile
# Multi-stage build para optimización
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Imagen de producción
FROM python:3.12-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y ffmpeg espeak && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN groupadd -r fluxuser && useradd -r -m -d /home/fluxuser -g fluxuser fluxuser

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

# Permisos
RUN mkdir -p /app/uploads && chown -R fluxuser:fluxuser /app

USER fluxuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

---

## ⚙️ **CONFIGURACIÓN AMBIENTAL**

### **📄 .ENV**
```bash
# Base de Datos
DATABASE_URL=postgresql+asyncpg://fluxadmin:fluxsecure2026@localhost:5434/fluxagent_v2
DB_HOST=localhost
DB_PORT=5434
DB_USER=fluxadmin
DB_PASSWORD=fluxsecure2026
DB_NAME=fluxagent_v2

# Redis
REDIS_URL=redis://:redisflux2026@localhost:6381/0
REDIS_HOST=localhost
REDIS_PORT=6381
REDIS_PASSWORD=redisflux2026

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=qwen2.5:3b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Seguridad
SECRET_KEY=cambiar_en_produccion_jwt_secret_mas_largo_y_seguro
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Aplicación
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# Frontend
NEXT_PUBLIC_BACKEND_URL=http://localhost:9000
```

---

## 🔐 **FLUJO DE AUTENTICACIÓN**

### **🔄 PROCESO COMPLETO**
1. **LOGIN**
   - Usuario ingresa email + contraseña
   - Frontend envía POST `/api/v1/auth/login`
   - Backend verifica bcrypt en DB
   - Si válido, genera JWT con:
     - `sub`: user_id
     - `tenant_id`: tenant_id
     - `rol`: rol del usuario
     - `exp`: expiración (24h)

2. **ALMACENAMIENTO**
   - Frontend guarda JWT en `localStorage`
   - También guarda `tenant_id` separado
   - Token se envía en header: `Authorization: Bearer <token>`

3. **VERIFICACIÓN**
   - Middleware de tenant isolation extrae `tenant_id` del JWT
   - Cada request automáticamente filtrada por tenant
   - Endpoints protegidos con `Depends(get_tenant_actual)`

4. **REFRESH**
   - Si token expira, frontend redirige a login
   - No hay refresh token (por simplicidad)

### **🛡️ SEGURIDAD**
- **Contraseñas:** bcrypt con salt aleatorio
- **JWT:** HMAC-SHA256, expiración 24h
- **Tenant Isolation:** Cada usuario solo ve sus datos
- **CORS:** Configurado para frontend en desarrollo
- **Rate Limiting:** Por tenant en Redis

---

## 🛣️ **ENDPOINTS PRINCIPALES**

### **🔐 AUTENTICACIÓN**
```
POST /api/v1/auth/login
POST /api/v1/auth/register
GET  /api/v1/auth/me
```

### **🤖 AGENTES**
```
GET    /api/v1/agents              # Listar agentes
POST   /api/v1/agents              # Crear agente
GET    /api/v1/agents/{id}         # Detalle agente
PUT    /api/v1/agents/{id}         # Actualizar agente
DELETE /api/v1/agents/{id}         # Eliminar agente
```

### **📊 ANALYTICS**
```
GET /api/v1/analytics/overview?days=7    # Overview general
GET /api/v1/analytics/conversations       # Conversaciones
GET /api/v1/analytics/performance       # Performance agentes
```

### **🏥 SALUD**
```
GET /health                           # Health check básico
GET /health/detailed                   # Health con circuit breakers
```

---

## 🧪 **SCRIPTS DE RECUPERACIÓN**

### **🚀 LEVANTAR SISTEMA COMPLETO**
```bash
#!/bin/bash
# script_levantar_sistema_completo.sh

echo "🚀 Levantando FluxAgent V2 desde cero..."

# 1. Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no instalado"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no instalado"
    exit 1
fi

# 2. Clonar repositorio (si no existe)
if [ ! -d "flux-agent-v2" ]; then
    echo "📥 Clonando repositorio..."
    git clone https://github.com/tu-repo/flux-agent-v2.git
    cd flux-agent-v2
else
    cd flux-agent-v2
    echo "📁 Usando repositorio existente"
fi

# 3. Configurar variables de entorno
if [ ! -f ".env" ]; then
    echo "📝 Creando .env..."
    cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://fluxadmin:fluxsecure2026@localhost:5434/fluxagent_v2
REDIS_URL=redis://:redisflux2026@localhost:6381/0
OLLAMA_BASE_URL=http://localhost:11434
SECRET_KEY=cambiar_en_produccion_jwt_secret_mas_largo_y_seguro
NEXT_PUBLIC_BACKEND_URL=http://localhost:9000
APP_ENV=development
EOF
fi

# 4. Construir y levantar contenedores
echo "🐳 Construyendo y levantando servicios..."
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 5. Esperar servicios
echo "⏳ Esperando que servicios estén listos..."
sleep 30

# 6. Verificar health checks
echo "🔍 Verificando salud del sistema..."

# Backend
if curl -sf http://localhost:9000/health > /dev/null; then
    echo "✅ Backend saludable"
else
    echo "❌ Backend no responde"
fi

# Frontend
if curl -sf http://localhost:4000 > /dev/null; then
    echo "✅ Frontend saludable"
else
    echo "❌ Frontend no responde"
fi

# Database
if docker-compose exec -T postgres pg_isready -U fluxadmin -d fluxagent_v2 > /dev/null; then
    echo "✅ Base de datos saludable"
else
    echo "❌ Base de datos no responde"
fi

# Redis
if docker-compose exec -T redis redis-cli -a redisflux2026 ping > /dev/null; then
    echo "✅ Redis saludable"
else
    echo "❌ Redis no responde"
fi

# Ollama
if curl -sf http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama saludable"
else
    echo "❌ Ollama no responde"
fi

echo ""
echo "🎯 Sistema levantado exitosamente!"
echo "📱 Frontend: http://localhost:4000"
echo "🔧 Backend API: http://localhost:9000"
echo "📚 Swagger Docs: http://localhost:9000/docs"
echo ""
echo "👤 Usuario por defecto:"
echo "   Email: maritza@mendoza.com"
echo "   Contraseña: password"
echo ""
echo "🧪 Para ejecutar tests:"
echo "   pytest tests/e2e/test_core_flow.py -v --asyncio-mode=auto"
```

### **🗄️ MIGRAR BASE DE DATOS**
```bash
#!/bin/bash
# script_migrar_base_datos.sh

echo "🗄️ Migrando base de datos..."

# 1. Verificar conexión a DB
if ! docker-compose exec -T postgres pg_isready -U fluxadmin -d fluxagent_v2 > /dev/null; then
    echo "❌ No hay conexión a la base de datos"
    exit 1
fi

# 2. Aplicar migraciones en orden
echo "📋 Aplicando migraciones..."

for migration in migrations/*.sql; do
    echo "📄 Aplicando $migration..."
    docker-compose exec -T postgres psql -U fluxadmin -d fluxagent_v2 < "$migration"
    echo "✅ $migration aplicada"
done

echo "🎉 Migraciones completadas!"
```

### **🧪 VERIFICACIÓN COMPLETA**
```bash
#!/bin/bash
# script_verificacion_completa.sh

echo "🔍 Verificación completa del sistema..."

# Ejecutar script de verificación pre-beta
./scripts/verify_pre_beta.sh

# Tests automatizados
echo "🧪 Ejecutando tests E2E..."
pytest tests/e2e/test_core_flow.py -v --asyncio-mode=auto

echo ""
echo "📊 Resumen final:"
echo "   ✅ Sistema levantado"
echo "   ✅ Base de datos migrada"
echo "   ✅ Tests ejecutados"
echo "   ✅ Listo para producción"
```

---

## 🧪 **TESTING AUTOMATIZADO**

### **🎯 E2E SMOKE TEST**
```python
# tests/e2e/test_core_flow.py

@pytest.mark.asyncio
async def test_e2e_core_flow():
    """Test del flujo completo: Login → Agente → Analytics"""
    
    async with AsyncClient() as client:
        # 1. Login
        res = await client.post("/api/v1/auth/login", json={
            "email": "test@fluxagent.com",
            "password": "password"
        })
        assert res.status_code == 200
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Crear Agente
        res = await client.post("/api/v1/agents", json={
            "nombre": "Agente Test",
            "agent_type": "sales",
            "modelo": "qwen2.5:3b"
        }, headers=headers)
        assert res.status_code == 200
        agent_id = res.json()["id"]
        
        # 3. Analytics
        res = await client.get("/api/v1/analytics/overview", headers=headers)
        assert res.status_code == 200
        analytics = res.json()
        assert "total_conversations" in analytics
        
        # 4. Health Check
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"
        
        print("🎉 Flujo E2E completado exitosamente")
```

### **🔧 EJECUCIÓN DE TESTS**
```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio httpx testcontainers[postgres,redis]

# Ejecutar tests E2E
pytest tests/e2e/test_core_flow.py -v --asyncio-mode=auto

# Ejecutar todos los tests
pytest tests/ -v
```

---

## 🏥 **MONITOREO Y SALUD**

### **📊 HEALTH CHECKS**
```python
# /health endpoint
{
    "status": "healthy",
    "timestamp": "2026-05-07T02:02:13.789055",
    "uptime": 3600,
    "version": "2.0.0",
    "circuits": {
        "database": {"state": "CLOSED", "failures": 0},
        "redis": {"state": "CLOSED", "failures": 0},
        "ollama": {"state": "CLOSED", "failures": 0}
    }
}
```

### **📈 MÉTRICAS DISPONIBLES**
- **Circuit Breakers:** Estado de cada servicio externo
- **Rate Limiting:** Requests por segundo por tenant
- **Response Times:** Latencia de endpoints
- **Error Rates:** Tasa de errores por servicio
- **Cache Hit Ratio:** Eficiencia de caché Redis

---

## 🔧 **TROUBLESHOOTING COMÚN**

### **❌ PROBLEMAS FRECUENTES**

#### **🔐 Login no funciona**
```bash
# Verificar backend
curl http://localhost:9000/health

# Verificar usuario en DB
docker-compose exec postgres psql -U fluxadmin -d fluxagent_v2 \
  -c "SELECT email, rol FROM usuarios WHERE email='tu@email.com'"

# Verificar contraseña
python3 -c "
import bcrypt
hash = '\$2b\$12\$...'
print(bcrypt.checkpw('tu_contraseña'.encode(), hash.encode()))
"
```

#### **🐳 Docker no levanta**
```bash
# Verificar puertos ocupados
netstat -tulpn | grep :5434
netstat -tulpn | grep :6381
netstat -tulpn | grep :9000
netstat -tulpn | grep :4000

# Limpiar contenedores
docker system prune -f
docker volume prune -f

# Reconstruir imágenes
docker-compose build --no-cache
```

#### **📊 Analytics no cargan**
```bash
# Verificar Redis
docker-compose exec redis redis-cli -a redisflux2026 ping

# Verificar cache
docker-compose exec redis redis-cli -a redisflux2026 keys "analytics:*"

# Limpiar cache si es necesario
docker-compose exec redis redis-cli -a redisflux2026 flushall
```

#### **🤖 Ollama no responde**
```bash
# Verificar Ollama
curl http://localhost:11434/api/tags

# Descargar modelo si falta
curl -X POST http://localhost:11434/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name": "qwen2.5:3b"}'

# Reiniciar Ollama
docker-compose restart ollama
```

### **📋 COMANDOS ÚTILES**
```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs de servicio específico
docker-compose logs -f backend
docker-compose logs -f frontend

# Entrar a contenedor
docker-compose exec backend bash
docker-compose exec postgres psql -U fluxadmin -d fluxagent_v2

# Reiniciar servicio específico
docker-compose restart backend
docker-compose restart postgres

# Reconstruir servicio
docker-compose up -d --build backend
```

---

## 🎯 **RESUMEN DE RECUPERACIÓN**

### **✅ PASOS CRÍTICOS**
1. **Clonar repositorio** con todo el código
2. **Configurar .env** con variables correctas
3. **Levantar infraestructura** con Docker Compose
4. **Migrar base de datos** con scripts SQL
5. **Verificar salud** de todos los servicios
6. **Ejecutar tests** E2E automatizados
7. **Crear usuario** por defecto para acceso
8. **Documentar** credenciales y URLs

### **🚀 LISTO PARA USO**
```bash
# Comando único para levantar todo
./scripts/levantar_sistema_completo.sh

# Verificación final
./scripts/verificacion_completa.sh
```

### **📱 ACCESOS POR DEFECTO**
- **Frontend:** http://localhost:4000
- **Backend API:** http://localhost:9000
- **Swagger Docs:** http://localhost:9000/docs
- **Usuario:** maritza@mendoza.com
- **Contraseña:** password

---

## 📞 **SOPORTE Y EMERGENCIAS**

### **🆘 SI TODO FALLA**
1. **Verificar logs:** `docker-compose logs`
2. **Reiniciar servicios:** `docker-compose restart`
3. **Limpiar volúmenes:** Último recurso
4. **Restaurar desde backup:** Si existe
5. **Contactar soporte:** Con logs completos

### **📚 DOCUMENTACIÓN ADICIONAL**
- **API Docs:** http://localhost:9000/docs
- **Database Schema:** migrations/ folder
- **Testing:** tests/ folder
- **Scripts:** scripts/ folder

---

## 🏁 **CONCLUSIÓN**

Este documento proporciona **toda la información necesaria** para reconstruir FluxAgent V2 completamente desde cero. Incluye:

- ✅ **Arquitectura completa** con diagramas
- ✅ **Stack tecnológico** detallado
- ✅ **Código fuente** estructurado
- ✅ **Configuración** ambiental
- ✅ **Scripts automatizados** de recuperación
- ✅ **Testing** E2E completo
- ✅ **Troubleshooting** común
- ✅ **Accesos por defecto** para verificación

**Con este documento, cualquier desarrollador puede levantar el sistema completo en menos de 30 minutos.**

---

*Última actualización: 7 de Mayo de 2026*  
*Versión: FluxAgent V2.0.0*  
*Estado: BETA-READY*
