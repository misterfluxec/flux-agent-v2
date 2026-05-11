import React, { useState, useEffect } from 'react';
import { Package, UserPlus, PlayCircle, AlertOctagon, Activity } from 'lucide-react';

interface TimelineEvent {
  id: string;
  type: string;
  title: string;
  timestamp: string;
  connector: string;
}

export function SyncTimeline() {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Polling simulation for Realtime Timeline Engine
    const fetchJobs = async () => {
      try {
        const res = await fetch('/api/v1/observability/sync-jobs?limit=15');
        if (res.ok) {
          const data = await res.json();
          // Mapeamos los jobs a Eventos de la Timeline
          const mapped = data.map((job: any) => {
            let eventType = 'sync.started';
            let title = 'Sync started';
            
            if (job.status === 'failed' || job.error_count > 0) {
              eventType = 'sync.failed';
              title = `Sync failed with ${job.error_count} errors`;
            } else if (job.status === 'success') {
              eventType = `${job.entity_type}.updated`;
              title = `${job.entity_type} updated (${job.metrics.inserted + job.metrics.updated} items)`;
            }

            return {
              id: job.id,
              type: eventType,
              title: title,
              timestamp: job.started_at ? new Date(job.started_at).toLocaleTimeString() : 'N/A',
              connector: job.connector_name
            };
          });
          setEvents(mapped);
        }
      } catch (err) {
        console.error("Failed to fetch sync jobs", err);
      } finally {
        setLoading(false);
      }
    };

    fetchJobs();
    const interval = setInterval(fetchJobs, 10000); // 10s polling to simulate Realtime Feed
    return () => clearInterval(interval);
  }, []);

  const getIcon = (type: string) => {
    if (type.includes('failed')) return <AlertOctagon className="w-4 h-4 text-rose-400" />;
    if (type.includes('started')) return <PlayCircle className="w-4 h-4 text-cyan-400" />;
    if (type.includes('customer')) return <UserPlus className="w-4 h-4 text-indigo-400" />;
    if (type.includes('catalog') || type.includes('inventory')) return <Package className="w-4 h-4 text-emerald-400" />;
    return <Activity className="w-4 h-4 text-slate-400" />;
  };

  const getBadgeColor = (type: string) => {
    if (type.includes('failed')) return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
    if (type.includes('started')) return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
    if (type.includes('customer')) return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
    if (type.includes('catalog') || type.includes('inventory')) return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
    return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
  };

  if (loading) {
    return (
      <div className="h-full px-4 py-6 flex justify-center text-slate-500">
        <Activity className="w-5 h-5 animate-spin" />
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="h-full px-4 py-6 flex flex-col items-center justify-center text-center">
        <Activity className="w-8 h-8 text-slate-600 mb-2" />
        <p className="text-sm font-medium text-slate-400">Sin actividad reciente.</p>
        <p className="text-xs text-slate-500 mt-1 max-w-[200px]">Los eventos aparecerán aquí automáticamente.</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto px-4 py-6">
      <div className="relative border-l border-white/10 ml-3 space-y-6">
        
        {events.map((e) => (
          <div key={e.id} className="relative pl-6 group">
            {/* Timeline Dot */}
            <div className="absolute -left-[13px] top-1 p-1 rounded-full bg-slate-900 border border-white/10 group-hover:border-white/30 transition-colors z-10">
              {getIcon(e.type)}
            </div>

            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between">
                <span className={`text-[10px] uppercase tracking-wider font-semibold border px-1.5 py-0.5 rounded ${getBadgeColor(e.type)}`}>
                  {e.type}
                </span>
                <span className="text-[10px] text-slate-500">{e.timestamp}</span>
              </div>
              <p className="text-sm font-medium text-slate-200 mt-1">{e.title}</p>
              <p className="text-xs text-slate-500">via {e.connector}</p>
            </div>
          </div>
        ))}
        
      </div>
    </div>
  );
}
