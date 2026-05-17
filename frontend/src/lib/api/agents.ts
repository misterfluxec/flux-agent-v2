// =============================================================================
// FLUXAGENT V2 — AGENTS API CLIENT (MEJORADO)
// =============================================================================
// Validación resiliente para onboarding funcional
// Coherencia con backend schema
// =============================================================================

import { api } from '../api';

// =============================================================================
// TYPES
// =============================================================================

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
  sales_script?: ScriptVentas;
  agent_type?: string;
  system_prompt?: string;
  specialty?: string;
}

export interface ScriptVentas {
  fases: any[];
  reglas: any[];
  scripts: any[];
  escalacion: {
    enabled: boolean;
    keywords: string[];
  };
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
  sales_script?: ScriptVentas;
  agent_type: string;
  system_prompt?: string;
  specialty?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

// =============================================================================
// API FUNCTIONS
// =============================================================================

/**
 * Helper para generar system prompt por defecto coherente con backend
 */
function generateDefaultPrompt(agent: Partial<AgentCreate>): string {
  const base = `Eres un asistente ${agent.agent_type || 'profesional'}`;
  const personality = agent.personality ? `. Tu personality: ${agent.personality}` : '';
  const instructions = agent.instructions ? `. Instrucciones: ${agent.instructions}` : '';
  const business = agent.business_type ? `. Contexto de negocio: ${agent.business_type}` : '';
  return `${base}${personality}${instructions}${business}.`;
}

/**
 * Crea nuevo agente con validación resiliente
 */
export async function createAgent(payload: AgentCreate): Promise<{ mensaje: string; agente_id: string }> {
  const response = await api.post<{ mensaje: string; agente_id: string }>('/agents', {
    ...payload,
    // Garantizar estructura mínima si el frontend no la envía
    sales_script: payload.sales_script ?? {
      fases: [],
      reglas: [],
      scripts: [],
      escalacion: { enabled: true, keywords: [] }
    },
    agent_type: payload.agent_type ?? 'sales',
    system_prompt: payload.system_prompt ?? generateDefaultPrompt(payload),
    specialty: payload.specialty ?? payload.business_type ?? 'general'
  });
  return response.data;
}

/**
 * Obtiene todos los agentes del tenant actual
 */
export async function fetchAgents(): Promise<AgentResponse[]> {
  const { data } = await api.get<AgentResponse[]>('/agents');
  return data;
}

/**
 * Obtiene un agente específico por ID
 */
export async function fetchAgent(id: string): Promise<AgentResponse> {
  const { data } = await api.get<AgentResponse>(`/agents/${id}`);
  return data;
}

/**
 * Actualiza un agente existente
 */
export async function updateAgent(id: string, req: AgentUpdate): Promise<{ mensaje: string }> {
  const { data } = await api.patch<{ mensaje: string }>(`/agents/${id}`, req);
  return data;
}

/**
 * Elimina un agente
 */
export async function deleteAgent(id: string): Promise<{ mensaje: string }> {
  const { data } = await api.delete<{ mensaje: string }>(`/agents/${id}`);
  return data;
}

/**
 * Sube avatar para el agente
 */
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

/**
 * Obtiene estadísticas de un agente específico
 */
export async function fetchAgentStats(id: string, days: number = 30): Promise<{
  conversations: number;
  messages: number;
  leads: number;
  sales: number;
  avg_response_time: number;
  satisfaction_score: number;
}> {
  const { data } = await api.get(`/agents/${id}/stats?days=${days}`);
  return data;
}

/**
 * Duplica un agente existente
 */
export async function duplicateAgent(id: string, newName: string): Promise<{ mensaje: string; agente_id: string }> {
  const { data } = await api.post<{ mensaje: string; agente_id: string }>(`/agents/${id}/duplicate`, {
    name: newName
  });
  return data;
}

/**
 * Activa/desactiva un agente
 */
export async function toggleAgentStatus(id: string, enabled: boolean): Promise<{ mensaje: string }> {
  const { data } = await api.patch<{ mensaje: string }>(`/agents/${id}/status`, {
    status: enabled ? 'is_active' : 'inactivo'
  });
  return data;
}

/**
 * Exporta configuración de agente
 */
export async function exportAgentConfig(id: string): Promise<{
  config: AgentResponse;
  export_date: string;
}> {
  const { data } = await api.get(`/agents/${id}/export`);
  return data;
}

/**
 * Importa configuración de agente
 */
export async function importAgentConfig(config: AgentCreate): Promise<{ mensaje: string; agente_id: string }> {
  const response = await api.post<{ mensaje: string; agente_id: string }>('/agents/import', config);
  return response.data;
}
