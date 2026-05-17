'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getInsights, acknowledgeInsight, type CopilotInsight } from '@/services/api/intelligence';
import { useRealtimeEvents } from '@/hooks/useRealtimeEvents';
import { PermissionGate } from '@/components/system/PermissionGate';

export function CopilotPanel() {
  const [acknowledgedIds, setAcknowledgedIds] = useState<Set<string>>(new Set());

  // Cargar insights iniciales
  const { data: insights = [], refetch } = useQuery({
    queryKey: ['copilot', 'insights'],
    queryFn: () => getInsights({ limit: 5, priority: 'high' }),
    staleTime: 30_000, // 30 segundos
  });

  // Escuchar eventos en tiempo real a nivel global
  useRealtimeEvents();

  const handleAcknowledge = async (insight: CopilotInsight, action: 'accepted' | 'dismissed') => {
    await acknowledgeInsight(insight.id, action);
    setAcknowledgedIds(prev => new Set(prev).add(insight.id));
    refetch();
  };

  const priorityColors = {
    low: 'border-slate-600 bg-slate-800/50',
    medium: 'border-amber-500/50 bg-amber-900/20',
    high: 'border-orange-500/50 bg-orange-900/20',
    critical: 'border-red-500/50 bg-red-900/20 animate-pulse'
  };

  return (
    <PermissionGate feature="ai.recommendations.view" behavior="upsell">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-purple-400">✨ Yanua Copilot</h3>
          <button 
            onClick={() => refetch()}
            className="text-[10px] text-slate-400 hover:text-slate-200"
          >
            ↻ Refresh
          </button>
        </div>

        {insights.filter(i => !acknowledgedIds.has(i.id)).map(insight => (
          <div 
            key={insight.id}
            className={`p-3 rounded-lg border ${priorityColors[insight.priority]} transition-all`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <p className="text-xs font-medium text-slate-100">{insight.title}</p>
                <p className="text-[10px] text-slate-400 mt-1">{insight.description}</p>
              </div>
              
              {insight.actionable && (
                <div className="flex gap-1">
                  <button
                    onClick={() => handleAcknowledge(insight, 'accepted')}
                    className="px-2 py-1 text-[10px] bg-cyan-600 hover:bg-cyan-500 rounded text-white"
                  >
                    {insight.action_label || 'Actuar'}
                  </button>
                  <button
                    onClick={() => handleAcknowledge(insight, 'dismissed')}
                    className="px-2 py-1 text-[10px] bg-slate-700 hover:bg-slate-600 rounded text-slate-300"
                  >
                    ✕
                  </button>
                </div>
              )}
            </div>
            
            {insight.metadata?.correlation_id && (
              <p className="text-[9px] text-slate-500 mt-2 font-mono">
                ID: {insight.metadata.correlation_id.slice(0, 8)}...
              </p>
            )}
          </div>
        ))}

        {insights.filter(i => !acknowledgedIds.has(i.id)).length === 0 && (
          <p className="text-xs text-slate-500 text-center py-4">
            🎯 Todo bajo control. Yanua te avisará si hay algo importante.
          </p>
        )}
      </div>
    </PermissionGate>
  );
}
