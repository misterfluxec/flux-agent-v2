import { useState, useEffect, useCallback } from 'react';
import { Conversation, Message, MOCK_CONVERSATIONS, PipelineStage } from '@/types/conversation';
import { useEventBus } from '@/providers/EventBusProvider';

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>(MOCK_CONVERSATIONS);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isSending, setIsSending] = useState(false);

  const { subscribe } = useEventBus();

  // Escuchar eventos reales del EventBus
  useEffect(() => {
    const unsubscribe = subscribe(["CONVERSATION_HANDOFF", "VOICE_LIVE_TRANSCRIPT", "LEAD_HOT"], (msg) => {
      setConversations(prev => {
        // En un caso real, buscaríamos por tenant o conversation_id real. 
        // Como usamos mocks, forzaremos actualización en el primer mock o crearemos uno nuevo.
        const idToUpdate = msg.event_id || '1'; 
        
        // Si es un handoff, marcar status como waiting
        if (msg.type === "CONVERSATION_HANDOFF") {
          return prev.map(c => c.id === '1' ? { ...c, status: 'waiting', lastMessage: 'Handoff: ' + msg.data?.reason, lastMessageTime: new Date().toISOString() } : c);
        }
        
        // Si es un transcript de voz, agregarlo a la historia (simulado)
        if (msg.type === "VOICE_LIVE_TRANSCRIPT") {
          return prev.map(c => c.id === '2' ? { 
            ...c, 
            lastMessage: `🎙️ ${msg.data?.text}`, 
            lastMessageTime: new Date().toISOString() 
          } : c);
        }

        return prev;
      });
    });

    return () => unsubscribe();
  }, [subscribe]);

  const filtered = conversations.filter(c => {
    const matchSearch = c.contactName.toLowerCase().includes(search.toLowerCase()) || c.contactPhone.includes(search);
    const matchStatus = statusFilter === 'all' || c.status === statusFilter;
    return matchSearch && matchStatus;
  }).sort((a, b) => new Date(b.lastMessageTime).getTime() - new Date(a.lastMessageTime).getTime());

  const selected = conversations.find(c => c.id === selectedId) || null;

  const sendMessage = useCallback(async (text: string) => {
    if (!selectedId || !text.trim()) return;
    setIsSending(true);
    // Simula delay de red/LLM
    await new Promise(r => setTimeout(r, 800));
    
    const newMsg: Message = { id: Date.now().toString(), role: 'agent', content: text, timestamp: new Date().toISOString() };
    setConversations(prev => prev.map(c => c.id === selectedId ? { ...c, messages: [...c.messages, newMsg], lastMessage: text, lastMessageTime: new Date().toISOString() } : c));
    setIsSending(false);
  }, [selectedId]);

  const updatePipeline = useCallback((convId: string, stage: PipelineStage) => {
    setConversations(prev => prev.map(c => c.id === convId ? { ...c, pipelineStage: stage } : c));
  }, []);

  return { 
    conversations: filtered, 
    allConversations: conversations, // Para el tablero que no filtra por status
    selected, 
    selectedId, 
    setSelectedId, 
    search, 
    setSearch, 
    statusFilter, 
    setStatusFilter, 
    sendMessage, 
    isSending, 
    updatePipeline 
  };
}
