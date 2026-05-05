-- =============================================================================
-- FLUXAGENT V2 — ESQUEMA DE BASE DE DATOS MULTI-TENANT
-- =============================================================================
-- Versión : 2.0.0
-- Motor   : PostgreSQL 15 + pgvector
-- Autor   : FluxAgent Team
-- Fecha   : 2026-04-29
--
-- DESCRIPCIÓN:
--   Este esquema implementa una arquitectura multi-tenant segura con:
--   - Aislamiento de datos por RLS (Row Level Security)
--   - Soporte de vectores para búsqueda semántica (RAG)
--   - Gestión de agentes IA personalizables por tenant
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 0. EXTENSIONES REQUERIDAS
-- -----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";    -- Generación de UUIDs v4
CREATE EXTENSION IF NOT EXISTS "vector";       -- pgvector: embeddings semánticos
CREATE EXTENSION IF NOT EXISTS "pg_trgm";      -- Búsqueda fuzzy en textos

-- -----------------------------------------------------------------------------
-- 1. TABLA DE TENANTS (Clientes del SaaS)
-- -----------------------------------------------------------------------------
-- Cada tenant representa una empresa o individuo que contrata el servicio.
-- Es el punto de anclaje de todos los demás recursos del sistema.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenants (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Información de la empresa
    nombre_empresa          VARCHAR(255) NOT NULL,
    email_contacto          VARCHAR(255) UNIQUE NOT NULL,
    telefono                VARCHAR(50),
    pais                    VARCHAR(100) DEFAULT 'Ecuador',
    zona_horaria            VARCHAR(100) DEFAULT 'America/Guayaquil',

    -- Plan de suscripción
    plan                    VARCHAR(50) NOT NULL DEFAULT 'starter'
                                CHECK (plan IN ('starter', 'pro', 'business', 'enterprise')),
    estado                  VARCHAR(50) NOT NULL DEFAULT 'activo'
                                CHECK (estado IN ('activo', 'suspendido', 'cancelado')),

    -- Límites según el plan contratado
    max_agentes             INTEGER NOT NULL DEFAULT 1,
    max_mensajes_mes        INTEGER NOT NULL DEFAULT 500,
    mensajes_usados_mes     INTEGER NOT NULL DEFAULT 0,
    max_instancias_whatsapp INTEGER NOT NULL DEFAULT 1,

    -- Fechas del contrato
    contrato_inicio         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    contrato_fin            TIMESTAMPTZ,

    -- Branding para Portal Corporativo (Marca Blanca)
    color_primario          VARCHAR(20) DEFAULT '#6366f1',
    branding_config         JSONB,
    dominio_personalizado   VARCHAR(255),

    -- Auditoría
    creado_en               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE tenants IS 'Clientes del SaaS. Cada tenant es una empresa con su propia instancia de datos aislada.';
COMMENT ON COLUMN tenants.plan IS 'Plan de suscripción: starter (gratuito/básico), pro (profesional), enterprise (empresarial).';

-- -----------------------------------------------------------------------------
-- 2. TABLA DE USUARIOS
-- -----------------------------------------------------------------------------
-- Usuarios que pertenecen a un tenant. Un tenant puede tener múltiples usuarios
-- con diferentes roles (admin, agente, viewer).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Credenciales
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    nombre          VARCHAR(255),

    -- Control de acceso
    rol             VARCHAR(50) NOT NULL DEFAULT 'admin'
                        CHECK (rol IN ('super_admin', 'admin', 'agente', 'viewer')),
    estado          VARCHAR(50) NOT NULL DEFAULT 'activo'
                        CHECK (estado IN ('activo', 'inactivo', 'suspendido')),

    -- Preferencias
    idioma          VARCHAR(10) DEFAULT 'es',

    -- Auditoría
    ultimo_login    TIMESTAMPTZ,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE usuarios IS 'Usuarios autenticados que pertenecen a un tenant específico.';
COMMENT ON COLUMN usuarios.rol IS 'super_admin: acceso total al sistema. admin: gestión del tenant. agente: solo operación. viewer: solo lectura.';

-- -----------------------------------------------------------------------------
-- 3. TABLA DE AGENTS (Agentes IA personalizables)
-- -----------------------------------------------------------------------------
-- Cada agente IA tiene una personalidad, género y humor configurables.
-- Un tenant puede tener múltiples agentes para diferentes canales o propósitos.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Identidad del agente
    nombre          VARCHAR(255) NOT NULL,
    avatar_url      TEXT,
    
    -- Área / Departamento (para múltiples agentes por tenant)
    area            VARCHAR(100),                  -- Ej: "Ventas", "Soporte", "RRHH"
    descripcion     TEXT,                          -- Descripción breve del agente

    -- Personalidad
    genero          VARCHAR(20) NOT NULL DEFAULT 'femenino'
                        CHECK (genero IN ('masculino', 'femenino', 'neutro')),
    humor           VARCHAR(50) NOT NULL DEFAULT 'profesional'
                        CHECK (humor IN ('formal', 'profesional', 'amigable', 'casual', 'humoristico')),
    personalidad    TEXT,                          -- Descripción libre de la personalidad
    idioma          VARCHAR(50) NOT NULL DEFAULT 'Español (Ecuador)',
    tono            VARCHAR(50) NOT NULL DEFAULT 'profesional',

    -- Conocimiento y dominio (RAG)
    coleccion_rag   VARCHAR(255),                  -- Colección de conocimiento asociada
    tipo_negocio    TEXT,                          -- Ej: "Empresa de seguros de vida"
    objetivo        TEXT,                          -- Ej: "Cerrar ventas y calificar leads"
    instrucciones   TEXT,                          -- Prompt base del agente

    -- Configuración del modelo LLM
    modelo          VARCHAR(100) NOT NULL DEFAULT 'qwen2.5:3b',
    temperatura     FLOAT NOT NULL DEFAULT 0.7 CHECK (temperatura BETWEEN 0.0 AND 2.0),
    max_tokens      INTEGER NOT NULL DEFAULT 512,

    -- Canales habilitados para este agente
    canales         TEXT[] NOT NULL DEFAULT ARRAY['web_chat'],
    
    -- Horario de atención
    horario_inicio  TIME DEFAULT '08:00',
    horario_fin     TIME DEFAULT '20:00',
    dias_atencion   TEXT[] DEFAULT ARRAY['lunes','martes','miercoles','jueves','viernes'],
    mensaje_fuera_horario TEXT,

    -- Estado operativo
    estado          VARCHAR(50) NOT NULL DEFAULT 'entrenando'
                        CHECK (estado IN ('entrenando', 'activo', 'pausado', 'archivado')),

    -- Auditoría
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE agents IS 'Agentes IA configurados por cada tenant. Personalidad, humor y objetivo son personalizables.';
COMMENT ON COLUMN agents.humor IS 'Tono emocional del agente: desde formal hasta humorístico.';
COMMENT ON COLUMN agents.canales IS 'Lista de canales donde opera: web_chat, whatsapp, telegram, email.';

-- -----------------------------------------------------------------------------
-- 4. TABLA DE KNOWLEDGE_CHUNKS (Base de conocimiento con embeddings)
-- -----------------------------------------------------------------------------
-- Almacena fragmentos de texto extraídos de documentos (PDF, Excel, URLs)
-- junto con su vector de embedding para búsqueda semántica (RAG).
-- El tipo VECTOR(768) corresponde al modelo nomic-embed-text (Ollama).
-- Verificado: docker exec fluxv2-backend → nomic-embed-text → 768 dims.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id        UUID REFERENCES agents(id) ON DELETE SET NULL,

    -- Contenido del fragmento
    contenido       TEXT NOT NULL,                 -- Texto del fragmento (chunk)
    fuente_nombre   VARCHAR(255),                  -- Ej: "catalogo_productos.pdf"
    fuente_tipo     VARCHAR(50) DEFAULT 'pdf'
                        CHECK (fuente_tipo IN ('pdf', 'excel', 'csv', 'url', 'texto', 'whatsapp')),
    fuente_url      TEXT,                          -- URL original si aplica

    -- Vector de embedding para búsqueda semántica
    -- Dimensión 768: nomic-embed-text via Ollama (producción verificada)
    embedding       VECTOR(768),

    -- Metadatos del chunk
    pagina_numero   INTEGER,                       -- Número de página del PDF
    orden_chunk     INTEGER,                       -- Posición del chunk en el documento
    tokens_count    INTEGER,                       -- Cantidad de tokens del fragmento

    -- Auditoría
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE knowledge_chunks IS 'Base de conocimiento vectorial (RAG). Cada fila es un fragmento de documento con su embedding para búsqueda semántica.';
COMMENT ON COLUMN knowledge_chunks.embedding IS 'Vector de dimensión 768. Modelo: nomic-embed-text via Ollama :11434. Verificado en producción.';

-- Índice vectorial IVFFlat para búsqueda ANN (Approximate Nearest Neighbor)
-- lists=100 es recomendado para tablas hasta 1M de filas
CREATE INDEX IF NOT EXISTS idx_knowledge_embedding
    ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_knowledge_tenant_agent
    ON knowledge_chunks (tenant_id, agent_id);

-- -----------------------------------------------------------------------------
-- 5. TABLA DE CONVERSACIONES
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversaciones (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id            UUID REFERENCES agents(id) ON DELETE SET NULL,

    -- Identificación del lead externo (número de WhatsApp, email, etc.)
    lead_externo_id     VARCHAR(255),
    canal               VARCHAR(50) DEFAULT 'web_chat',

    -- Métricas de la conversación
    estado              VARCHAR(50) DEFAULT 'activa'
                            CHECK (estado IN ('activa', 'cerrada', 'transferida')),
    sentimiento         FLOAT,                     -- Score entre -1.0 y 1.0
    lead_calificado     BOOLEAN DEFAULT FALSE,
    venta_cerrada       BOOLEAN DEFAULT FALSE,
    valor_venta         DECIMAL(10,2) DEFAULT 0.00,

    -- Uso de tokens (para control de costos)
    tokens_entrada      INTEGER DEFAULT 0,
    tokens_salida       INTEGER DEFAULT 0,

    -- Fechas
    iniciada_en         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cerrada_en          TIMESTAMPTZ
);

COMMENT ON TABLE conversaciones IS 'Historial de conversaciones. Incluye métricas de conversión y uso de tokens por tenant.';

-- -----------------------------------------------------------------------------
-- 6. TABLA DE MENSAJES
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mensajes (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversacion_id     UUID NOT NULL REFERENCES conversaciones(id) ON DELETE CASCADE,
    tenant_id           UUID NOT NULL,              -- Desnormalizado para RLS eficiente

    rol                 VARCHAR(20) NOT NULL
                            CHECK (rol IN ('usuario', 'asistente', 'sistema')),
    contenido           TEXT NOT NULL,
    tokens              INTEGER DEFAULT 0,

    creado_en           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE mensajes IS 'Mensajes individuales de cada conversación. tenant_id desnormalizado para aplicar RLS sin JOINs.';

-- =============================================================================
-- SECCIÓN: ROW LEVEL SECURITY (RLS)
-- =============================================================================
-- Política de aislamiento total entre tenants.
-- Ningún tenant puede leer o modificar datos de otro tenant.
-- Las políticas se aplican a nivel de motor de base de datos.
-- =============================================================================

-- Habilitar RLS en todas las tablas que contienen datos de tenants
ALTER TABLE usuarios           ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents             ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_chunks   ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversaciones     ENABLE ROW LEVEL SECURITY;
ALTER TABLE mensajes           ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- VARIABLE DE SESIÓN: app.current_tenant_id
-- -----------------------------------------------------------------------------
-- El backend debe ejecutar SET app.current_tenant_id = '<uuid>' al inicio
-- de cada request autenticado. Las políticas RLS leen esta variable.
-- -----------------------------------------------------------------------------

-- Política RLS: usuarios
CREATE POLICY tenant_isolation_usuarios ON usuarios
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

-- Política RLS: agents
CREATE POLICY tenant_isolation_agents ON agents
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

-- Política RLS: knowledge_chunks
CREATE POLICY tenant_isolation_knowledge ON knowledge_chunks
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

-- Política RLS: conversaciones
CREATE POLICY tenant_isolation_conversaciones ON conversaciones
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

-- Política RLS: mensajes
CREATE POLICY tenant_isolation_mensajes ON mensajes
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

-- =============================================================================
-- SECCIÓN: ROL DE APLICACIÓN
-- =============================================================================
-- Creamos un rol restringido para la aplicación. Este rol tiene acceso
-- a los datos pero NO puede bypassear RLS (eso solo puede hacerlo el superuser).
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'fluxagent_app') THEN
        CREATE ROLE fluxagent_app LOGIN PASSWORD 'fluxpass_secure_2026';
    END IF;
END
$$;

-- Otorgar permisos mínimos necesarios al rol de aplicación
GRANT CONNECT ON DATABASE fluxagent_v2 TO fluxagent_app;
GRANT USAGE ON SCHEMA public TO fluxagent_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fluxagent_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fluxagent_app;

-- =============================================================================
-- SECCIÓN: FUNCIONES DE UTILIDAD
-- =============================================================================

-- Función para actualizar automáticamente el campo actualizado_en
CREATE OR REPLACE FUNCTION fn_actualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado_en = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para tenants
CREATE TRIGGER trg_tenants_actualizado
    BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION fn_actualizar_timestamp();

-- Trigger para agents
CREATE TRIGGER trg_agents_actualizado
    BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION fn_actualizar_timestamp();

-- =============================================================================
-- SECCIÓN: ÍNDICES DE RENDIMIENTO
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_usuarios_tenant    ON usuarios (tenant_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_email     ON usuarios (email);
CREATE INDEX IF NOT EXISTS idx_agents_tenant      ON agents (tenant_id, estado);
CREATE INDEX IF NOT EXISTS idx_conv_tenant        ON conversaciones (tenant_id, iniciada_en DESC);
CREATE INDEX IF NOT EXISTS idx_mensajes_conv      ON mensajes (conversacion_id, creado_en ASC);

-- =============================================================================
-- SECCIÓN: DATOS INICIALES (Seed)
-- =============================================================================

-- Tenant de demostración para pruebas internas
INSERT INTO tenants (id, nombre_empresa, email_contacto, plan)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'FluxAgent Demo',
    'demo@fluxagent.com',
    'enterprise'
) ON CONFLICT DO NOTHING;

-- Usuario super_admin para el tenant de demo
INSERT INTO usuarios (tenant_id, email, password_hash, nombre, rol)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'admin@fluxagent.com',
    -- Hash de 'Admin2026!' — CAMBIAR EN PRODUCCIÓN
    '$2b$12$placeholder_replace_with_real_bcrypt_hash',
    'Administrador FluxAgent',
    'super_admin'
) ON CONFLICT DO NOTHING;

-- =============================================================================
-- SECCIÓN: TABLA DE CANALES (WHATSAPP, ETC)
-- =============================================================================
CREATE TABLE IF NOT EXISTS canales_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,

    canal VARCHAR(50) NOT NULL CHECK (canal IN ('whatsapp', 'telegram', 'instagram', 'web_chat')),
    instancia_nombre VARCHAR(255) NOT NULL,
    
    token_acceso TEXT,
    webhook_url TEXT,

    estado VARCHAR(50) DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo', 'desconectado')),
    
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(tenant_id, canal, instancia_nombre)
);

ALTER TABLE canales_config ENABLE ROW LEVEL SECURITY;
CREATE INDEX IF NOT EXISTS idx_canales_tenant ON canales_config(tenant_id);

CREATE POLICY tenant_isolation_canales ON canales_config
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

CREATE TRIGGER trg_canales_actualizado
    BEFORE UPDATE ON canales_config
    FOR EACH ROW EXECUTE FUNCTION fn_actualizar_timestamp();

-- =============================================================================
-- FIN DEL ESQUEMA
-- =============================================================================

-- =============================================================================
-- TICKETS (SOPORTE PARA EL PANEL SUPER ADMIN)
-- =============================================================================
CREATE TABLE IF NOT EXISTS tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    asunto VARCHAR(255) NOT NULL,
    descripcion TEXT,
    estado VARCHAR(50) DEFAULT 'abierto' CHECK (estado IN ('abierto', 'en_proceso', 'resuelto')),
    prioridad VARCHAR(50) DEFAULT 'media' CHECK (prioridad IN ('baja', 'media', 'alta')),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 7. TABLAS DE FACTURACIÓN Y PLANES
-- =============================================================================

CREATE TABLE IF NOT EXISTS plans (
  id VARCHAR(20) PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  precio DECIMAL(10,2) NOT NULL DEFAULT 0,
  moneda VARCHAR(10) DEFAULT 'USD',
  features JSONB NOT NULL,
  usage_limits JSONB NOT NULL,
  max_agentes INT NOT NULL DEFAULT 1,
  max_instancias_whatsapp INT NOT NULL DEFAULT 0,
  orden INT DEFAULT 0,
  activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS usage_daily (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  fecha DATE NOT NULL DEFAULT CURRENT_DATE,
  mensajes_count INT DEFAULT 0,
  audio_seconds INT DEFAULT 0,
  images_count INT DEFAULT 0,
  tokens_in INT DEFAULT 0,
  tokens_out INT DEFAULT 0,
  UNIQUE(tenant_id, fecha)
);

-- Política RLS: usage_daily
ALTER TABLE usage_daily ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_usage ON usage_daily
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

