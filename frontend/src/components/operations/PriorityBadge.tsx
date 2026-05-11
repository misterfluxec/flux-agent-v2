import React from 'react';

export interface PriorityBadgeProps {
  score: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

const severityConfig = {
  critical: { bg: 'bg-rose-500/10', border: 'border-rose-500/30', text: 'text-rose-400', label: 'CRÍTICO' },
  high:     { bg: 'bg-orange-500/10', border: 'border-orange-500/30', text: 'text-orange-400', label: 'ALTO' },
  medium:   { bg: 'bg-amber-500/10', border: 'border-amber-500/30', text: 'text-amber-400', label: 'MEDIO' },
  low:      { bg: 'bg-slate-500/10', border: 'border-slate-500/30', text: 'text-slate-400', label: 'BAJO' },
};

export function PriorityBadge({ score, severity }: PriorityBadgeProps) {
  const config = severityConfig[severity] || severityConfig.low;
  
  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-medium border ${config.bg} ${config.border} ${config.text}`}>
      <span className="opacity-70">{config.label}</span>
      {score > 0 && (
        <>
          <div className="w-px h-2.5 bg-current opacity-30" />
          <span>{score} pts</span>
        </>
      )}
    </div>
  );
}
