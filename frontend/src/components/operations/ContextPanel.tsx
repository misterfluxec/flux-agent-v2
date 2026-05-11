'use client';
import React from 'react';
import { TimelineEvent } from '@/types/operations';
import { PriorityBadge } from './PriorityBadge';
import { Tag, TrendingDown, TrendingUp, Zap, Clock, User, MessageSquareText } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { getEntityIntelligence } from '@/services/api/operations';

interface Props {
  event: TimelineEvent | null;
}

export function ContextPanel({ event }: Props) {
  if (!event) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-500 p-6 text-center">
        <p>Selecciona un evento para ver su contexto completo y tomar acciones avanzadas.</p>
      </div>
    );
  }

  const { data: intelligence, isLoading: isLoadingIntel } = useQuery({
    queryKey: ['entity-intelligence', event.aggregate?.type, event.aggregate?.id],
    queryFn: () => getEntityIntelligence(event.aggregate!.type, event.aggregate!.id),
    enabled: !!event.aggregate,
  });

  return (
    <div className="flex flex-col h-full bg-slate-900 border-l border-white/5 overflow-y-auto">
      <div className="p-4 border-b border-white/5">
        <h2 className="text-lg font-semibold text-slate-200 mb-2">Detalles del Evento</h2>
        <div className="flex items-center gap-2 mb-2">
          <PriorityBadge score={event.priority_score || 0} severity={event.severity} />
          {event.ack_state && (
            <span className="text-xs text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
              Estado: {event.ack_state}
            </span>
          )}
        </div>
        <p className="text-sm text-slate-300 font-medium">{event.summary}</p>
        <p className="text-xs text-slate-500 mt-1 font-mono">ID: {event.id}</p>
        <p className="text-xs text-slate-500 font-mono">Correlation: {event.correlation_id || 'N/A'}</p>
      </div>

      <div className="p-4 border-b border-white/5">
        <h3 className="text-sm font-medium text-slate-400 mb-2">Etiquetas (Tags)</h3>
        <div className="flex flex-wrap gap-2">
          {(event.tags ?? []).map(tag => (
            <span key={tag} className="text-xs flex items-center gap-1 text-slate-300 bg-slate-800 border border-slate-700 px-2 py-1 rounded">
              <Tag size={10} /> {tag}
            </span>
          ))}
          {(!event.tags || event.tags.length === 0) && (
            <span className="text-xs text-slate-600 italic">Sin etiquetas</span>
          )}
        </div>
      </div>

      {/* Intelligence Panel */}
      {event.aggregate ? (
        <div className="p-4 border-b border-white/5 bg-indigo-950/20">
          <div className="flex items-center gap-2 mb-4">
            <Zap className="text-indigo-400" size={16} />
            <h3 className="text-sm font-semibold text-indigo-300">Operational Intelligence</h3>
          </div>
          
          {isLoadingIntel ? (
            <div className="animate-pulse flex flex-col gap-3">
              <div className="h-10 bg-white/5 rounded"></div>
              <div className="h-10 bg-white/5 rounded"></div>
            </div>
          ) : intelligence ? (
            <div className="flex flex-col gap-4">
              
              {/* SLA & Risk */}
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2.5 bg-slate-900/50 rounded-lg border border-white/5">
                  <span className="text-[10px] text-slate-500 uppercase flex items-center gap-1 mb-1">
                    <Clock size={10} /> SLA Deadline
                  </span>
                  <span className="text-xs font-mono text-slate-200">
                    {intelligence.sla_deadline ? new Date(intelligence.sla_deadline).toLocaleTimeString() : 'N/A'}
                  </span>
                </div>
                <div className="p-2.5 bg-slate-900/50 rounded-lg border border-white/5">
                  <span className="text-[10px] text-slate-500 uppercase flex items-center gap-1 mb-1">
                    {intelligence.churn_risk === 'high' ? <TrendingDown size={10} className="text-rose-400"/> : <TrendingUp size={10} className="text-emerald-400"/>} 
                    Churn Risk
                  </span>
                  <span className={`text-xs font-semibold ${
                    intelligence.churn_risk === 'high' ? 'text-rose-400' : 
                    intelligence.churn_risk === 'medium' ? 'text-amber-400' : 'text-emerald-400'
                  }`}>
                    {intelligence.churn_risk.toUpperCase()}
                  </span>
                </div>
              </div>

              {/* LTV & Playbook */}
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2.5 bg-slate-900/50 rounded-lg border border-white/5">
                  <span className="text-[10px] text-slate-500 uppercase mb-1 block">LTV Promedio</span>
                  <span className="text-sm font-semibold text-emerald-400">${intelligence.ltv.toLocaleString()}</span>
                </div>
                <div className="p-2.5 bg-slate-900/50 rounded-lg border border-white/5">
                  <span className="text-[10px] text-slate-500 uppercase mb-1 block">Playbook</span>
                  <span className="text-xs text-cyan-300 font-medium truncate block" title={intelligence.active_playbook}>
                    {intelligence.active_playbook || 'N/A'}
                  </span>
                </div>
              </div>

              {/* Next Best Action */}
              {intelligence.next_best_action && (
                <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-lg">
                  <span className="text-[10px] text-indigo-400 uppercase font-semibold mb-1 block">Next Best Action (AI)</span>
                  <p className="text-sm text-slate-200 font-medium mb-1">{intelligence.next_best_action.action}</p>
                  <p className="text-xs text-slate-400">{intelligence.next_best_action.reason}</p>
                </div>
              )}

              {/* Notes */}
              <div className="p-3 bg-slate-900/50 border border-white/5 rounded-lg">
                <span className="text-[10px] text-slate-500 uppercase flex items-center gap-1 mb-1">
                  <MessageSquareText size={10} /> Operator Notes
                </span>
                <p className="text-xs text-slate-300 italic">
                  "{intelligence.operator_notes}"
                </p>
              </div>

            </div>
          ) : (
            <span className="text-xs text-slate-500">No hay inteligencia disponible para esta entidad.</span>
          )}
        </div>
      ) : null}

      <div className="p-4">
        <h3 className="text-sm font-medium text-slate-400 mb-2">Payload Raw</h3>
        {event.payload && Object.keys(event.payload).length > 0 ? (
          <pre className="p-3 bg-slate-950 rounded border border-white/5 text-[10px] text-slate-400 overflow-x-auto font-mono">
            {JSON.stringify(event.payload, null, 2)}
          </pre>
        ) : (
          <span className="text-xs text-slate-600 italic">No hay payload asociado</span>
        )}
      </div>
    </div>
  );
}
