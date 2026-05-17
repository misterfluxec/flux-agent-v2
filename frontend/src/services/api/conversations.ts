/**
 * conversations.ts — API Service para Conversaciones Real
 * Conecta el frontend con el backend real de FluxAgent V2
 */

import { apiClient } from "@/lib/api-client";

// ─── Types ─────────────────────────────────────────────────────────────────

export type ConversationStatus =
  | "nuevo"
  | "contactado"
  | "interesado"
  | "cerrado"
  | "perdido"
  | "waiting" // Para compatibilidad con UI
  | "active";

export type ConversationChannel = "whatsapp" | "telegram" | "web" | "voice";

export interface Conversation {
  id: string;
  contactPhone: string;
  contactName: string;
  email?: string;
  channel: ConversationChannel;
  status: ConversationStatus;
  lastMessage: string;
  lastMessageTime: string;
  leadScore: number;
  monto: number;
  messages: Message[];
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "agent" | "system";
  content: string;
  timestamp: string;
}

export interface ConversationFilters {
  status?: string;
  search?: string;
}

// ─── API Functions ──────────────────────────────────────────────────────────

/** Lista todas las conversaciones (leads) desde el backend */
export async function getConversations(
  filters?: ConversationFilters
): Promise<Conversation[]> {
  const params = new URLSearchParams();
  if (filters?.search) params.set("search", filters.search);
  
  // El backend usa /api/v1/leads para el listado del inbox
  const response = await apiClient.get<any[]>("/leads", { 
    // Adaptar filtros si el backend los soporta en el futuro
  });
  
  // Mapear respuesta del backend a nuestro formato de frontend
  return response.data.map(item => ({
    id: item.id,
    contactPhone: item.phone,
    contactName: item.name,
    email: item.email,
    channel: item.canal as ConversationChannel,
    status: item.status as ConversationStatus,
    lastMessage: "Último mensaje del lead...", // El backend actual no devuelve el último mensaje en el listado
    lastMessageTime: item.fecha || new Date().toISOString(),
    leadScore: Math.round(item.sentimiento * 100),
    monto: item.monto,
    messages: [] // Se cargan al seleccionar la conversación
  }));
}

/** Obtiene una conversación específica con su historial real desde el backend */
export async function getConversation(id: string): Promise<Conversation> {
  // 1. Obtener datos básicos del lead/conversación
  const all = await getConversations();
  const found = all.find(c => c.id === id);
  if (!found) throw new Error("Conversación no encontrada");
  
  // 2. Obtener historial de mensajes real del backend
  try {
    const historyRes = await apiClient.get<any[]>(`/chat/history/${id}`);
    found.messages = historyRes.data.map((msg, index) => ({
      id: `msg-${index}-${Date.now()}`,
      role: msg.role === 'assistant' ? 'assistant' : 'user',
      content: msg.content,
      timestamp: msg.timestamp
    }));
    
    // Actualizar el último mensaje con el más reciente del historial si existe
    if (found.messages.length > 0) {
      const last = found.messages[found.messages.length - 1];
      found.lastMessage = last.content;
      found.lastMessageTime = last.timestamp;
    }
  } catch (error) {
    console.error("No se pudo cargar el historial real:", error);
    // Fallback a mensajes vacíos si hay error
    found.messages = [];
  }
  
  return found;
}

/** Envía un mensaje real al backend de Chat */
export async function sendChatMessage(
  conversationId: string,
  message: string,
  sessionId: string
): Promise<any> {
  return apiClient.post("/chat", {
    session_id: sessionId,
    mensaje: message,
    // El backend maneja el resto vía ContextoAgente
  });
}
