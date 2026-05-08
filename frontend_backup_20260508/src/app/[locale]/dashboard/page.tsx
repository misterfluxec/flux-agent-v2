'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  MessageSquare, Zap, Bot, ArrowUpRight, ShieldCheck, 
  Wifi, Activity, AlertCircle, Circle, Command, PhoneOff
} from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function DashboardPage() {
  const router = useRouter();
  const [isHydrated, setIsHydrated] = useState(false);
  
  // Mocking Live Data
  const [feed, setFeed] = useState([
    { id: 1, type: "insight", text: "Cliente VIP 'Mister' esperando respuesta rápida.", time: "Hace 1m" },
    { id: 2, type: "system", text: "WhatsApp Cloud API conectada.", time: "Hace 3m" },
    { id: 3, type: "policy", text: "Policy Engine bloqueó un descuento mayor al 20%.", time: "Hace 12m" }
  ]);

  useEffect(() => {
    setIsHydrated(true);
    // Simular eventos live (EventBus)
    const timer = setInterval(() => {
      setFeed(prev => [
        { id: Date.now(), type: "action", text: "Yanua resolvió una consulta de horarios.", time: "Ahora" },
        ...prev.slice(0, 4)
      ]);
    }, 15000);
    return () => clearInterval(timer);
  }, []);

  if (!isHydrated) return null; // Zero-spinner rule (Progressive Hydration)

  return (
    <div className="space-y-6 animate-in fade-in duration-700 pb-12 px-4 md:px-8 max-w-7xl mx-auto pt-8">
      
      {/* HEADER + NORTH STAR */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 relative mb-8">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-3xl font-black tracking-tight text-white/90">Torre de Control</h1>
            <div 
              onClick={() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))}
              className="px-2.5 py-1 rounded-md bg-white/5 border border-white/10 text-xs text-white/50 font-medium flex items-center gap-1.5 cursor-pointer hover:bg-white/10 transition-colors"
            >
              <Command className="w-3 h-3" /> K
            </div>
          </div>
          <p className="text-white/50 text-sm">Resumen ejecutivo y pulso del sistema en vivo.</p>
        </div>
        
        {/* NORTH-STAR METRIC */}
        <div className="bg-primary/10 border border-primary/20 rounded-2xl p-4 pr-12 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary/20 blur-3xl -mr-10 -mt-10"></div>
          <p className="text-xs font-semibold text-primary/80 uppercase tracking-wider mb-1">Valor Potencial Hoy</p>
          <div className="flex items-end gap-3">
            <h2 className="text-3xl font-black text-white">$2,430</h2>
            <span className="text-sm font-medium text-emerald-400 flex items-center mb-1">
              <ArrowUpRight className="w-4 h-4 mr-0.5" /> 18%
            </span>
          </div>
          <p className="text-xs text-white/50 mt-2">Basado en <span className="text-white/80 font-medium">3 leads calientes</span> en curso.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* MAIN COLUMN (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          
          {/* SEMÁFORO DE ESTADO (System Traffic Light) */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-[#111827] border border-white/5 rounded-xl p-4 flex items-center gap-4">
              <div className="relative">
                <div className="w-3 h-3 rounded-full bg-emerald-500 z-10 relative"></div>
                <div className="w-3 h-3 rounded-full bg-emerald-500 absolute inset-0 animate-ping opacity-50"></div>
              </div>
              <div>
                <p className="text-xs text-white/50 font-medium">Orquestador</p>
                <p className="text-sm text-white/90 font-semibold">Operativo</p>
              </div>
            </div>
            
            <div className="bg-[#111827] border border-white/5 rounded-xl p-4 flex items-center gap-4">
              <div className="relative">
                <div className="w-3 h-3 rounded-full bg-emerald-500 z-10 relative"></div>
              </div>
              <div>
                <p className="text-xs text-white/50 font-medium">WhatsApp</p>
                <p className="text-sm text-white/90 font-semibold">Conectado</p>
              </div>
            </div>
            
            <div className="bg-red-500/5 border border-red-500/10 rounded-xl p-4 flex items-center gap-4 cursor-pointer hover:bg-red-500/10 transition-colors" onClick={() => router.push('/dashboard/conversations')}>
              <div className="relative">
                <div className="w-3 h-3 rounded-full bg-red-500 z-10 relative"></div>
                <div className="w-3 h-3 rounded-full bg-red-500 absolute inset-0 animate-ping opacity-50"></div>
              </div>
              <div>
                <p className="text-xs text-white/50 font-medium">Handoffs</p>
                <p className="text-sm text-red-400 font-bold">2 Esperando</p>
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
              {feed.map((item) => (
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
                      Intervenir
                    </Button>
                  )}
                </div>
              ))}
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
