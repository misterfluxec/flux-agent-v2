import { useIngestionStats } from '@/app/dashboard/centro-de-datos/hooks/useIngestionStats';
import { Brain, Database, Activity, Clock, RefreshCw } from 'lucide-react';

function formatTimeAgo(dateStr: string | null): string {
  if (!dateStr) return 'Nunca';
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (diff < 60) return 'Hace <1 min';
  if (diff < 3600) return `Hace ${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `Hace ${Math.floor(diff / 3600)} h`;
  return new Date(dateStr).toLocaleDateString();
}

export function DataHubMetrics() {
  const { data, isLoading, refetch } = useIngestionStats();

  if (isLoading) return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
      {Array(4).fill(0).map((_, i) => (
        <div key={i} className="h-32 bg-gray-900/40 backdrop-blur-md rounded-2xl border border-gray-800/50" />
      ))}
    </div>
  );

  const metrics = [
    { 
      label: 'IA Brain Capacity', 
      value: `${((data?.total_tokens || 0) / 1000).toFixed(1)}K`, 
      sub: `${data?.total_chunks || 0} fragmentos indexados`, 
      icon: Brain, 
      color: 'text-fuchsia-400', 
      bg: 'bg-fuchsia-500/10', 
      border: 'border-fuchsia-500/20',
      gradient: 'from-fuchsia-500/20 to-transparent'
    },
    { 
      label: 'Catálogo Activo', 
      value: data?.active_products || 0, 
      sub: 'productos/servicios en RAG', 
      icon: Database, 
      color: 'text-indigo-400', 
      bg: 'bg-indigo-500/10', 
      border: 'border-indigo-500/20',
      gradient: 'from-indigo-500/20 to-transparent'
    },
    { 
      label: 'Salud de Sync', 
      value: `${data?.success_rate || 0}%`, 
      sub: `${data?.active_sources || 0} fuentes activas`, 
      icon: Activity, 
      color: (data?.success_rate || 0) > 90 ? 'text-emerald-400' : 'text-amber-400', 
      bg: (data?.success_rate || 0) > 90 ? 'bg-emerald-500/10' : 'bg-amber-500/10', 
      border: (data?.success_rate || 0) > 90 ? 'border-emerald-500/20' : 'border-amber-500/20',
      gradient: (data?.success_rate || 0) > 90 ? 'from-emerald-500/20 to-transparent' : 'from-amber-500/20 to-transparent'
    },
    { 
      label: 'Latencia de Ingesta', 
      value: `${data?.avg_index_time_seconds || 0}s`, 
      sub: `Última: ${formatTimeAgo(data?.last_sync_at || null)}`, 
      icon: Clock, 
      color: 'text-cyan-400', 
      bg: 'bg-cyan-500/10', 
      border: 'border-cyan-500/20',
      gradient: 'from-cyan-500/20 to-transparent'
    }
  ];

  return (
    <div className="space-y-6 mb-8">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold text-gray-500 uppercase tracking-widest flex items-center gap-2">
          <Activity className="w-4 h-4" />
          Métricas de Inteligencia
        </h2>
        <button 
          onClick={refetch} 
          className="p-2 hover:bg-white/5 rounded-xl transition-all duration-300 text-gray-500 hover:text-white"
          title="Actualizar métricas"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((m, i) => (
          <div key={i} className={`relative overflow-hidden bg-black/40 backdrop-blur-xl border ${m.border} rounded-2xl p-5 hover:border-white/20 transition-all duration-500 group shadow-2xl`}>
            {/* Ambient Background Gradient */}
            <div className={`absolute inset-0 bg-gradient-to-br ${m.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-700`} />
            
            <div className="flex items-start justify-between mb-4 relative z-10">
              <div className={`p-2.5 rounded-xl backdrop-blur-md border ${m.border} ${m.bg} shadow-inner group-hover:scale-110 transition-transform`}>
                <m.icon className={`w-5 h-5 ${m.color}`} />
              </div>
              {m.label === 'IA Brain Capacity' && (
                <div className="flex gap-0.5">
                  {[1,2,3,4,5].map(dot => (
                    <div key={dot} className={`w-1 h-3 rounded-full ${dot <= 3 ? 'bg-fuchsia-500' : 'bg-white/10'}`} />
                  ))}
                </div>
              )}
            </div>
            
            <div className="relative z-10">
              <div className="flex items-baseline gap-1">
                <p className="text-3xl font-bold text-white tracking-tight">{m.value}</p>
                {m.label === 'Latencia de Ingesta' && <span className="text-xs text-cyan-400/60 font-medium">avg</span>}
              </div>
              <p className="text-sm font-medium text-gray-500 mt-1">{m.sub}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Premium Source Mix Banner */}
      <div className="bg-gradient-to-r from-indigo-600/10 via-purple-600/10 to-transparent border border-indigo-500/20 rounded-2xl p-4 flex flex-col md:flex-row items-center justify-between gap-4 backdrop-blur-sm">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30">
            <RefreshCw className="w-6 h-6 text-indigo-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Mezcla de Fuentes de Datos</h3>
            <p className="text-xs text-indigo-300/60">Proporción de datos estáticos vs conexiones en vivo</p>
          </div>
        </div>
        
        <div className="flex-1 max-w-md w-full px-4">
          <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden flex">
            <div 
              className="h-full bg-indigo-500 shadow-[0_0_10px_rgba(99,102,241,0.5)] transition-all duration-1000" 
              style={{ width: `${(data?.static_sources || 0) / ((data?.total_sources || 1)) * 100}%` }} 
            />
            <div 
              className="h-full bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.5)] transition-all duration-1000" 
              style={{ width: `${(data?.dynamic_sources || 0) / ((data?.total_sources || 1)) * 100}%` }} 
            />
          </div>
          <div className="flex justify-between mt-2">
            <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-tighter">Estáticos ({data?.static_sources || 0})</span>
            <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-tighter">Dinámicos ({data?.dynamic_sources || 0})</span>
          </div>
        </div>

        <div className="hidden lg:block text-right">
          <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Estado del RAG</p>
          <p className="text-xs font-medium text-emerald-400">Optimizado & Listo</p>
        </div>
      </div>
    </div>
  );
}
