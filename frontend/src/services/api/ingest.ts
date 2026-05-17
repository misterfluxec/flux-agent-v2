import { apiClient } from "@/lib/api-client";

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

/**
 * Obtiene el resumen de conocimiento del tenant autenticado.
 */
export async function fetchKnowledge(): Promise<KnowledgeResponse> {
  const { data } = await apiClient.get<KnowledgeResponse>("/knowledge");
  return data;
}

/**
 * Elimina una fuente de conocimiento específica.
 */
export async function deleteKnowledgeSource(fuenteNombre: string): Promise<{ eliminados: number; fuente: string }> {
  const { data } = await apiClient.delete<{ eliminados: number; fuente: string }>(`/knowledge/${encodeURIComponent(fuenteNombre)}`);
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

  const { data } = await apiClient.post<IngestResponse>("/ingest/start", form);
  return data;
}

/**
 * Ingesta de URLs web
 */
export async function ingestUrl(url: string, agentId?: string): Promise<IngestResponse> {
  const form = new FormData();
  form.append("url", url);
  if (agentId) form.append("agent_id", agentId);

  const { data } = await apiClient.post<IngestResponse>("/ingest/start", form);
  return data;
}

/**
 * Consulta el status de un job de ingesta
 */
export async function fetchIngestionStatus(jobId: string): Promise<IngestStatusResponse> {
  const { data } = await apiClient.get<IngestStatusResponse>(`/ingest/status/${jobId}`);
  return data;
}

/**
 * Obtiene los fragmentos extraídos de una fuente
 */
export async function fetchSourceChunks(fuenteNombre: string): Promise<SourceChunksResponse> {
  const { data } = await apiClient.get<SourceChunksResponse>(`/knowledge/${encodeURIComponent(fuenteNombre)}/chunks`);
  return data;
}

export async function clearBrain(): Promise<{ mensaje: string; chunks_eliminados: number; productos_eliminados: number }> {
  const { data } = await apiClient.delete<{ mensaje: string; chunks_eliminados: number; productos_eliminados: number }>("/knowledge");
  return data;
}
