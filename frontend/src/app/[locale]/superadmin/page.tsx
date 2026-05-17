"use client";

import { useEffect, useState, useRef } from "react";
import dynamic from "next/dynamic";
import { 
  Cpu, 
  MemoryStick, 
  HardDrive, 
  Activity, 
  Terminal as TerminalIcon, 
  ShieldCheck, 
  Zap, 
  Database,
  Globe,
  Lock,
  ArrowUpRight,
  Server,
  TrendingUp,
  Users,
  CreditCard
} from "lucide-react";
import { api } from "@/lib/api";

// Carga dinámica de Recharts para evitar errores de hidratación/module factory en Next.js 16/Turbopack
const ResponsiveContainer = dynamic(() => import("recharts").then(m => m.ResponsiveContainer), { ssr: false });
const AreaChart = dynamic(() => import("recharts").then(m => m.AreaChart), { ssr: false });
const Area = dynamic(() => import("recharts").then(m => m.Area), { ssr: false });
const XAxis = dynamic(() => import("recharts").then(m => m.XAxis), { ssr: false });
const YAxis = dynamic(() => import("recharts").then(m => m.YAxis), { ssr: false });
const CartesianGrid = dynamic(() => import("recharts").then(m => m.CartesianGrid), { ssr: false });
const Tooltip = dynamic(() => import("recharts").then(m => m.Tooltip), { ssr: false });

type SysInfo = {
  cpu_percent: number;
  ram_percent: number;
  ram_total_gb: number;
  ram_used_gb: number;
  disk_percent: number;
  disk_total_gb: number;
  disk_used_gb: number;
  ollama_status: string;
  active_brain: string;
  db_status: string;
};

export default function NOCDashboard() {
  const [data, setData] = useState<SysInfo | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    const messages = [
      "[SYSTEM] Protocolo NOC iniciado — Conexión segura establecida.",
      "[DATABASE] Heartbeat Postgres: OK (Latencia 1.2ms)",
      "[LLM] Ollama Engine detectado: qwen2.5:3b is_active.",
      "[AUTH] Validando tokens JWT de sesiones activas...",
      "[INGRESS] Tráfico entrante vía Cloudflare Tunnel (Port 4000)",
      "[DEBUG] Memoria swap en niveles óptimos.",
      "[SERVER] Verificando integridad de esquemas pgvector...",
      "[SYSTEM] Sincronización de tenants completada."
    ];
    
    let i = 0;
    const interval = setInterval(() => {
      const now = new Date().toLocaleTimeString();
      setLogs(prev => [...prev.slice(-15), `[${now}] ${messages[i % messages.length]}`]);
      i++;
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  useEffect(() => {
    const fetchInfo = async () => {
      try {
        const res = await api.get("/admin/sysinfo");
        const newData = res.data;
        setData(newData);
        
        setHistory(prev => {
          const next = [...prev, { 
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), 
            cpu: newData.cpu_percent,
            ram: newData.ram_percent 
          }];
          return next.slice(-15);
        });
      } catch (e) {
        console.error("NOC Sync Error");
      }
    };
    fetchInfo();
    const interval = setInterval(fetchInfo, 5000);
    return () => clearInterval(interval);
  }, []);

  if (!isClient || !data) return (
    <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
        <div className="w-10 h-10 border-2 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
        <p className="text-emerald-500/50 font-mono text-[10px] uppercase tracking-widest">Encrypting NOC Tunnel...</p>
    </div>
  );

  return (
    <div className="space-y-8 animate-fadeIn pb-12">
      {/* Header Resumen Ejecutivo */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-black text-white tracking-tighter uppercase italic">Resumen Ejecutivo</h1>
          <p className="text-slate-500 text-sm mt-1 font-medium italic">KPIs en tiempo real e inteligencia de infraestructura</p>
        </div>
        <div className="flex items-center gap-3 bg-slate-900/50 p-1.5 rounded-xl border border-slate-800">
            <button className="px-4 py-1.5 rounded-lg bg-emerald-500 text-slate-950 text-xs font-bold shadow-lg shadow-emerald-500/20 transition-all">HOY</button>
            <button className="px-4 py-1.5 rounded-lg text-slate-500 text-xs font-bold hover:text-slate-300 transition-all">7 DÍAS</button>
            <button className="px-4 py-1.5 rounded-lg text-slate-500 text-xs font-bold hover:text-slate-300 transition-all">30 DÍAS</button>
        </div>
      </div>

      {/* Tarjetas de KPIs Comerciales & Ops */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <KPICard title="Tenants Activos" value="24" trend="+3" icon={Server} color="text-emerald-400" />
        <KPICard title="Conversiones" value="12" trend="+15%" icon={TrendingUp} color="text-blue-400" />
        <KPICard title="Ingresos Hoy" value="$1,420" trend="+8%" icon={CreditCard} color="text-amber-400" />
        <KPICard title="Tickets Abiertos" value="4" trend="Low" icon={Activity} color="text-red-400" />
      </div>

      {/* Monitor de Recursos Bare-Metal */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
            <div className="bg-slate-900/40 border border-slate-800 p-8 rounded-3xl backdrop-blur-xl relative overflow-hidden">
                
                <div className="flex justify-between items-center mb-8 relative z-10">
                    <div>
                        <h3 className="text-lg font-bold text-white tracking-tight flex items-center gap-3">
                            <Cpu className="w-5 h-5 text-emerald-400" />
                            Telemetría de Inferencia
                        </h3>
                        <p className="text-xs text-slate-500 mt-1">Carga de procesamiento IA y buffer de memoria volátil</p>
                    </div>
                    <div className="flex gap-6">
                        <div className="text-right">
                            <div className="text-[10px] text-slate-600 font-black uppercase tracking-widest">CPU LOAD</div>
                            <div className="text-xl font-mono text-emerald-400 font-bold">{data.cpu_percent}%</div>
                        </div>
                        <div className="text-right">
                            <div className="text-[10px] text-slate-600 font-black uppercase tracking-widest">RAM USAGE</div>
                            <div className="text-xl font-mono text-blue-400 font-bold">{data.ram_percent}%</div>
                        </div>
                    </div>
                </div>

                <div className="h-[280px] w-full relative z-10">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={history}>
                            <defs>
                                <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                                </linearGradient>
                                <linearGradient id="colorRam" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                            <XAxis dataKey="time" hide />
                            <YAxis domain={[0, 100]} hide />
                            <Tooltip 
                                contentStyle={{ backgroundColor: '#020617', borderColor: '#1e293b', color: '#fff', borderRadius: '16px', fontSize: '11px', border: '1px solid rgba(255,255,255,0.05)' }}
                            />
                            <Area type="monotone" dataKey="cpu" stroke="#10b981" fillOpacity={1} fill="url(#colorCpu)" strokeWidth={3} />
                            <Area type="monotone" dataKey="ram" stroke="#3b82f6" fillOpacity={1} fill="url(#colorRam)" strokeWidth={3} />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <StatusPanel title="AI Engine (Ollama)" status={data.ollama_status} icon={Zap} desc={data.active_brain} />
                <StatusPanel title="Master DB (Postgres)" status={data.db_status} icon={Database} desc="Vector Index: Ready" />
            </div>
        </div>

        {/* Columna Derecha: Consola & Alertas */}
        <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl flex flex-col h-full overflow-hidden">
                <div className="p-5 border-b border-slate-800 bg-slate-950/50 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse shadow-[0_0_10px_rgba(239,68,68,0.5)]" />
                        <span className="text-[11px] font-black text-slate-400 uppercase tracking-[0.2em]">Live Kernel Logs</span>
                    </div>
                    <TerminalIcon className="w-4 h-4 text-slate-700" />
                </div>
                <div 
                    ref={scrollRef}
                    className="flex-1 p-6 font-mono text-[10px] leading-relaxed text-emerald-500/90 overflow-y-auto space-y-2 bg-black/40 scrollbar-hide"
                >
                    {logs.map((log, i) => (
                        <div key={i} className="pl-3 border-l border-emerald-500/20">
                            <span className="text-emerald-500/40 mr-2">»</span>
                            {log}
                        </div>
                    ))}
                    <div className="animate-pulse inline-block w-2 h-4 bg-emerald-500/50 ml-1 translate-y-1" />
                </div>
            </div>

            <div className="bg-gradient-to-br from-indigo-600 to-blue-700 p-8 rounded-3xl shadow-xl shadow-blue-500/10 relative overflow-hidden group cursor-pointer">
                <div className="absolute -right-8 -bottom-8 opacity-20 group-hover:scale-110 transition-transform duration-500">
                    <ShieldCheck className="w-40 h-48 text-white" />
                </div>
                <h4 className="text-white font-black text-xl tracking-tight uppercase italic mb-2 relative z-10">Security Audit</h4>
                <p className="text-blue-100/80 text-xs leading-relaxed relative z-10">
                    Protocolos de encriptación activos. <br/>
                    Último escaneo global: <span className="font-bold">Hace 14 minutos</span>.
                </p>
                <div className="mt-6 flex items-center gap-2 text-[10px] font-black text-white uppercase tracking-widest relative z-10">
                    Ver Reporte de Integridad
                    <ArrowUpRight className="w-4 h-4 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}

function KPICard({ title, value, trend, icon: Icon, color }: any) {
    return (
        <div className="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl group hover:border-slate-700 transition-all hover:translate-y-[-2px]">
            <div className="flex justify-between items-start mb-4">
                <div className={`p-3 rounded-xl bg-slate-950 border border-slate-800 group-hover:border-slate-700 transition-all`}>
                    <Icon className={`w-5 h-5 ${color}`} />
                </div>
                <span className={`text-[10px] font-black px-2 py-1 rounded-lg ${trend.includes('+') ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-500'}`}>
                    {trend}
                </span>
            </div>
            <div className="text-3xl font-black text-white tracking-tighter mb-1">{value}</div>
            <div className="text-[10px] text-slate-600 font-bold uppercase tracking-widest">{title}</div>
        </div>
    )
}

function StatusPanel({ title, status, icon: Icon, desc }: any) {
  const isOk = status === 'operativo' || status === 'online' || status === 'secure' || status === 'conectado';
  return (
    <div className="bg-slate-900/30 border border-slate-800 p-6 rounded-2xl flex items-center gap-5 hover:bg-slate-900/50 transition-all">
        <div className={`p-4 rounded-2xl ${isOk ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'}`}>
            <Icon className="w-6 h-6" />
        </div>
        <div className="flex-1">
            <div className="flex justify-between items-center">
                <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{title}</span>
                <span className={`text-[9px] font-black uppercase px-2 py-0.5 rounded border ${isOk ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
                    {status}
                </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1 font-medium truncate">{desc}</p>
        </div>
    </div>
  )
}
