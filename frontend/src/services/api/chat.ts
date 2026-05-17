import { apiClient } from "@/lib/api-client";

export interface ChatRequest {
  tenant_id?: string; // Opcional, el backend lo saca del token
  agent_id?: string;
  sesion_id?: string;
  session_id?: string;
  mensaje: string;
  historial?: { role: string; contenido: string }[];
  configuracion?: { name: string; mood: string; business_type?: string };
}

export interface ChatResponse {
  respuesta: string;
  sesion_id?: string;
  session_id?: string;
  tokens?: number;
  model?: string;
  fuentes_rag?: string[];
  chunks_usados?: number;
}

export async function sendChat(req: ChatRequest): Promise<ChatResponse> {
  const { data } = await apiClient.post<ChatResponse>("/chat", req);
  return data;
}

export async function clearChatSession(sessionId: string): Promise<{ mensaje: string }> {
  const { data } = await apiClient.delete<{ mensaje: string }>(`/chat/session/${sessionId}`);
  return data;
}
