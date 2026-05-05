import axios from "axios";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:9000";

// Base client apuntando a /api/v1 según especificación
export const api = axios.create({
  baseURL: `${BACKEND_URL}/api/v1`,
  timeout: 60_000, // Aumentado a 60s para ingesta
  headers: { "Content-Type": "application/json" },
});

// Interceptor para inyectar el JWT en cada petición
api.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("flux_token") : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para manejar errores globales (ej: token expirado 401)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("flux_token");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// Cliente sin prefijo para endpoints en la raíz (ej: /health)
export const apiRoot = axios.create({
  baseURL: BACKEND_URL,
  timeout: 10_000,
});

// ─── Types ────────────────────────────────────────────────────────────────────

export interface HealthResponse {
  estado: "saludable" | "degradado";
  servicios: Record<string, { estado: string; latencia_ms?: number }>;
  version: string;
}

export interface ChatRequest {
  tenant_id?: string; // Opcional, el backend lo saca del token
  agent_id?: string;
  session_id: string;
  mensaje: string;
  historial: { rol: string; contenido: string }[];
  configuracion: { nombre: string; humor: string; tipo_negocio?: string };
}

export interface ChatResponse {
  session_id: string;
  respuesta: string;
  tokens: number;
  modelo: string;
  fuentes_rag: string[];
  chunks_usados: number;
}

export interface IngestResponse {
  job_id: string;
  estado: string;
  fuente: string;
  mensaje: string;
}

export interface IngestStatusResponse {
  estado: string;
  progreso: number;
  mensaje: string;
  chunks?: number;
}

export interface ChunkItem {
  id: string;
  contenido: string;
  orden: number;
  tipo: string;
}

export interface SourceChunksResponse {
  fuente: string;
  total_chunks: number;
  chunks: ChunkItem[];
}

export interface KnowledgeSource {
  fuente_nombre: string;
  fuente_tipo: string;
  chunks: number;
  ultima_ingesta: string;
}

export interface KnowledgeResponse {
  total_chunks: number;
  fuentes: KnowledgeSource[];
  tenant_id: string;
}

export interface StatsOverviewResponse {
  kpis: {
    total_conversaciones: number;
    leads_capturados: number;
    sentimiento_promedio: number;
    uso_tokens: number;
  };
  mensajes_por_dia: { fecha: string; conteo: number }[];
  sentimiento_distribucion: { name: string; value: number; fill: string }[];
  actividad_reciente: { id: string; action: string; agent: string; time: string; status: string }[];
}

// ─── API functions ────────────────────────────────────────────────────────────

export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await apiRoot.get<HealthResponse>("/health");
  return data;
}

export async function fetchStatsOverview(): Promise<StatsOverviewResponse> {
  const { data } = await api.get<StatsOverviewResponse>("/stats/overview");
  return data;
}

export async function sendChat(req: ChatRequest): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>("/chat", req);
  return data;
}

/**
 * Obtiene el resumen de conocimiento del tenant autenticado.
 */
export async function fetchKnowledge(): Promise<KnowledgeResponse> {
  const { data } = await api.get<KnowledgeResponse>("/knowledge");
  return data;
}

/**
 * Elimina una fuente de conocimiento específica.
 */
export async function deleteKnowledgeSource(fuenteNombre: string): Promise<{ eliminados: number; fuente: string }> {
  const { data } = await api.delete(`/knowledge/${encodeURIComponent(fuenteNombre)}`);
  return data;
}

/**
 * Ingesta de archivos (PDF, CSV, XLSX, TXT)
 */
export async function uploadDocument(
  file: File,
  agentId?: string
): Promise<IngestResponse> {
  const form = new FormData();
  form.append("archivo", file);
  if (agentId) form.append("agent_id", agentId);

  const { data } = await api.post<IngestResponse>("/ingest/start", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

/**
 * Ingesta de URLs web
 */
export async function ingestUrl(url: string, agentId?: string): Promise<IngestResponse> {
  const form = new FormData();
  form.append("url", url);
  if (agentId) form.append("agent_id", agentId);

  const { data } = await api.post<IngestResponse>("/ingest/start", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

/**
 * Consulta el estado de un job de ingesta
 */
export async function fetchIngestionStatus(jobId: string): Promise<IngestStatusResponse> {
  const { data } = await api.get<IngestStatusResponse>(`/ingest/status/${jobId}`);
  return data;
}

/**
 * Obtiene los fragmentos extraídos de una fuente
 */
export async function fetchSourceChunks(fuenteNombre: string): Promise<SourceChunksResponse> {
  const { data } = await api.get<SourceChunksResponse>(`/knowledge/${encodeURIComponent(fuenteNombre)}/chunks`);
  return data;
}

/**
 * Inventario de productos estructurado
 */
export interface ProductData {
  id: string;
  codigo: string | null;
  nombre: string;
  precio: number;
  stock: number;
  estado: string;
  descripcion: string | null;
}

export async function fetchProducts(): Promise<ProductData[]> {
  const { data } = await api.get<ProductData[]>("/products");
  return data;
}

export async function updateProduct(id: string, updates: { precio?: number; stock?: number }): Promise<{ mensaje: string }> {
  const { data } = await api.patch<{ mensaje: string }>(`/products/${id}`, updates);
  return data;
}

export async function clearBrain(): Promise<{ mensaje: string; chunks_eliminados: number; productos_eliminados: number }> {
  const { data } = await api.delete("/knowledge");
  return data;
}

export interface LeadData {
  id: string;
  name: string;
  phone: string;
  email: string;
  canal: string;
  estado: string;
  monto: number;
  fecha: string;
  sentimiento: number;
}

export async function fetchLeads(): Promise<LeadData[]> {
  const { data } = await api.get<LeadData[]>("/leads");
  return data;
}

// ─── Agents API ──────────────────────────────────────────────────────────────

export interface AgentCreate {
  nombre: string;
  area?: string | null;
  descripcion?: string | null;
  genero?: string;
  humor?: string;
  personalidad?: string | null;
  idioma?: string;
  tono?: string;
  coleccion_rag?: string | null;
  tipo_negocio?: string | null;
  objetivo?: string | null;
  instrucciones?: string | null;
  modelo?: string;
  temperatura?: number;
  max_tokens?: number;
  canales?: string[];
  horario_inicio?: string | null;
  horario_fin?: string | null;
  dias_atencion?: string[] | null;
  mensaje_fuera_horario?: string | null;
  script_ventas?: any | null;
}

export interface AgentUpdate extends Partial<AgentCreate> {
  estado?: string;
}

export interface AgentResponse {
  id: string;
  nombre: string;
  area?: string | null;
  descripcion?: string | null;
  genero: string;
  humor: string;
  personalidad?: string | null;
  idioma: string;
  tono: string;
  coleccion_rag?: string | null;
  tipo_negocio?: string | null;
  objetivo?: string | null;
  instrucciones?: string | null;
  modelo: string;
  temperatura: number;
  max_tokens: number;
  canales: string[];
  horario_inicio?: string | null;
  horario_fin?: string | null;
  dias_atencion?: string[] | null;
  mensaje_fuera_horario?: string | null;
  script_ventas?: any | null;
  estado: string;
  creado_en: string;
  actualizado_en: string;
}

export async function fetchAgents(): Promise<AgentResponse[]> {
  const { data } = await api.get<AgentResponse[]>("/agents");
  return data;
}

export async function createAgent(req: AgentCreate): Promise<{ mensaje: string; agente_id: string }> {
  const { data } = await api.post<{ mensaje: string; agente_id: string }>("/agents", req);
  return data;
}

export async function updateAgent(id: string, req: AgentUpdate): Promise<{ mensaje: string }> {
  const { data } = await api.patch<{ mensaje: string }>(`/agents/${id}`, req);
  return data;
}

export async function uploadAgentAvatar(id: string, file: File): Promise<{ mensaje: string; avatar_url: string }> {
  const formData = new FormData();
  formData.append("file", file);
  
  const { data } = await api.post<{ mensaje: string; avatar_url: string }>(`/agents/${id}/avatar`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return data;
}

