'use client';
import React from 'react';
import { useOperationsHealth } from '@/hooks/useOperationsHealth';
import { useEventBus } from '@/providers/EventBusProvider';
import { Activity, AlertTriangle, CheckCircle, Clock, ServerCrash, ShieldAlert } from 'lucide-react';

export function MissionControlBar() {
  const { report, isLoading } = useOperationsHealth(30000); // Polling 30s
  const { history } = useEventBus(); // Live events today count

  if (isLoading || !report) {
    return (
      <div className="flex items-center h-12 px-4 border-b border-white/5 bg-slate-900/50 animate-pulse">
        <div className="h-4 w-32 bg-white/10 rounded"></div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'ok': return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
      case 'warning': return 'text-amber-400 bg-amber-400/10 border-amber-400/20';
      case 'degraded': return 'text-orange-400 bg-orange-400/10 border-orange-400/20';
      case 'critical': return 'text-rose-400 bg-rose-400/10 border-rose-400/20';
      default: return 'text-slate-400 bg-slate-400/10 border-slate-400/20';
    }
  };

  const getStatusIcon = (status: string) => {
    switch(status) {
      case 'ok': return <CheckCircle size={14} />;
      case 'warning': return <Clock size={14} />;
      case 'degraded': return <AlertTriangle size={14} />;
      case 'critical': return <ServerCrash size={14} />;
      default: return <Activity size={14} />;
    }
  };

  const getTopBorderColor = (status: string) => {
    switch(status) {
      case 'ok': return 'border-t-emerald-500';
      case 'warning': return 'border-t-amber-500';
      case 'degraded': return 'border-t-orange-500';
      case 'critical': return 'border-t-rose-500';
      default: return 'border-t-slate-500';
    }
  };

  return (
    <div className={`flex flex-wrap items-center gap-4 px-4 py-2 border-b border-white/5 bg-slate-950 border-t-2 ${getTopBorderColor(report.overall_status)}`}>
      
      {/* Global Status */}
      <div className={`flex items-center gap-2 px-3 py-1.5 rounded-md border ${getStatusColor(report.overall_status)}`}>
        {getStatusIcon(report.overall_status)}
        <span className="text-xs font-semibold tracking-wide uppercase">
          {report.overall_status === 'ok' ? 'System Normal' : `Status: ${report.overall_status}`}
        </span>
      </div>

      <div className="w-px h-6 bg-white/10" />

      {/* Health Checks */}
      <div className="flex items-center gap-4 flex-1 overflow-x-auto no-scrollbar">
        {report.checks.map((check, i) => (
          <div key={i} className="flex flex-col min-w-max">
            <span className="text-[10px] text-slate-500 uppercase tracking-wider">{check.check}</span>
            <div className="flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full ${check.status === 'ok' ? 'bg-emerald-500' : check.status === 'critical' ? 'bg-rose-500' : 'bg-amber-500'}`}></span>
              <span className="text-xs text-slate-300 font-medium">{check.message}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="w-px h-6 bg-white/10" />

      {/* Live Events Metric */}
      <div className="flex flex-col items-end">
        <span className="text-[10px] text-slate-500 uppercase tracking-wider">Live Events (Session)</span>
        <span className="text-xs font-mono text-cyan-400 font-medium">
          {history.length}
        </span>
      </div>

    </div>
  );
}
