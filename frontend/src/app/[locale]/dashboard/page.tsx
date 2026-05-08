'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  MessageSquare, Zap, Bot, ArrowUpRight, ShieldCheck, 
  Wifi, Activity, AlertCircle, Circle, Command, PhoneOff
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useEventBus } from '@/providers/EventBusProvider';
import { OnboardingWizard } from '@/components/system/OnboardingWizard';
import { RecommendationFeed } from '@/components/insights/RecommendationFeed';
import { useActivationMoments } from '@/hooks/useActivationMoments';
import { FLUX_LEXICON } from '@/constants/lexicon';

export default function DashboardPage() {
  const router = useRouter();
  const [isHydrated, setIsHydrated] = useState(false);
  
  const { isConnected, history } = useEventBus();
  
  // Activar micro-victorias en background (sin render visible)
  useActivationMoments();
  
  // Mapeamos el history global del websocket a formato feed de la UI
  const feed = history.map((msg, index) => {
    let text = "Evento desconocido";
    let iconType = "system";
    
    if (msg.type === "SYSTEM_ALERT") { text = msg.data?.message || "Alerta del sistema"; iconType = "insight"; }
    else if (msg.type === "ORCHESTRATOR_STEP") { text = `Orquestador: Fase ${msg.data?.step} completada.`; iconType = "action"; }
    else if (msg.type === "BILLING_ALERT") { text = `Facturación: ${msg.data?.alert_type} - ${msg.data?.resource}`; iconType = "policy"; }
    else if (msg.type === "LEAD_HOT") { text = `¡Lead Caliente Detectado! Score: ${msg.data?.score}`; iconType = "insight"; }
    else if (msg.type === "CONVERSATION_HANDOFF") { text = `Handoff solicitado por agente. Motivo: ${msg.data?.reason}`; iconType = "insight"; }
    else if (msg.type === "VOICE_LIVE_TRANSCRIPT") { text = `Voz: "${msg.data?.text}"`; iconType = "action"; }
    else if (msg.type === "VOICE_INTERRUPTED") { text = "Interrupción de voz detectada."; iconType = "insight"; }

    // Generar tiempo (mockeado rápido para la UI)
    const timeText = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : "Ahora";
    
    return {
      id: msg.event_id || `msg-${index}`,
      type: iconType,
      text: text,
      time: timeText
    };
  });

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  if (!isHydrated) return null; // Zero-spinner rule (Progressive Hydration)

  return (
    <div className="space-y-5 animate-in fade-in duration-500 pb-12 px-6 md:px-8 max-w-6xl mx-auto pt-6">
      
      {/* ONBOARDING — First Victory Wizard */}
      <OnboardingWizard />

      {/* RECOMMENDATIONS — Decision Center */}
      <RecommendationFeed />

      {/* HEADER + NORTH STAR */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-5 relative">
        <div>
          <div className="flex items-center gap-3 mb-1">
            {/* Título: font-bold (no black) para reducir peso visual en lectura continua */}
            <h1 className="text-2xl font-bold tracking-tight text-white/80">{FLUX_LEXICON.HOME}</h1>
            <div 
              onClick={() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))}
              className="px-2.5 py-1 rounded-md bg-white/[0.04] border border-white/[0.07] text-[11px] text-slate-500 font-medium flex items-center gap-1.5 cursor-pointer hover:bg-white/[0.07] transition-colors"
            >
              <Command className="w-3 h-3" /> K
            </div>
          </div>
          <p className="text-slate-500 text-[13px] leading-relaxed">Pulso del sistema en vivo. Toma decisiones con contexto.</p>
        </div>
        
        {/* NORTH-STAR METRIC — sin blur glow masivo (reduce fatiga) */}
        <div className="bg-cyan-500/[0.06] border border-cyan-500/[0.12] rounded-2xl p-4 pr-10 relative overflow-hidden">
          <p className="text-[11px] font-bold text-cyan-400/50 uppercase tracking-widest mb-1">Valor Potencial Hoy</p>
          <div className="flex items-end gap-3">
            <h2 className="text-2xl font-black text-white/80 tabular-nums">$2,430</h2>
            <span className="text-[13px] font-semibold text-emerald-400/80 flex items-center mb-0.5">
              <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" /> 18%
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1.5">Basado en <span className="text-slate-300 font-medium">3 leads calientes</span> en curso.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* MAIN COLUMN (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          
          {/* STATUS CARDS — tamaño y animación calibrados anti-fatiga */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-white/[0.02] border border-white/[0.05] rounded-xl p-3.5 flex items-center gap-3">
              <div className="relative">
                <div className={`w-2.5 h-2.5 rounded-full ${isConnected ? "bg-emerald-500/80" : "bg-amber-500"}`}></div>
                {/* Ping solo cuando NO está conectado (estado anormal) */}
                {!isConnected && <div className="w-2.5 h-2.5 rounded-full bg-amber-500 absolute inset-0 animate-ping opacity-40"></div>}
              </div>
              <div>
                <p className="text-[11px] text-slate-600 font-medium">Event Bus WS</p>
                <p className="text-[13px] text-slate-300 font-semibold">{isConnected ? "Conectado" : "Conectando..."}</p>
              </div>
            </div>
            
            <div className="bg-white/[0.02] border border-white/[0.05] rounded-xl p-3.5 flex items-center gap-3">
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/70"></div>
              <div>
                <p className="text-[11px] text-slate-600 font-medium">WhatsApp</p>
                <p className="text-[13px] text-slate-300 font-semibold">Conectado</p>
              </div>
            </div>
            
            <div className="bg-red-500/[0.04] border border-red-500/[0.12] rounded-xl p-3.5 flex items-center gap-3 cursor-pointer hover:border-red-500/20 transition-colors" onClick={() => router.push('/dashboard/conversations')}>
              <div className="relative">
                <div className="w-2.5 h-2.5 rounded-full bg-red-500 z-10 relative"></div>
                <div className="w-2.5 h-2.5 rounded-full bg-red-500 absolute inset-0 animate-ping opacity-40"></div>
              </div>
              <div>
                <p className="text-[11px] text-slate-600 font-medium">Handoffs</p>
                <p className="text-[13px] text-red-400 font-bold">2 Esperando</p>
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
              {feed.length === 0 ? (
                <div className="p-8 text-center text-white/30 text-sm">Escuchando eventos en tiempo real...</div>
              ) : (
                feed.slice(0, 8).map((item) => (
                  <div key={item.id} className="flex gap-4 p-3 rounded-lg hover:bg-white/[0.02] transition-colors group">
                    <div className="pt-0.5">
                      {item.type === "insight" && <AlertCircle className="w-4 h-4 text-amber-400" />}
                      {item.type === "system" && <Wifi className="w-4 h-4 text-blue-400" />}
                      {item.type === "policy" && <ShieldCheck className="w-4 h-4 text-purple-400" />}
                      {item.type === "action" && <Bot className="w-4 h-4 text-primary" />}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-white/80">{item.text}</p>
                      <p className="text-xs text-white/40 mt-1">{item.time}</p>
                    </div>
                    {item.type === "insight" && (
                      <Button size="sm" variant="outline" className="opacity-0 group-hover:opacity-100 h-7 text-xs bg-transparent border-white/10 hover:bg-white/10" onClick={() => router.push('/dashboard/conversations')}>
                        Ver Detalles
                      </Button>
                    )}
                  </div>
                ))
              )}
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
