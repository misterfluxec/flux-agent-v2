import { apiClient } from "@/lib/api-client";

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
  const { data } = await apiClient.get<AgentResponse[]>("/agents");
  return data;
}

export async function createAgent(req: AgentCreate): Promise<{ mensaje: string; agente_id: string }> {
  const { data } = await apiClient.post<{ mensaje: string; agente_id: string }>("/agents", req);
  return data;
}

export async function updateAgent(id: string, req: AgentUpdate): Promise<{ mensaje: string }> {
  const { data } = await apiClient.patch<{ mensaje: string }>(`/agents/${id}`, req);
  return data;
}

export async function uploadAgentAvatar(id: string, file: File): Promise<{ mensaje: string; avatar_url: string }> {
  const formData = new FormData();
  formData.append("file", file);
  
  const { data } = await apiClient.post<{ mensaje: string; avatar_url: string }>(`/agents/${id}/avatar`, formData);
  return data;
}

export async function deleteAgent(id: string): Promise<{ mensaje: string }> {
  const { data } = await apiClient.delete<{ mensaje: string }>(`/agents/${id}`);
  return data;
}

export async function testAgent(id: string, mensaje: string): Promise<{ agente: string; respuesta: string; model: string }> {
  const { data } = await apiClient.post<{ agente: string; respuesta: string; model: string }>(`/agents/${id}/test`, { mensaje });
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
  const { data } = await apiClient.post<GenerateIdentityResponse>("/agents/generate-identity", req);
  return data;
}
