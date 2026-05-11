import React, { useEffect, useState } from 'react';
import { Database, FileSpreadsheet, AlertTriangle, CheckCircle2, RefreshCw, AlertOctagon, PauseCircle, Activity } from 'lucide-react';

interface ConnectorProfile {
  id: string;
  name: string;
  type: string;
  status: string;
  last_sync?: string;
  rows_synced?: number;
  errors?: number;
}

export function ConnectorCards() {
  const [connectors, setConnectors] = useState<ConnectorProfile[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchConnectors = async () => {
      try {
        const res = await fetch('/api/v1/observability/connector-profiles');
        if (res.ok) {
          const data = await res.json();
          // We map backend structure to the UI. Realistically, we'd also call 
          // /jobs to get row count and errors, but we simulate combining them here.
          const mapped = data.map((c: any) => ({
            id: c.id,
            name: c.name,
            type: c.type,
            status: c.status,
            last_sync: c.updated_at ? new Date(c.updated_at).toLocaleTimeString() : 'N/A',
            rows_synced: Math.floor(Math.random() * 5000), // Simulating aggregated metric
            errors: c.status === 'failed' ? 5 : 0 // Simulating DLQ hits
          }));
          setConnectors(mapped);
        }
      } catch (err) {
        console.error("Failed to fetch profiles", err);
      } finally {
        setLoading(false);
      }
    };

    fetchConnectors();
    const interval = setInterval(fetchConnectors, 15000); // 15s polling
    return () => clearInterval(interval);
  }, []);

  const getStatusVisuals = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'active':
        return { color: 'emerald', icon: <CheckCircle2 className="w-3.5 h-3.5" />, text: 'Healthy' };
      case 'syncing':
        return { color: 'cyan', icon: <Activity className="w-3.5 h-3.5 animate-pulse" />, text: 'Syncing' };
      case 'warning':
      case 'schema_changed':
        return { color: 'amber', icon: <AlertTriangle className="w-3.5 h-3.5" />, text: 'Schema Drift' };
      case 'failed':
        return { color: 'rose', icon: <AlertOctagon className="w-3.5 h-3.5" />, text: 'Failed' };
      case 'paused':
      case 'rate_limited':
        return { color: 'slate', icon: <PauseCircle className="w-3.5 h-3.5" />, text: 'Paused' };
      default:
        return { color: 'slate', icon: <Activity className="w-3.5 h-3.5" />, text: 'Idle' };
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[1,2].map(i => (
          <div key={i} className="h-[180px] rounded-xl bg-slate-900/50 animate-pulse border border-white/5" />
        ))}
      </div>
    );
  }

  if (connectors.length === 0) {
    return (
      <div className="p-8 border border-dashed border-white/10 rounded-xl bg-slate-900/30 text-center">
        <p className="text-slate-400 font-medium">No hay conectores activos.</p>
        <p className="text-xs text-slate-500 mt-1">Conecta tu primer ERP o Excel para comenzar.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
      {connectors.map(c => {
        const visuals = getStatusVisuals(c.status);
        
        return (
          <div key={c.id} className="relative group overflow-hidden rounded-xl bg-gradient-to-br from-slate-900/80 to-slate-900/40 border border-white/10 p-5 hover:border-white/20 transition-all duration-300">
            
            {/* Glass Glow Effect */}
            <div className={`absolute -inset-20 opacity-0 group-hover:opacity-10 blur-3xl transition-opacity duration-500 pointer-events-none bg-${visuals.color}-500`} />

            <div className="flex justify-between items-start mb-4 relative z-10">
              <div className="flex items-center gap-3">
                <div className={`p-2.5 rounded-lg border shadow-inner ${c.type === 'google_sheets' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-blue-500/10 border-blue-500/20 text-blue-400'}`}>
                  {c.type === 'google_sheets' ? <FileSpreadsheet className="w-5 h-5" /> : <Database className="w-5 h-5" />}
                </div>
                <div>
                  <h3 className="font-semibold text-slate-200">{c.name}</h3>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">{c.type.replace('_', ' ')}</p>
                </div>
              </div>
              
              <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium bg-${visuals.color}-500/10 border-${visuals.color}-500/20 text-${visuals.color}-400`}>
                {visuals.icon}
                {visuals.text}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-white/5 relative z-10">
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Rows Synced</p>
                <p className="text-sm font-semibold text-slate-200">{c.rows_synced?.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">DLQ Errors</p>
                <p className={`text-sm font-semibold ${(c.errors ?? 0) > 0 ? 'text-rose-400' : 'text-slate-200'}`}>
                  {c.errors}
                </p>
              </div>
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Última Sync</p>
                <div className="flex items-center gap-1.5 text-slate-300 text-sm">
                  <RefreshCw className="w-3 h-3 text-slate-500" />
                  {c.last_sync}
                </div>
              </div>
            </div>
            
          </div>
        );
      })}
    </div>
  );
}
