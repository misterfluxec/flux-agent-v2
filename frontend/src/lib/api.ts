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
  status: "saludable" | "degradado";
  servicios: Record<string, { status: string; latencia_ms?: number }>;
  version: string;
}

export interface ChatRequest {
  tenant_id?: string; // Opcional, el backend lo saca del token
  agent_id?: string;
  session_id: string;
  mensaje: string;
  historial: { role: string; contenido: string }[];
  configuracion: { name: string; mood: string; business_type?: string };
}

export interface ChatResponse {
  session_id: string;
  respuesta: string;
  tokens: number;
  model: string;
  fuentes_rag: string[];
  chunks_usados: number;
}

export interface IngestResponse {
  job_id: string;
  status: string;
  fuente: string;
  mensaje: string;
}

export interface IngestStatusResponse {
  status: string;
  progreso: number;
  mensaje: string;
  chunks?: number;
}

export interface ChunkItem {
  id: string;
  contenido: string;
  sort_order: number;
  type: string;
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
 * Consulta el status de un job de ingesta
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
  name: string;
  price: number;
  stock: number;
  status: string;
  description: string | null;
}

export async function fetchProducts(): Promise<ProductData[]> {
  const { data } = await api.get<ProductData[]>("/products");
  return data;
}

export async function updateProduct(id: string, updates: { price?: number; stock?: number }): Promise<{ mensaje: string }> {
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
  status: string;
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
  name: string;
  area?: string | null;
  description?: string | null;
  gender?: string;
  mood?: string;
  personality?: string | null;
  language?: string;
  tone?: string;
  rag_collection?: string | null;
  business_type?: string | null;
  objective?: string | null;
  instructions?: string | null;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  channels?: string[];
  schedule_start?: string | null;
  schedule_end?: string | null;
  service_days?: string[] | null;
  off_hours_message?: string | null;
  sales_script?: any | null;
  agent_type?: string;
  specialty?: string | null;
  system_prompt?: string | null;
}

export interface AgentUpdate extends Partial<AgentCreate> {
  status?: string;
}

export interface AgentResponse {
  id: string;
  name: string;
  area?: string | null;
  description?: string | null;
  gender: string;
  mood: string;
  personality?: string | null;
  language: string;
  tone: string;
  rag_collection?: string | null;
  business_type?: string | null;
  objective?: string | null;
  instructions?: string | null;
  model: string;
  temperature: number;
  max_tokens: number;
  channels: string[];
  schedule_start?: string | null;
  schedule_end?: string | null;
  service_days?: string[] | null;
  off_hours_message?: string | null;
  sales_script?: any | null;
  agent_type: string;
  specialty?: string | null;
  system_prompt?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  knowledge_base_size: number;
  last_sync_at?: string | null;
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

export async function deleteAgent(id: string): Promise<{ mensaje: string }> {
  const { data } = await api.delete<{ mensaje: string }>(`/agents/${id}`);
  return data;
}

export async function testAgent(id: string, mensaje: string): Promise<{ agente: string; respuesta: string; model: string }> {
  const { data } = await api.post<{ agente: string; respuesta: string; model: string }>(`/agents/${id}/test`, { mensaje });
  return data;
}

export interface GenerateIdentityRequest {
  descripcion_negocio: string;
  agent_type: string;
  tone: string;
}

export interface GenerateIdentityResponse {
  instructions: string;
}

export async function generateAgentIdentity(req: GenerateIdentityRequest): Promise<GenerateIdentityResponse> {
  const { data } = await api.post<GenerateIdentityResponse>("/agents/generate-identity", req);
  return data;
}

export class ApiClient {
  static async get(endpoint: string) {
    const url = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9000/api/v1";
    const res = await fetch(`${url}${endpoint}`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
    return res.json();
  }
  static async post(endpoint: string, data: any) {
    const url = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9000/api/v1";
    const res = await fetch(`${url}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
    return res.json();
  }
}

