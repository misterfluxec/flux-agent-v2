'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { 
  TrendingUp, Users, ShoppingCart, DollarSign, 
  Zap, BarChart3, PieChart, Calendar, 
  ArrowUpRight, ArrowDownRight, Target, 
  ChevronRight, Download, Share2, Shield
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { fetchAnalyticsOverview, AnalyticsOverview } from '@/lib/api/analytics';
import { KPICardSkeleton, ConversationsKPI, LeadsKPI, ConversionRateKPI, SentimentKPI } from '@/components/ui/kpi-card';
import { Button } from '@/components/ui/button';
import { useEventBus } from '@/providers/EventBusProvider';
import { useEffect, useState as useReactState } from 'react';
import { SystemObservability } from './components/SystemObservability';

type TabType = 'overview' | 'sales' | 'ops' | 'system';

// Datos iniciales en caso de fallo de red
const INITIAL_ANALYTICS: AnalyticsOverview = {
  total_conversations: 1240,
  total_messages: 8934,
  total_sales: 94,
  conversion_rate: 7.6,
  avg_response_time: 1.2,
  sentiment_score: 0.85
};

export default function AnalyticsPage() {
  const t = useTranslations('analytics');
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  const { data: serverAnalytics, isLoading } = useQuery<AnalyticsOverview, Error>({
    queryKey: ['analytics-overview'],
    queryFn: () => fetchAnalyticsOverview(),
    staleTime: 60000,
    refetchInterval: 60000,
    initialData: INITIAL_ANALYTICS, // Fallback para MVP
  });

  const { subscribe } = useEventBus();
  const [analytics, setAnalytics] = useReactState<AnalyticsOverview>(INITIAL_ANALYTICS);

  useEffect(() => {
    if (serverAnalytics) {
      setAnalytics(serverAnalytics);
    }
  }, [serverAnalytics]);

  useEffect(() => {
    // Escuchar eventos en tiempo real para actualizar contadores
    const unsubscribe = subscribe(["ORCHESTRATOR_STEP_COMPLETED", "BILLING_ALERT"], (msg) => {
      setAnalytics(prev => {
        if (msg.type === "ORCHESTRATOR_STEP_COMPLETED") {
           return { ...prev, total_messages: prev.total_messages + 1 };
        }
        if (msg.type === "BILLING_ALERT") {
           // En un caso real podríamos tener un KPI de tokens. Por ahora, asumimos que un lead se completó.
           return { ...prev, total_conversations: prev.total_conversations + 1 };
        }
        return prev;
      });
    });
    return () => unsubscribe();
  }, [subscribe]);

  if (isLoading) {
    return (
      <div className="space-y-8 max-w-6xl mx-auto pb-20">
        <div className="flex flex-col md:flex-row items-start md:items-end justify-between gap-4">
          <div className="animate-pulse">
            <div className="h-10 w-48 bg-white/5 rounded-xl mb-2" />
            <div className="h-4 w-96 bg-white/5 rounded-lg" />
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1,2,3,4].map(i => <KPICardSkeleton key={i} />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-20">
      {/* Header with Export */}
      <div className="flex flex-col md:flex-row items-start md:items-end justify-between gap-6">
        <div>
           <h1 className="text-3xl font-black tracking-tight text-white">{t('title')}</h1>
           <p className="text-slate-400 mt-1">Monitorea el rendimiento de tu agente y el ROI de tus campañas en tiempo real.</p>
        </div>
        <div className="flex items-center gap-3 w-full md:w-auto">
          <Button variant="outline" className="flex-1 md:flex-none rounded-xl border-white/5 bg-white/5 text-white hover:bg-white/10 h-12">
            <Download className="w-4 h-4 mr-2" /> Exportar
          </Button>
          <div className="bg-primary/10 border border-primary/20 px-4 py-2 rounded-2xl flex items-center gap-3">
             <Zap className="w-5 h-5 text-primary fill-primary/20" />
             <div>
               <p className="text-[10px] font-black uppercase tracking-[0.15em] text-primary/70 leading-none">Status</p>
               <p className="text-sm font-black text-primary">Live Data</p>
             </div>
          </div>
        </div>
      </div>

      {/* Main Tabs */}
      <div className="flex items-center gap-2 bg-slate-900/50 p-1.5 rounded-2xl border border-white/5 w-fit">
        {[
          { id: 'overview', label: 'Resumen General', icon: BarChart3 },
          { id: 'sales', label: 'Rendimiento de Ventas', icon: TrendingUp },
          { id: 'ops', label: 'Eficiencia Operativa', icon: Zap },
          { id: 'system', label: 'Sistema', icon: Shield },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as TabType)}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm transition-all duration-300 ${
              activeTab === tab.id 
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/15' 
                : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>
      
      {activeTab === 'overview' && (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-500">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <ConversationsKPI value={analytics?.total_conversations || 0} />
            <LeadsKPI value={analytics?.total_messages || 0} />
            <ConversionRateKPI value={analytics?.conversion_rate || 0} />
            <SentimentKPI value={analytics?.sentiment_score || 0} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 bg-slate-900/40 backdrop-blur-xl border border-white/5 rounded-[32px] p-8 relative overflow-hidden shadow-2xl">
              <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full -mr-20 -mt-20 blur-3xl pointer-events-none" />
              <h3 className="text-xl font-black text-white mb-8 flex items-center gap-2">
                <Target className="w-6 h-6 text-indigo-500" />
                Embudo de Conversión (Funnels)
              </h3>
              <div className="space-y-8 relative z-10">
                {[
                  { label: 'Visitantes Totales', value: '4,200', color: 'bg-slate-700', width: 'w-full' },
                  { label: 'Conversaciones Iniciadas', value: '1,240', color: 'bg-indigo-600', width: 'w-[29.5%]', highlight: true },
                  { label: 'Ventas Cerradas', value: '94', color: 'bg-emerald-500', width: 'w-[7.6%]' },
                ].map((item, i) => (
                  <div key={i} className={`flex flex-col gap-2 ${i > 0 ? 'ml-' + (i * 4) : ''}`}>
                    <div className="flex justify-between items-end">
                      <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{item.label}</span>
                      <span className={`text-sm font-black ${item.highlight ? 'text-indigo-400' : 'text-white'}`}>{item.value}</span>
                    </div>
                    <div className="h-4 bg-white/5 rounded-full overflow-hidden border border-white/5">
                      <div className={`h-full ${item.width} ${item.color} rounded-full transition-all duration-1000 ${item.highlight ? 'shadow-[0_0_20px_rgba(79,70,229,0.4)]' : ''}`} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-gradient-to-br from-indigo-600 to-blue-700 rounded-[32px] p-8 text-white flex flex-col justify-between shadow-2xl shadow-indigo-500/20 group hover:scale-[1.02] transition-all duration-500">
               <div className="space-y-6">
                  <div className="w-14 h-14 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur-md group-hover:rotate-12 transition-transform">
                     <TrendingUp className="w-7 h-7" />
                  </div>
                  <div>
                    <h4 className="text-2xl font-black leading-tight">Crecimiento este mes</h4>
                    <p className="text-white/70 text-sm mt-4 leading-relaxed font-medium">
                      Tu agente ha procesado un <b className="text-white text-lg">24%</b> más de leads que el mes pasado, reduciendo el costo por adquisición en un <b className="text-white text-lg">15%</b>.
                    </p>
                  </div>
               </div>
               <Button className="w-full h-14 bg-white text-indigo-600 rounded-2xl font-black text-sm shadow-xl hover:bg-white/90 transition-all active:scale-95 mt-10">
                 Ver Insight Detallado
               </Button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'sales' && (
        <div className="bg-slate-900/40 backdrop-blur-xl border border-white/5 rounded-[32px] p-12 shadow-2xl flex flex-col items-center justify-center text-center animate-in fade-in slide-in-from-bottom-2 duration-500">
          <div className="w-20 h-20 rounded-3xl bg-indigo-500/10 flex items-center justify-center mb-6">
            <PieChart className="w-10 h-10 text-indigo-400" />
          </div>
          <h3 className="text-2xl font-black text-white">Próximamente: Análisis de Ingresos</h3>
          <p className="text-slate-500 mt-2 max-w-md font-medium">
            Estamos terminando de procesar tus datos de facturación para mostrarte el ROI detallado y proyecciones de venta para el próximo trimestre.
          </p>
        </div>
      )}

      {activeTab === 'ops' && (
        <div className="bg-slate-900/40 backdrop-blur-xl border border-white/5 rounded-[32px] p-12 shadow-2xl flex flex-col items-center justify-center text-center animate-in fade-in slide-in-from-bottom-2 duration-500">
          <div className="w-20 h-20 rounded-3xl bg-emerald-500/10 flex items-center justify-center mb-6">
            <Zap className="w-10 h-10 text-emerald-400" />
          </div>
          <h3 className="text-2xl font-black text-white">Eficiencia del Agente</h3>
          <p className="text-slate-500 mt-2 max-w-md font-medium">
            Aquí podrás ver el tiempo de respuesta promedio, satisfacción del cliente y tasa de resolución automática.
          </p>
        </div>
      )}

      {activeTab === 'system' && <SystemObservability />}
    </div>
  );
}
