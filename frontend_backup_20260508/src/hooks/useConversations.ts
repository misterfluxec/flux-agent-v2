import { useState, useEffect, useCallback } from 'react';
import { Conversation, Message, MOCK_CONVERSATIONS, PipelineStage } from '@/types/conversation';

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>(MOCK_CONVERSATIONS);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isSending, setIsSending] = useState(false);

  // Simulación de mensajes entrantes en "tiempo real"
  useEffect(() => {
    const interval = setInterval(() => {
      setConversations(prev => prev.map(c => 
        c.id === '2' ? { ...c, unreadCount: c.unreadCount + 1, lastMessage: '¿Sigue disponible el descuento?', lastMessageTime: new Date().toISOString() } : c
      ));
    }, 15000);
    return () => clearInterval(interval);
  }, []);

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
