export type ConversationStatus = 'new' | 'active' | 'waiting' | 'closed';
export type MessageRole = 'user' | 'agent' | 'system';
export type PipelineStage = 'new' | 'qualified' | 'negotiation' | 'closed';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
}

export interface Conversation {
  id: string;
  contactName: string;
  contactPhone: string;
  avatar?: string;
  lastMessage: string;
  lastMessageTime: string;
  status: ConversationStatus;
  unreadCount: number;
  leadScore: number; // 0-100
  pipelineStage: PipelineStage;
  tags: string[];
  messages: Message[];
}

export const MOCK_CONVERSATIONS: Conversation[] = [
  {
    id: '1', contactName: 'María López', contactPhone: '+593987654321',
    lastMessage: '¿Tienen stock de las zapatillas Nike?', lastMessageTime: '2026-05-05T10:30:00Z',
    status: 'active', unreadCount: 2, leadScore: 85, pipelineStage: 'negotiation',
    tags: ['cliente-nuevo', 'alto-interes'],
    messages: [
      { id: 'm1', role: 'user', content: 'Hola, busco zapatillas para correr', timestamp: '2026-05-05T10:25:00Z' },
      { id: 'm2', role: 'agent', content: '¡Hola María! Claro, tenemos el modelo AirZoom. ¿Qué talla usas?', timestamp: '2026-05-05T10:26:00Z' },
      { id: 'm3', role: 'user', content: '¿Tienen stock de las zapatillas Nike?', timestamp: '2026-05-05T10:30:00Z' }
    ]
  },
  {
    id: '2', contactName: 'Carlos Ruiz', contactPhone: '+593991234567',
    lastMessage: 'Gracias, lo revisaré', lastMessageTime: '2026-05-05T09:15:00Z',
    status: 'waiting', unreadCount: 0, leadScore: 40, pipelineStage: 'qualified',
    tags: ['seguimiento'],
    messages: [
      { id: 'm4', role: 'agent', content: 'Te envié el catálogo actualizado. Avísame si necesitas cotización.', timestamp: '2026-05-05T09:10:00Z' },
      { id: 'm5', role: 'user', content: 'Gracias, lo revisaré', timestamp: '2026-05-05T09:15:00Z' }
    ]
  },
  {
    id: '3', contactName: 'Ana Martínez', contactPhone: '+593988765432',
    lastMessage: 'Quiero agendar una cita para mañana', lastMessageTime: '2026-05-05T08:00:00Z',
    status: 'new', unreadCount: 1, leadScore: 92, pipelineStage: 'new',
    tags: ['reserva', 'urgente'],
    messages: [
      { id: 'm6', role: 'user', content: 'Quiero agendar una cita para mañana', timestamp: '2026-05-05T08:00:00Z' }
    ]
  }
];
