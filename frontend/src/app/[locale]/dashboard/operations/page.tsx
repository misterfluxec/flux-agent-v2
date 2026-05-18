'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { MissionControlBar } from '@/components/operations/MissionControlBar';
import { UnifiedTimeline } from '@/components/operations/UnifiedTimeline';
import { ContextPanel } from '@/components/operations/ContextPanel';
import { CreateQuoteModal } from '@/components/operations/CreateQuoteModal';
import { TimelineEvent } from '@/types/operations';
import { usePriorityQueue } from '@/hooks/usePriorityQueue';
import { TimelineEventItem } from '@/components/operations/TimelineEventItem';
import { Loader2, CheckCircle } from 'lucide-react';

export default function OperationsDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // URL-persisted state
  const tabParam = searchParams.get('tab');
  const activeTab = (tabParam === 'queue' || tabParam === 'timeline') ? tabParam : 'timeline';

  const [isQuoteModalOpen, setIsQuoteModalOpen] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);

  const { queue, isLoading: queueLoading } = usePriorityQueue(20);

  const handleTabChange = (tab: 'timeline' | 'queue') => {
    const params = new URLSearchParams(searchParams.toString());
    params.set('tab', tab);
    router.replace(`?${params.toString()}`, { scroll: false });
  };

  const handleAction = (action: string, event: TimelineEvent) => {
    if (action === 'open_drawer' || action === 'view_details') {
      setSelectedEvent(event);
    }
  };

  // Keyboard shortcut to close panel
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSelectedEvent(null);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] overflow-hidden bg-slate-950 text-slate-200">
      {/* CAPA 1: Mission Control (Health + Metrics) */}
      <MissionControlBar />

      {/* CAPA 2: Tabs de Vista (Mobile/Tablet only) */}
      <div className="xl:hidden flex items-center gap-4 px-4 py-3 border-b border-white/5 bg-slate-900/30">
        <button 
          onClick={() => handleTabChange('timeline')}
          className={`text-sm font-medium transition-colors ${activeTab === 'timeline' ? 'text-cyan-400' : 'text-slate-400 hover:text-slate-200'}`}
        >
          Chat Activo
        </button>
        <button 
          onClick={() => handleTabChange('queue')}
          className={`text-sm font-medium transition-colors ${activeTab === 'queue' ? 'text-cyan-400' : 'text-slate-400 hover:text-slate-200'}`}
        >
          Inbox
          <span className="ml-2 px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-400 text-[10px]">
            3
          </span>
        </button>
      </div>

      {/* CAPA 3: Área de contenido 3 Columnas (Inbox / Chat / CRM Context) */}
      <div className="flex-1 flex overflow-hidden relative">
        
        {/* Columna 1: INBOX (Live, Pendientes, Historial) */}
        <div className={`
          flex-col w-full xl:w-[320px] border-r border-white/5 bg-slate-900/10 h-full
          ${activeTab === 'queue' ? 'flex' : 'hidden xl:flex'}
        `}>
          <div className="p-3 border-b border-white/5 bg-slate-900/30 hidden xl:flex items-center justify-between">
            <h2 className="text-sm font-medium text-slate-300">Inbox</h2>
            <div className="flex gap-1">
              <span className="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-400 text-[10px] font-medium cursor-pointer">
                🔴 2 Live
              </span>
              <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 text-[10px] font-medium cursor-pointer">
                🟡 1 Pend.
              </span>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-3">
            {/* MOCK INBOX LIST */}
            <div className="space-y-2">
              <div className="bg-white/5 border border-rose-500/30 rounded-lg p-3 cursor-pointer hover:bg-white/10 transition-colors" onClick={() => setSelectedEvent({} as any)}>
                <div className="flex justify-between items-start mb-1">
                  <span className="text-xs font-bold text-white/90">Carlos Mendoza</span>
                  <span className="text-[10px] text-rose-400 font-bold animate-pulse">LIVE</span>
                </div>
                <p className="text-[11px] text-slate-400 truncate">Handoff: "Necesito hablar con un humano por favor"</p>
                <p className="text-[10px] text-slate-500 mt-2">Hace 2 min vía WhatsApp</p>
              </div>

              <div className="bg-white/5 border border-amber-500/30 rounded-lg p-3 cursor-pointer hover:bg-white/10 transition-colors" onClick={() => setSelectedEvent({} as any)}>
                <div className="flex justify-between items-start mb-1">
                  <span className="text-xs font-bold text-white/90">María López</span>
                  <span className="text-[10px] text-amber-400 font-bold">WAITING</span>
                </div>
                <p className="text-[11px] text-slate-400 truncate">Lead: Solicitó cotización de servicio Pro</p>
                <p className="text-[10px] text-slate-500 mt-2">Hace 32 min vía Telegram</p>
              </div>

              <div className="bg-white/[0.02] border border-white/5 rounded-lg p-3 cursor-pointer hover:bg-white/10 transition-colors">
                <div className="flex justify-between items-start mb-1">
                  <span className="text-xs font-bold text-white/70">Juan Pérez</span>
                  <span className="text-[10px] text-emerald-400 font-bold">SOLVED</span>
                </div>
                <p className="text-[11px] text-slate-500 truncate">Bot cerró la venta satisfactoriamente</p>
                <p className="text-[10px] text-slate-600 mt-2">Ayer 14:30 vía Web</p>
              </div>
            </div>
          </div>
        </div>

        {/* Columna 2: CHAT EN VIVO */}
        <div className={`
          flex-1 flex-col h-full bg-slate-950
          ${activeTab === 'timeline' ? 'flex' : 'hidden xl:flex'}
        `}>
          <div className="p-3 border-b border-white/5 bg-slate-900/30 hidden xl:flex items-center justify-between">
            <h2 className="text-sm font-medium text-slate-300">Chat Activo: Carlos Mendoza</h2>
            <div className="flex items-center gap-2">
              <button className="px-3 py-1 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 rounded text-xs transition-colors">
                Marcar Resuelto (Release to IA)
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-hidden relative flex flex-col">
             {/* Área de mensajes mock */}
             <div className="flex-1 overflow-y-auto p-4 space-y-4">
                <div className="flex flex-col items-center mb-6">
                   <span className="text-xs text-slate-500 bg-slate-900 px-3 py-1 rounded-full">Bot atendió durante 5 minutos</span>
                </div>
                <div className="flex justify-end">
                   <div className="bg-cyan-900/30 text-cyan-100 text-sm p-3 rounded-l-xl rounded-br-xl max-w-[70%]">
                      Hola, quería saber el precio del plan Pro.
                   </div>
                </div>
                <div className="flex justify-start">
                   <div className="bg-slate-800 text-slate-200 text-sm p-3 rounded-r-xl rounded-bl-xl max-w-[70%] border border-slate-700">
                      <strong>Sales Bot:</strong> ¡Hola! El plan Pro tiene un costo de $99/mes. ¿Te gustaría que te envíe una cotización formal?
                   </div>
                </div>
                <div className="flex justify-end">
                   <div className="bg-cyan-900/30 text-cyan-100 text-sm p-3 rounded-l-xl rounded-br-xl max-w-[70%]">
                      Sí, pero tengo una duda técnica. Necesito hablar con un humano por favor.
                   </div>
                </div>
                <div className="flex flex-col items-center my-4">
                   <span className="text-xs font-bold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-3 py-1 rounded-full uppercase tracking-widest animate-pulse">
                      Handoff Requested (Humano requerido)
                   </span>
                </div>
             </div>
             {/* Input area */}
             <div className="p-3 bg-slate-900/50 border-t border-white/5">
               <div className="flex gap-2">
                 <input type="text" placeholder="Escribe tu mensaje como operador..." className="flex-1 bg-slate-950 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500" />
                 <button className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm font-medium transition-colors">Enviar</button>
               </div>
             </div>
          </div>
        </div>

        {/* Columna 3: CRM CONTEXT + ACCIONES */}
        <div className={`
          w-[320px] 2xl:w-[380px] h-full hidden lg:block border-l border-white/5 bg-slate-900/30
          transition-all duration-300 ease-in-out
          ${selectedEvent ? 'translate-x-0' : 'translate-x-[400px] absolute right-0'}
        `}>
           <div className="h-full flex flex-col">
            <div className="p-4 border-b border-white/5">
              <h2 className="text-lg font-bold text-white mb-1">Carlos Mendoza</h2>
              <p className="text-xs text-slate-400 flex items-center gap-2">
                <span className="text-emerald-400">●</span> +593 99 123 4567
              </p>
              <div className="flex gap-2 mt-3">
                 <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 text-[10px] font-bold uppercase tracking-wider">Cliente VIP</span>
                 <span className="px-2 py-0.5 rounded bg-slate-700 text-slate-300 text-[10px] font-bold uppercase tracking-wider">Tech</span>
              </div>
            </div>

            {/* Smart Actions (Contextuales) */}
            <div className="p-4 border-b border-white/5 bg-cyan-900/10">
               <h3 className="text-[10px] font-bold text-cyan-500 uppercase tracking-widest mb-3">Acciones Sugeridas por IA</h3>
               <div className="space-y-2">
                 <button 
                   onClick={() => setIsQuoteModalOpen(true)}
                   className="w-full flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs rounded border border-slate-700 transition-colors"
                 >
                    <span>💰</span> Generar Cotización
                 </button>
                 <button className="w-full flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs rounded border border-slate-700 transition-colors">
                    <span>📅</span> Agendar Demo Técnica
                 </button>
                 <button className="w-full flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs rounded border border-slate-700 transition-colors">
                    <span>🏷️</span> Agregar Tag "Interesado"
                 </button>
               </div>
            </div>

            <div className="flex-1 overflow-y-auto">
               <ContextPanel event={selectedEvent} />
            </div>
          </div>
        </div>
        
        {/* Mobile slide-over for Context Panel */}
        {selectedEvent && (
          <div className="lg:hidden absolute inset-0 z-50 flex justify-end bg-slate-950/50 backdrop-blur-sm">
            <div className="w-[85%] max-w-[320px] h-full bg-slate-900 border-l border-white/10 shadow-2xl animate-in slide-in-from-right">
              <div className="flex justify-between items-center p-3 border-b border-white/5 bg-slate-950">
                <span className="text-sm font-medium text-slate-200">CRM Context</span>
                <button 
                  onClick={() => setSelectedEvent(null)}
                  className="text-slate-400 hover:text-white p-1"
                >
                  ✕
                </button>
              </div>
              <div className="h-[calc(100%-3rem)]">
                <ContextPanel event={selectedEvent} />
              </div>
            </div>
          </div>
        )}

        <CreateQuoteModal 
          isOpen={isQuoteModalOpen} 
          onClose={() => setIsQuoteModalOpen(false)} 
          customerId="carlos_mendoza_123" 
          customerName="Carlos Mendoza" 
        />
      </div>
    </div>
  );
}
