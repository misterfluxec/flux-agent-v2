'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  MessageSquare, Zap, Bot, ArrowUpRight, ShieldCheck, 
  Wifi, Activity, AlertCircle, Circle, Command, PhoneOff, CheckCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useEventBus } from '@/providers/EventBusProvider';
import { OnboardingWizard } from '@/components/system/OnboardingWizard';
import { RecommendationFeed } from '@/components/insights/RecommendationFeed';
import { useActivationMoments } from '@/hooks/useActivationMoments';
import { FLUX_LEXICON } from '@/constants/lexicon';
import { useOperationsTimeline } from '@/hooks/useOperationsTimeline';
import { useOperationsHealth } from '@/hooks/useOperationsHealth';
import { TimelineEvent } from '@/types/operations';
import { dashboardApi, DashboardKPIs } from '@/services/api/dashboard';

export default function DashboardPage() {
  const router = useRouter();
  const [isHydrated, setIsHydrated] = useState(false);
  const [overview, setOverview] = useState<DashboardKPIs | null>(null);
  
  const { isConnected } = useEventBus();
  
  // Activar micro-victorias en background (sin render visible)
  useActivationMoments();
  
  // Feed operacional unificado
  const { events: timelineEvents, isLoading: isTimelineLoading } = useOperationsTimeline({
    limit: 10,
    realtime: true
  });

  // Estado de salud operacional
  const { report: healthReport } = useOperationsHealth();

  useEffect(() => {
    setIsHydrated(true);
    dashboardApi.getOverview()
      .then(setOverview)
      .catch((err) => console.error("Error cargando overview:", err));
  }, []);

  if (!isHydrated) return null; // Zero-spinner rule (Progressive Hydration)

  // Derive critical count from health report or fallback
  const criticalCount = healthReport?.critical_count || 0;

  return (
    <div className="space-y-5 animate-in fade-in duration-500 pb-12 px-6 md:px-8 max-w-6xl mx-auto pt-6">
      
      {/* ONBOARDING — First Victory Wizard */}
      <OnboardingWizard />

      {/* RECOMMENDATIONS — Decision Center */}
      <RecommendationFeed />

      {/* HEADER + KPIs DEL DÍA */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-5 relative mb-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold tracking-tight text-white/80">Buenos días, Admin · Empresa S.A.</h1>
            <div 
              onClick={() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))}
              className="px-2.5 py-1 rounded-md bg-white/[0.04] border border-white/[0.07] text-[11px] text-slate-500 font-medium flex items-center gap-1.5 cursor-pointer hover:bg-white/[0.07] transition-colors"
            >
              <Command className="w-3 h-3" /> K
            </div>
          </div>
          <p className="text-slate-500 text-[13px] leading-relaxed">Pulso del sistema en vivo. Toma decisiones con contexto.</p>
        </div>
        <Button onClick={() => router.push('/dashboard/operations?action=new_chat')} className="bg-cyan-500 hover:bg-cyan-600 text-white shadow-[0_0_15px_rgba(6,182,212,0.4)] transition-all">
          + Nuevo Chat
        </Button>
      </div>

      {/* 4 KPIs CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-[#111827] border border-white/5 rounded-2xl p-5 shadow-lg relative overflow-hidden group hover:border-white/10 transition-colors cursor-pointer" onClick={() => router.push('/dashboard/operations')}>
          <p className="text-[12px] font-medium text-slate-400 mb-2">Conversaciones</p>
          <h2 className="text-2xl font-black text-white/90 tabular-nums">{overview?.kpis.total_conversaciones ?? '...'}</h2>
          <span className="text-[12px] font-medium text-emerald-400 mt-1 flex items-center">
            <ArrowUpRight className="w-3 h-3 mr-1" /> +0% vs ayer
          </span>
        </div>
        
        <div className="bg-[#111827] border border-white/5 rounded-2xl p-5 shadow-lg relative overflow-hidden group hover:border-white/10 transition-colors cursor-pointer" onClick={() => router.push('/dashboard/crm')}>
          <p className="text-[12px] font-medium text-slate-400 mb-2">Leads Capturados</p>
          <h2 className="text-2xl font-black text-white/90 tabular-nums">{overview?.kpis.leads_capturados ?? '...'}</h2>
          <span className="text-[12px] font-medium text-emerald-400 mt-1 flex items-center">
            <ArrowUpRight className="w-3 h-3 mr-1" /> +0 vs ayer
          </span>
        </div>
        
        <div className="bg-[#111827] border border-white/5 rounded-2xl p-5 shadow-lg relative overflow-hidden group hover:border-white/10 transition-colors cursor-pointer" onClick={() => router.push('/dashboard/analytics')}>
          <p className="text-[12px] font-medium text-slate-400 mb-2">Satisfacción</p>
          <h2 className="text-2xl font-black text-white/90 tabular-nums flex items-center gap-2">
            {overview ? `${Math.round(overview.kpis.sentimiento_promedio * 100)}%` : '...'} <span className="text-lg">😊</span>
          </h2>
          <span className="text-[12px] font-medium text-slate-500 mt-1 flex items-center">
            Sentimiento de usuarios
          </span>
        </div>

        <div className="bg-[#111827] border border-white/5 rounded-2xl p-5 shadow-lg relative overflow-hidden group hover:border-white/10 transition-colors cursor-pointer" onClick={() => router.push('/dashboard/orders')}>
          <p className="text-[12px] font-bold text-slate-400 mb-2">Tokens Usados</p>
          <h2 className="text-2xl font-black text-white/90 tabular-nums">{overview?.kpis.uso_tokens ?? '...'}</h2>
          <span className="text-[12px] font-medium text-slate-400 mt-1 flex items-center">
            Este mes
          </span>
          <div className="w-full bg-white/5 h-1.5 rounded-full mt-2">
            <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: '15%' }}></div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* MAIN COLUMN (8 cols) */}
        <div className="lg:col-span-8 space-y-6">

          {/* RENDIMIENTO DE AGENTES Y ALERTAS */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className={`bg-${criticalCount > 0 ? 'red' : 'amber'}-500/[0.04] border border-${criticalCount > 0 ? 'red-500/[0.12]' : 'amber-500/[0.12]'} rounded-xl p-4 cursor-pointer`} onClick={() => router.push('/dashboard/operations')}>
              <h3 className="text-sm font-semibold text-white/80 flex items-center gap-2 mb-3">
                <AlertCircle className={`w-4 h-4 ${criticalCount > 0 ? 'text-red-400' : 'text-amber-400'}`} />
                Alertas Prioritarias
              </h3>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2 text-red-300/90">
                   <span className="mt-0.5">⚠️</span> 3 leads sin atender hace &gt; 30 min
                </li>
                <li className="flex items-start gap-2 text-amber-300/90">
                   <span className="mt-0.5">⚠️</span> Cuota de LLM al 80%
                </li>
                <li className="flex items-start gap-2 text-emerald-300/90">
                   <span className="mt-0.5">💡</span> Oportunidad: 5 cotizaciones vistas hoy
                </li>
              </ul>
            </div>

            <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-white/80 flex items-center gap-2 mb-3">
                <Bot className="w-4 h-4 text-primary" />
                Rendimiento de Agentes
              </h3>
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-white/5 rounded-lg p-2 flex justify-between items-center cursor-pointer hover:bg-white/10" onClick={() => router.push('/dashboard/agents')}>
                  <span className="text-xs text-white/80">Sales Bot</span>
                  <span className="text-xs font-bold text-emerald-400">156 🟢</span>
                </div>
                <div className="bg-white/5 rounded-lg p-2 flex justify-between items-center cursor-pointer hover:bg-white/10" onClick={() => router.push('/dashboard/agents')}>
                  <span className="text-xs text-white/80">Support</span>
                  <span className="text-xs font-bold text-emerald-400">89 🟢</span>
                </div>
                <div className="bg-white/5 rounded-lg p-2 flex justify-between items-center cursor-pointer hover:bg-white/10" onClick={() => router.push('/dashboard/agents')}>
                  <span className="text-xs text-white/80">Ops Bot</span>
                  <span className="text-xs font-bold text-amber-400">45 🟡</span>
                </div>
                <div className="bg-white/5 rounded-lg p-2 flex justify-between items-center cursor-pointer hover:bg-white/10" onClick={() => router.push('/dashboard/agents')}>
                  <span className="text-xs text-white/80">Yanua</span>
                  <span className="text-xs font-bold text-red-400">12 🔴</span>
                </div>
              </div>
            </div>
          </div>

          {/* LIVE INSIGHTS FEED */}
          <div className="bg-[#111827] border border-white/5 rounded-2xl overflow-hidden shadow-lg">
            <div className="px-6 py-4 border-b border-white/5 flex justify-between items-center">
              <h3 className="text-sm font-semibold text-white/80 flex items-center gap-2">
                <Activity className="w-4 h-4 text-primary" />
                Live Action Feed
              </h3>
              <span className="text-[10px] uppercase font-bold text-emerald-500 tracking-wider bg-emerald-500/10 px-2 py-1 rounded">Live</span>
            </div>
            <div className="p-4 space-y-1">
              {isTimelineLoading ? (
                <div className="p-8 text-center text-white/30 text-sm">Escuchando eventos en tiempo real...</div>
              ) : timelineEvents.length === 0 ? (
                <div className="p-8 text-center text-white/30 text-sm">No hay eventos recientes.</div>
              ) : (
                timelineEvents.slice(0, 8).map((event: TimelineEvent) => {
                  const time = new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                  return (
                  <div key={event.id} className="flex gap-4 p-3 rounded-lg hover:bg-white/[0.02] transition-colors group">
                    <div className="pt-0.5">
                      {event.category === "ops" && <AlertCircle className="w-4 h-4 text-amber-400" />}
                      {event.category === "billing" && <ShieldCheck className="w-4 h-4 text-purple-400" />}
                      {event.category === "commerce" && <Activity className="w-4 h-4 text-emerald-400" />}
                      {event.category === "interaction" && <MessageSquare className="w-4 h-4 text-blue-400" />}
                      {event.category === "automation" && <Bot className="w-4 h-4 text-primary" />}
                      {event.category === "system" && <Wifi className="w-4 h-4 text-slate-500" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white/80 truncate">{event.summary}</p>
                      <p className="text-xs text-white/40 mt-1">{time}</p>
                    </div>
                    <Button size="sm" variant="outline" className="opacity-0 group-hover:opacity-100 h-7 text-xs bg-transparent border-white/10 hover:bg-white/10" onClick={() => router.push(`/dashboard/operations?event=${event.id}`)}>
                      Ver Detalles
                    </Button>
                  </div>
                )})
              )}
            </div>
            <div className="p-3 border-t border-white/5 text-center">
               <Button variant="ghost" className="w-full text-xs text-slate-400 hover:text-white" onClick={() => router.push('/dashboard/operations')}>
                 Ver Timeline Completo →
               </Button>
            </div>
          </div>

        </div>

        {/* RIGHT COLUMN (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* TOKEN ECONOMY WIDGET */}
          <div className="bg-[#111827] border border-white/5 rounded-2xl p-6 shadow-lg">
            <h3 className="text-sm font-semibold text-white/80 mb-4 flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" />
              Economía de Tokens
            </h3>
            
            <div className="relative h-32 flex items-center justify-center mb-4">
              {/* Fake Donut Chart */}
              <svg viewBox="0 0 36 36" className="w-32 h-32 transform -rotate-90">
                <path
                  className="text-white/5"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="3"
                />
                <path
                  className="text-primary transition-all duration-1000 ease-out"
                  strokeDasharray="78, 100"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="3"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-2xl font-black text-white">78%</span>
                <span className="text-[10px] text-white/40 uppercase font-semibold">Usado</span>
              </div>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between text-xs">
                <span className="text-white/50">Límite Pro</span>
                <span className="text-white/90 font-medium">1,000,000</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-white/50">Consumidos</span>
                <span className="text-white/90 font-medium">780,450</span>
              </div>
              <div className="pt-2 border-t border-white/5">
                <p className="text-[11px] text-amber-400/80 mt-1 leading-tight">
                  Alerta: Al 80% te notificaremos. Si llegas al 100% se activará el Kill-Switch si no hay overage.
                </p>
              </div>
            </div>
          </div>

          {/* POLICY ENGINE SHIELD */}
          <div className="bg-gradient-to-br from-purple-500/10 to-[#111827] border border-purple-500/20 rounded-2xl p-6 shadow-lg">
            <h3 className="text-sm font-semibold text-white/80 mb-2 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-purple-400" />
              Escudo Activo
            </h3>
            <p className="text-3xl font-black text-white mb-1">14</p>
            <p className="text-xs text-purple-200/50">Acciones riesgosas bloqueadas por políticas hoy.</p>
          </div>

        </div>
      </div>
    </div>
  );
}
