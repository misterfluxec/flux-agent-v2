'use client';

import React, { useState } from 'react';
import { UnifiedTimeline } from '@/components/operations/UnifiedTimeline';
import { ActionDrawer } from '@/components/operations/ActionDrawer';
import { TimelineEvent, AggregateType } from '@/types/operations';
import { ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function OperationDetailView({ 
  params 
}: { 
  params: { locale: string; type: AggregateType; id: string } 
}) {
  const router = useRouter();
  const { type, id } = params;
  
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);

  const handleAction = (action: string, event: TimelineEvent) => {
    if (action === 'open_drawer') {
      setSelectedEvent(event);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] overflow-hidden bg-slate-950 text-slate-200">
      {/* Header */}
      <div className="flex items-center gap-4 px-4 py-3 border-b border-white/5 bg-slate-900/50">
        <button 
          onClick={() => router.back()}
          className="p-1.5 hover:bg-white/10 rounded text-slate-400 transition-colors"
        >
          <ArrowLeft size={18} />
        </button>
        <div>
          <h2 className="text-lg font-semibold text-slate-200 capitalize">
            {type} <span className="text-slate-500 font-normal">#{id.slice(0,8)}</span>
          </h2>
          <p className="text-xs text-slate-500">Vista detallada operacional</p>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Panel izquierdo: Timeline de esta entidad específica */}
        <div className="flex-1 border-r border-white/5 overflow-hidden">
          <UnifiedTimeline 
            aggregateType={type} 
            aggregateId={id} 
            onAction={handleAction} 
          />
        </div>

        {/* Panel derecho: Contexto de la entidad (CRM, info) */}
        <div className="w-80 bg-slate-900/30 overflow-y-auto p-4 hidden lg:block">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 uppercase tracking-wider">Contexto de la Entidad</h3>
          <div className="p-4 rounded-md border border-white/5 bg-slate-950">
            <p className="text-xs text-slate-500">Tipo: {type}</p>
            <p className="text-xs text-slate-500 font-mono mt-1">ID: {id}</p>
            <p className="text-xs text-slate-400 mt-4">
              Aquí se integrarán los detalles específicos de negocio (CRM, montos, contacto)
              según el type de agregado.
            </p>
          </div>
        </div>

        {/* Action Drawer global para eventos dentro de este timeline */}
        {selectedEvent && (
          <ActionDrawer 
            event={selectedEvent} 
            onClose={() => setSelectedEvent(null)} 
          />
        )}
      </div>
    </div>
  );
}
