'use client';
import React, { useState } from 'react';
import { useOperationsTimeline } from '@/hooks/useOperationsTimeline';
import { TimelineEventItem } from './TimelineEventItem';
import { TimelineEvent, AggregateType } from '@/types/operations';
import { Loader2, RefreshCw, MessageSquare } from 'lucide-react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { useMemo, useRef } from 'react';

type TimelineRow = 
  | { type: 'header', id: string, date: string }
  | { type: 'event', id: string, event: TimelineEvent };

interface Props {
  aggregateType?: AggregateType;
  aggregateId?: string;
  realtime?: boolean;
  onAction?: (action: string, event: TimelineEvent) => void;
}

export function UnifiedTimeline({ 
  aggregateType, 
  aggregateId, 
  realtime = true,
  onAction 
}: Props) {
  const { 
    events, 
    groupedEvents, 
    isLoading, 
    isError, 
    refetch,
    liveEventsCount,
    pendingBurstCount,
    flushBurst
  } = useOperationsTimeline({
    aggregateType,
    aggregateId,
    limit: 50,
    realtime
  });

  const parentRef = useRef<HTMLDivElement>(null);

  const rows: TimelineRow[] = useMemo(() => {
    const result: TimelineRow[] = [];
    Object.entries(groupedEvents).forEach(([date, dayEvents]) => {
      result.push({ type: 'header', id: `header-${date}`, date });
      dayEvents.forEach(event => {
        result.push({ type: 'event', id: event.id, event });
      });
    });
    return result;
  }, [groupedEvents]);

  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (index) => rows[index].type === 'header' ? 32 : 100,
    overscan: 10,
  });

  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refetch();
    setIsRefreshing(false);
  };

  if (isLoading && events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-slate-400">
        <Loader2 className="animate-spin mb-4" size={24} />
        <p className="text-sm">Cargando línea de tiempo...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-8 text-center text-rose-400">
        <p className="mb-4">Error cargando la línea de tiempo.</p>
        <button 
          onClick={() => refetch()}
          className="px-4 py-2 bg-rose-500/10 border border-rose-500/30 rounded text-sm hover:bg-rose-500/20"
        >
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-slate-950 relative">
      {/* Header timeline */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/5 bg-slate-900/50">
        <div className="flex items-center gap-3">
          <h3 className="font-medium text-slate-200">
            {aggregateType ? 'Timeline de Entidad' : 'Timeline Global (Live)'}
          </h3>
          {liveEventsCount > 0 && (
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
            </span>
          )}
        </div>
        <button 
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="p-1.5 text-slate-400 hover:text-white hover:bg-white/10 rounded transition-colors disabled:opacity-50"
        >
          <RefreshCw size={14} className={isRefreshing ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Burst Backpressure Pill */}
      {pendingBurstCount > 0 && (
        <div className="absolute top-16 left-1/2 -translate-x-1/2 z-50">
          <button
            onClick={flushBurst}
            className="flex items-center gap-2 px-4 py-1.5 bg-indigo-500 hover:bg-indigo-400 text-white text-xs font-semibold rounded-full shadow-lg shadow-indigo-500/20 transition-all animate-bounce"
          >
            {pendingBurstCount} nuevos eventos
          </button>
        </div>
      )}

      {/* Lista de eventos */}
      <div className="flex-1 overflow-y-auto pb-8 relative" ref={parentRef}>
        {events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full min-h-[300px] p-12 text-center">
            <div className="w-16 h-16 rounded-full bg-slate-800/50 border border-slate-700/50 flex items-center justify-center mb-4">
              <MessageSquare className="w-8 h-8 text-slate-500/50" />
            </div>
            <h3 className="text-sm font-semibold text-slate-300 mb-1">Sin Actividad Registrada</h3>
            <p className="text-xs text-slate-500 max-w-[250px]">La línea de tiempo se llenará automáticamente a medida que ocurran eventos en el sistema.</p>
          </div>
        ) : (
          <div 
            style={{ 
              height: `${rowVirtualizer.getTotalSize()}px`, 
              width: '100%', 
              position: 'relative' 
            }}
          >
            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const row = rows[virtualRow.index];
              return (
                <div
                  key={row.id}
                  data-index={virtualRow.index}
                  ref={rowVirtualizer.measureElement}
                  className="absolute top-0 left-0 w-full"
                  style={{
                    transform: `translateY(${virtualRow.start}px)`
                  }}
                >
                  {row.type === 'header' ? (
                    <div className="px-4 py-1.5 bg-slate-950/90 backdrop-blur-md border-y border-white/5 mb-1">
                      <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">{row.date}</span>
                    </div>
                  ) : (
                    <div className="mb-0.5">
                      <TimelineEventItem 
                        event={row.event} 
                        onAction={onAction}
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
