import React, { useState, memo } from 'react';
import { TimelineEvent } from '@/types/operations';
import { PriorityBadge } from './PriorityBadge';
import { ActionMenu } from './ActionMenu';
import { 
  MessageSquare, ShoppingCart, UserCog, Settings, CreditCard, 
  Calendar, Zap, CheckCircle, Tag, ChevronDown, ChevronUp 
} from 'lucide-react';

interface Props {
  event: TimelineEvent;
  onAction?: (action: string, event: TimelineEvent) => void;
}

const categoryStyles: Record<string, string> = {
  interaction: 'border-l-cyan-500/50 bg-cyan-500/5',
  commerce: 'border-l-emerald-500/50 bg-emerald-500/5',
  ops: 'border-l-amber-500/50 bg-amber-500/5',
  automation: 'border-l-purple-500/50 bg-purple-500/5',
  system: 'border-l-slate-500/50 bg-slate-500/5',
  billing: 'border-l-indigo-500/50 bg-indigo-500/5',
};

function getIconForCategory(cat: string, type: string) {
  if (type.includes('payment')) return <CreditCard size={12} />;
  if (type.includes('booking')) return <Calendar size={12} />;
  if (cat === 'interaction') return <MessageSquare size={12} />;
  if (cat === 'commerce') return <ShoppingCart size={12} />;
  if (cat === 'ops') return <UserCog size={12} />;
  if (cat === 'automation') return <Zap size={12} />;
  if (cat === 'billing') return <CreditCard size={12} />;
  return <Settings size={12} />;
}

export const TimelineEventItem = memo(function TimelineEventItem({ event, onAction }: Props) {
  const [expanded, setExpanded] = useState(false);
  const time = new Date(event.timestamp).toLocaleTimeString('es-ES', { 
    hour: '2-digit', minute: '2-digit' 
  });
  
  const styleClass = categoryStyles[event.category] || categoryStyles.system;

  const isNew = event.timestamp && (Date.now() - new Date(event.timestamp).getTime() < 5000);
  const ageMs = Date.now() - new Date(event.timestamp).getTime();
  const ageHours = ageMs / 3_600_000;
  
  // Format relative time (e.g., "Hace 5m", "Hace 2h")
  const getRelativeTime = (timestamp: string) => {
    const diffSeconds = Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000);
    if (diffSeconds < 60) return "Ahora";
    if (diffSeconds < 3600) return `Hace ${Math.floor(diffSeconds / 60)}m`;
    if (diffSeconds < 86400) return `Hace ${Math.floor(diffSeconds / 3600)}h`;
    return `Hace ${Math.floor(diffSeconds / 86400)}d`;
  };
  
  const relativeTime = getRelativeTime(event.timestamp);
  
  return (
    <div className={`relative pl-6 py-3 border-l-2 ${styleClass} transition hover:bg-white/5 ${isNew ? 'animate-event-appear' : ''}`}>
      {/* Icono */}
      <div className="absolute -left-[9px] top-4 w-4 h-4 rounded-full bg-slate-900 border border-white/10 flex items-center justify-center text-slate-300">
        {getIconForCategory(event.category, event.type)}
      </div>

      {/* Contenido principal */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5 flex-wrap">
            <span className="text-sm font-medium text-slate-200">
              {event.summary}
            </span>
            <span className="text-[10px] text-slate-500 font-mono">{relativeTime} • {time}</span>
            {event.priority_score && event.priority_score > 0 && (
              <PriorityBadge score={event.priority_score} severity={event.severity} />
            )}
            
            {/* Aging Indicator */}
            {event.ack_state === 'unresolved' && ageHours > 4 && event.priority_score && event.priority_score > 70 && (
              <span className="relative flex h-2 w-2" title="SLA Risk: >4h sin resolver">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-60" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500" />
              </span>
            )}

            {event.ack_state && event.ack_state !== 'unresolved' && (
              <span className="text-[10px] flex items-center gap-1 text-emerald-400 bg-emerald-400/10 px-1.5 py-0.5 rounded">
                <CheckCircle size={10} /> {event.ack_state}
              </span>
            )}

            {/* Realtime Reconciliation Info */}
            {event.updated_by && event.updated_at && (
              <span className="text-[9px] text-indigo-400 italic flex items-center gap-0.5">
                • Actualizado por {event.updated_by.name} {getRelativeTime(event.updated_at).toLowerCase()}
              </span>
            )}
          </div>
          <div className="flex flex-wrap gap-2 mt-1">
            {(event.tags ?? []).map(tag => (
              <span key={tag} className="text-[9px] flex items-center gap-0.5 text-slate-400 bg-slate-800 border border-slate-700 px-1.5 py-0.5 rounded">
                <Tag size={8} /> {tag}
              </span>
            ))}
          </div>
        </div>

        {/* Acciones contextuales trigger */}
        <div className="flex-shrink-0 mt-0.5">
          <ActionMenu event={event} onAction={onAction} />
        </div>
      </div>

      {/* Expandible (Payload) */}
      {event.payload && Object.keys(event.payload).length > 0 && (
        <div className="mt-2">
          <button 
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-[10px] text-slate-500 hover:text-slate-300 transition-colors"
          >
            {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            {expanded ? "Ocultar detalles" : "Ver detalles payload"}
          </button>
          
          {expanded && (
            <pre className="mt-1.5 p-2.5 bg-slate-950/50 rounded-md border border-white/5 text-[10px] text-slate-400 overflow-x-auto font-mono">
              {JSON.stringify(event.payload, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
});
