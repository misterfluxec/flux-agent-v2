'use client';
import { useConversations } from '@/hooks/useConversations';
import { ConversationsList } from '@/components/conversations/ConversationsList';
import { ChatWindow } from '@/components/conversations/ChatWindow';
import { PipelineBoard } from '@/components/conversations/PipelineBoard';
import { MessageSquare, LayoutGrid, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTranslations } from 'next-intl';

export default function ConversationsPage() {
  const t = useTranslations('conversations');
  const { 
    conversations, 
    allConversations,
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
  } = useConversations();
  
  const pathname = usePathname();
  const isPipeline = pathname.includes('/pipeline');
  
  // Extraer locale de la ruta para los links
  const segments = pathname.split('/');
  const locale = segments[1]; // [locale] es el primer segmento

  return (
    <div className="flex flex-col h-screen max-h-[calc(100vh-4rem)] bg-background">
      {/* Navbar Interno / Tabs */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-border bg-card shrink-0">
        <div className="flex items-center gap-2">
          <Link 
            href={`/${locale}/dashboard/conversations`} 
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${
              !isPipeline 
              ? 'bg-primary text-primary-foreground shadow-md shadow-primary/20 scale-105' 
              : 'text-muted-foreground hover:bg-accent'
            }`}
          >
            <MessageSquare className="w-4 h-4" /> 
            <span className="hidden sm:inline">Bandeja de Entrada</span>
          </Link>
          <Link 
            href={`/${locale}/dashboard/conversations/pipeline`} 
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${
              isPipeline 
              ? 'bg-primary text-primary-foreground shadow-md shadow-primary/20 scale-105' 
              : 'text-muted-foreground hover:bg-accent'
            }`}
          >
            <LayoutGrid className="w-4 h-4" /> 
            <span className="hidden sm:inline">Pipeline CRM</span>
          </Link>
        </div>
        
        <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground uppercase tracking-widest bg-muted/50 px-3 py-1.5 rounded-full border border-border/50">
           Dashboard <ChevronRight className="w-3 h-3" /> Conversaciones
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {!isPipeline ? (
          <>
            <ConversationsList 
              conversations={conversations} 
              selectedId={selectedId} 
              onSelect={setSelectedId} 
              search={search} 
              onSearchChange={setSearch} 
              statusFilter={statusFilter} 
              onStatusFilterChange={setStatusFilter} 
            />
            <ChatWindow conversation={selected} onSend={sendMessage} isSending={isSending} />
          </>
        ) : (
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="px-6 py-4 border-b border-border bg-card/50 flex justify-between items-center shrink-0">
              <div className="flex flex-col">
                <h2 className="font-bold text-lg leading-none">Pipeline de Leads</h2>
                <p className="text-xs text-muted-foreground mt-1">Gestiona el progreso de tus clientes potenciales</p>
              </div>
              <div className="flex gap-2">
                 <div className="bg-green-500/10 text-green-600 text-[10px] font-bold px-2 py-1 rounded-md border border-green-500/10">
                   Meta: 15 Conversiones
                 </div>
              </div>
            </div>
            <PipelineBoard conversations={allConversations} onUpdateStage={updatePipeline} />
          </div>
        )}
      </div>
    </div>
  );
}
