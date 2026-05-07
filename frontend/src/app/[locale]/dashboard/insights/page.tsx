'use client';
import { useTranslations } from 'next-intl';
import { InsightCard } from '@/components/insights/InsightCard';
import { MOCK_INSIGHTS } from '@/types/insights';
import { Download, RefreshCw, Filter, BrainCircuit, Activity, BarChart3 } from 'lucide-react';

export default function InsightsPage() {
  const t = useTranslations('insights');

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="p-1.5 bg-primary/10 rounded-lg">
              <BrainCircuit className="w-5 h-5 text-primary" />
            </div>
            <h1 className="text-3xl font-black tracking-tight">{t('title')}</h1>
          </div>
          <p className="text-muted-foreground font-medium text-sm">{t('subtitle')}</p>
        </div>
        <div className="flex gap-3 w-full md:w-auto">
          <button className="flex-1 md:flex-none flex items-center justify-center gap-2 px-6 py-2.5 border border-border rounded-xl text-xs font-black uppercase tracking-widest hover:bg-accent transition-all active:scale-95">
            <Filter className="w-4 h-4" /> {t('filter')}
          </button>
          <button className="flex-1 md:flex-none flex items-center justify-center gap-2 px-6 py-2.5 bg-primary text-primary-foreground rounded-xl text-xs font-black uppercase tracking-widest hover:bg-primary/90 transition-all shadow-md shadow-primary/20 active:scale-95">
            <Download className="w-4 h-4" /> {t('export_report')}
          </button>
        </div>
      </div>

      {/* Grid de Insights */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {MOCK_INSIGHTS.map(insight => (
          <InsightCard key={insight.id} insight={insight} />
        ))}
      </div>

      {/* Sección de Rendimiento del Agente (Yanua) */}
      <div className="bg-card border border-border rounded-3xl p-8 mt-12 relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full -mr-20 -mt-20 blur-3xl group-hover:bg-primary/10 transition-all duration-700" />
        
        <div className="flex items-center justify-between mb-10 relative z-10">
          <h3 className="text-xl font-black flex items-center gap-3">
            <Activity className="w-6 h-6 text-primary" /> 
            {t('agent_performance')}
          </h3>
          <div className="text-[10px] font-black bg-muted px-3 py-1 rounded-full text-muted-foreground uppercase tracking-widest">
            Últimos 30 días
          </div>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-12 relative z-10">
          {[
            { label: 'resolution_rate', value: '94%', color: 'text-foreground', icon: BarChart3 },
            { label: 'avg_response', value: '12s', color: 'text-foreground', icon: RefreshCw },
            { label: 'sentiment_trend', value: '+15%', color: 'text-green-500', icon: Activity },
            { label: 'human_takeovers', value: '3', color: 'text-foreground', icon: BarChart3 },
          ].map((stat, i) => (
            <div key={i} className="flex flex-col items-center lg:items-start space-y-2 group/stat">
              <div className="flex items-center gap-2">
                 <stat.icon className="w-3.5 h-3.5 text-primary opacity-40" />
                 <p className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em]">{t(stat.label as any)}</p>
              </div>
              <p className={`text-4xl font-black ${stat.color} tracking-tighter group-hover/stat:scale-110 transition-transform origin-left`}>{stat.value}</p>
            </div>
          ))}
        </div>

        <div className="mt-12 pt-8 border-t border-border/50 flex flex-col sm:flex-row justify-between items-center gap-4 relative z-10">
           <p className="text-xs text-muted-foreground font-medium italic">
             "Yanua está operando a un 98% de eficiencia optimizando el flujo de ventas."
           </p>
           <button className="text-xs font-black text-primary hover:underline uppercase tracking-widest">
             Ver Auditoría Completa →
           </button>
        </div>
      </div>
    </div>
  );
}
