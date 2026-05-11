'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { MissionControlBar } from '@/components/operations/MissionControlBar';
import { UnifiedTimeline } from '@/components/operations/UnifiedTimeline';
import { ContextPanel } from '@/components/operations/ContextPanel';
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
          Global Timeline (Live)
        </button>
        <button 
          onClick={() => handleTabChange('queue')}
          className={`text-sm font-medium transition-colors ${activeTab === 'queue' ? 'text-cyan-400' : 'text-slate-400 hover:text-slate-200'}`}
        >
          Priority Queue
          {queue && queue.length > 0 && (
            <span className="ml-2 px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-400 text-[10px]">
              {queue.length}
            </span>
          )}
        </button>
      </div>

      {/* CAPA 3: Área de contenido 3 Columnas */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Columna 1: Priority Queue (Visible en desktop o si tab=queue) */}
        <div className={`
          flex-col w-full xl:w-[320px] border-r border-white/5 bg-slate-900/10 h-full
          ${activeTab === 'queue' ? 'flex' : 'hidden xl:flex'}
        `}>
          <div className="p-3 border-b border-white/5 bg-slate-900/30 hidden xl:flex items-center justify-between">
            <h2 className="text-sm font-medium text-slate-300">Priority Queue</h2>
            {queue && queue.length > 0 && (
              <span className="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-400 text-[10px] font-medium">
                {queue.length} pendientes
              </span>
            )}
          </div>
          <div className="flex-1 overflow-y-auto p-3">
            {queueLoading ? (
              <div className="flex justify-center p-8 text-slate-500"><Loader2 className="animate-spin w-5 h-5" /></div>
            ) : !queue || queue.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-[300px] p-8 text-center">
                <div className="w-16 h-16 rounded-full bg-emerald-500/10 flex items-center justify-center mb-4">
                  <CheckCircle className="w-8 h-8 text-emerald-500/80" />
                </div>
                <h3 className="text-sm font-semibold text-slate-200 mb-1">Queue Libre</h3>
                <p className="text-[11px] text-slate-500 max-w-[200px]">¡Excelente! El equipo está al día con todas las alertas críticas.</p>
              </div>
            ) : (
              <div className="space-y-1">
                {queue.map(event => (
                  <TimelineEventItem 
                    key={event.id} 
                    event={event} 
                    onAction={handleAction} 
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Columna 2: Unified Timeline (Visible en desktop o si tab=timeline) */}
        <div className={`
          flex-1 flex-col h-full bg-slate-950
          ${activeTab === 'timeline' ? 'flex' : 'hidden xl:flex'}
        `}>
          <div className="p-3 border-b border-white/5 bg-slate-900/30 hidden xl:flex items-center justify-between">
            <h2 className="text-sm font-medium text-slate-300">Global Timeline (Live)</h2>
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-60" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
              </span>
              <span className="text-[10px] text-cyan-500/70 uppercase tracking-wider font-semibold">Live Sync</span>
            </div>
          </div>
          <div className="flex-1 overflow-hidden relative">
            <UnifiedTimeline onAction={handleAction} />
          </div>
        </div>

        {/* Columna 3: Context Panel */}
        <div className={`
          w-[320px] 2xl:w-[380px] h-full hidden lg:block border-l border-white/5 bg-slate-900/30
          transition-all duration-300 ease-in-out
          ${selectedEvent ? 'translate-x-0' : 'translate-x-[400px] absolute right-0'}
        `}>
          <ContextPanel event={selectedEvent} />
        </div>
        
        {/* Mobile slide-over for Context Panel */}
        {selectedEvent && (
          <div className="lg:hidden absolute inset-0 z-50 flex justify-end bg-slate-950/50 backdrop-blur-sm">
            <div className="w-[85%] max-w-[320px] h-full bg-slate-900 border-l border-white/10 shadow-2xl animate-in slide-in-from-right">
              <div className="flex justify-between items-center p-3 border-b border-white/5 bg-slate-950">
                <span className="text-sm font-medium text-slate-200">Contexto</span>
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
      </div>
    </div>
  );
}
