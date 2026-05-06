import { useIngestionStats } from '../hooks/useIngestionStats';
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

  const staticCount = data?.static_sources ?? 0;
  const dynamicCount = data?.dynamic_sources ?? 0;
  const totalSources = staticCount + dynamicCount;

  const staticPercentage = totalSources > 0 ? (staticCount / totalSources) * 100 : 0;
  const dynamicPercentage = totalSources > 0 ? (dynamicCount / totalSources) * 100 : 0;

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
      value: `${((data?.total_tokens ?? 0) / 1000).toFixed(1)}K`, 
      sub: `${data?.total_chunks ?? 0} fragmentos indexados`, 
      icon: Brain, 
      color: 'text-fuchsia-400', 
      bg: 'bg-fuchsia-500/10', 
      border: 'border-fuchsia-500/20',
      gradient: 'from-fuchsia-500/20 to-transparent'
    },
    { 
      label: 'Catálogo Activo', 
      value: data?.active_products ?? 0, 
      sub: 'productos/servicios en RAG', 
      icon: Database, 
      color: 'text-indigo-400', 
      bg: 'bg-indigo-500/10', 
      border: 'border-indigo-500/20',
      gradient: 'from-indigo-500/20 to-transparent'
    },
    { 
      label: 'Salud de Sincronización', 
      value: `${data?.success_rate ?? 0}%`, 
      sub: `${data?.active_sources ?? 0} fuentes activas`, 
      icon: Activity, 
      color: 'text-emerald-400', 
      bg: 'bg-emerald-500/10', 
      border: 'border-emerald-500/20',
      gradient: 'from-emerald-500/20 to-transparent'
    },
    { 
      label: 'Último Entrenamiento', 
      value: formatTimeAgo(data?.last_sync_at ?? null), 
      sub: `${data?.avg_index_time_seconds ?? 0}s promedio/carga`, 
      icon: Clock, 
      color: 'text-amber-400', 
      bg: 'bg-amber-500/10', 
      border: 'border-amber-500/20',
      gradient: 'from-amber-500/20 to-transparent'
    }
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric, index) => (
          <div 
            key={index}
            className={`relative group overflow-hidden bg-gray-900/40 backdrop-blur-md rounded-2xl border ${metric.border} p-5 transition-all hover:scale-[1.02] hover:bg-gray-900/60`}
          >
            <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${metric.gradient} blur-3xl -mr-16 -mt-16 opacity-50`} />
            
            <div className="flex items-start justify-between">
              <div className={`p-3 rounded-xl ${metric.bg} border ${metric.border}`}>
                <metric.icon className={`w-6 h-6 ${metric.color}`} />
              </div>
            </div>

            <div className="mt-4">
              <p className="text-sm font-medium text-gray-400">{metric.label}</p>
              <h3 className={`text-2xl font-bold mt-1 ${metric.color}`}>{metric.value}</h3>
              <p className="text-xs text-gray-500 mt-1">{metric.sub}</p>
            </div>
          </div>
        ))}
      </div>

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
              style={{ width: `${staticPercentage}%` }} 
            />
            <div 
              className="h-full bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.5)] transition-all duration-1000" 
              style={{ width: `${dynamicPercentage}%` }} 
            />
          </div>
          <div className="flex justify-between mt-2">
            <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-tighter">Estáticos ({staticCount})</span>
            <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-tighter">Dinámicos ({dynamicCount})</span>
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
