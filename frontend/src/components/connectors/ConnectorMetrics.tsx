import React, { useEffect, useState } from 'react';
import { Activity, ArrowUpRight, Zap, Database } from 'lucide-react';

export function ConnectorMetrics() {
  const [metrics, setMetrics] = useState({
    success_rate: 100.0,
    failed_jobs_24h: 0,
    avg_sync_duration_ms: 0,
    total_rows_processed: 0
  });

  useEffect(() => {
    // Polling simulation for Realtime Engine
    const fetchMetrics = async () => {
      try {
        const res = await fetch('/api/v1/observability/sync-metrics');
        if (res.ok) {
          const data = await res.json();
          setMetrics(data);
        }
      } catch (err) {
        console.error("Failed to fetch sync metrics", err);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // 30s polling
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="hidden md:flex items-center gap-6 mr-4 border-r border-white/10 pr-6">
      
      {/* Sync Confidence Score (Success Rate) */}
      <div className="flex items-center gap-3 group">
        <div className={`p-1.5 rounded transition-colors ${metrics.success_rate > 95 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
          <Activity className="w-4 h-4" />
        </div>
        <div>
          <p className="text-[10px] text-slate-500 uppercase tracking-wider group-hover:text-slate-400 transition-colors">Sync Confidence</p>
          <div className="flex items-baseline gap-1">
            <span className="text-sm font-bold text-slate-200">{metrics.success_rate.toFixed(1)}%</span>
            {metrics.success_rate > 95 && <ArrowUpRight className="w-3 h-3 text-emerald-400" />}
          </div>
        </div>
      </div>

      {/* Operational Depth (Total Rows Processed) */}
      <div className="flex items-center gap-3 group">
        <div className="p-1.5 rounded bg-indigo-500/10 text-indigo-400">
          <Database className="w-4 h-4" />
        </div>
        <div>
          <p className="text-[10px] text-slate-500 uppercase tracking-wider group-hover:text-slate-400 transition-colors">Total Rows</p>
          <div className="flex items-baseline gap-1">
            <span className="text-sm font-bold text-slate-200">{metrics.total_rows_processed.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Throughput Velocity */}
      <div className="flex items-center gap-3 group">
        <div className="p-1.5 rounded bg-cyan-500/10 text-cyan-400">
          <Zap className="w-4 h-4" />
        </div>
        <div>
          <p className="text-[10px] text-slate-500 uppercase tracking-wider group-hover:text-slate-400 transition-colors">Avg Velocity</p>
          <div className="flex items-baseline gap-1">
            <span className="text-sm font-bold text-slate-200">{metrics.avg_sync_duration_ms}</span>
            <span className="text-[10px] text-slate-500">ms/job</span>
          </div>
        </div>
      </div>

    </div>
  );
}
