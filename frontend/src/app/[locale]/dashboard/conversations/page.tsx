'use client';

import { useConversations } from '@/hooks/useConversations';
import { ConversationsList } from '@/components/conversations/ConversationsList';
import { ChatWindow } from '@/components/conversations/ChatWindow';
import { LeadIntelligence } from '@/components/conversations/LeadIntelligence';
import { MessageSquare, LayoutGrid, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function ConversationsPage() {
  const { 
    conversations, 
    selected, 
    selectedId, 
    setSelectedId, 
    search, 
    setSearch, 
    statusFilter, 
    setStatusFilter, 
    sendMessage, 
    isSending,
  } = useConversations();
  
  const pathname = usePathname();
  const segments = pathname.split('/');
  const locale = segments[1] || 'es';

  const handleTakeover = () => {
    // Tomar control de IA (simulado por ahora)
    alert('Has tomado control de la conversación. Yanua está pausada para este lead.');
  };

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] bg-background border border-border rounded-xl overflow-hidden shadow-2xl">
      {/* Header General del Inbox */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-border bg-card shrink-0">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold bg-primary/10 text-primary border border-primary/20">
            <MessageSquare className="w-4 h-4" /> 
            <span>Inbox Inteligente</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground uppercase tracking-widest bg-muted/30 px-3 py-1.5 rounded-full border border-border/50">
           Yanua <ChevronRight className="w-3 h-3" /> Live Operations
        </div>
      </div>

      {/* Intercom-style 3-Panel Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Panel Izquierdo: Lista de Leads */}
        <ConversationsList 
          conversations={conversations} 
          selectedId={selectedId} 
          onSelect={setSelectedId} 
          search={search} 
          onSearchChange={setSearch} 
          statusFilter={statusFilter} 
          onStatusFilterChange={setStatusFilter} 
        />
        
        {/* Panel Central: Chat Window */}
        <div className="flex-1 flex flex-col min-w-0">
          <ChatWindow conversation={selected} onSend={sendMessage} isSending={isSending} />
        </div>

        {/* Panel Derecho: Lead Intelligence */}
        <LeadIntelligence conversation={selected} onTakeover={handleTakeover} />
      </div>
    </div>
  );
}
