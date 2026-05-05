"use client";

import { useEffect, useState, useCallback } from "react";
import {
  RefreshCw, Users, MessageSquare, Cpu,
  AlertTriangle, TrendingUp, Activity, Database, Bot
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

import { Button } from "@/components/ui/button";
import { fetchHealth, fetchStatsOverview, type HealthResponse, type StatsOverviewResponse } from "@/lib/api";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from "recharts";

import HeroNuevoAgente from "./components/HeroNuevoAgente";
import QuickStartModal from "./components/QuickStartModal";

function SkeletonCard() {
  return (
    <Card className="border-slate-200 dark:border-slate-800 shadow-sm h-32">
      <div className="p-5 space-y-4">
        <div className="h-4 w-1/2 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
        <div className="h-8 w-1/3 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
      </div>
    </Card>
  );
}

// ─── KPI Card ─────────────────────────────────────────────────────────────────
interface KpiCardProps {
  title: string;
  value: string | number;
  description: string;
  icon: React.ReactNode;
  trend?: string;
  trendPositive?: boolean;
  delay?: number;
}

function KpiCard({ title, value, description, icon, trend, trendPositive, delay = 0 }: KpiCardProps) {
  return (
    <Card className="animate-entry border-slate-200 dark:border-slate-800 shadow-sm" style={{ animationDelay: `${delay}ms` }}>
      <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-sm font-semibold text-slate-500 dark:text-slate-400">
          {title}
        </CardTitle>
        <div className="p-2 bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 rounded-lg">
          {icon}
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-bold text-slate-900 dark:text-white mb-1">
          {value}
        </p>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          {description}
        </p>
        {trend && (
          <div className="flex items-center mt-3 space-x-1">
            <span className={`text-xs font-bold px-2 py-0.5 rounded-full flex items-center ${trendPositive ? 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' : 'bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400'}`}>
              {trendPositive ? "↑" : "↓"} {trend}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}



// ─── Page ─────────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const [health, setHealth]     = useState<HealthResponse | null>(null);
  const [stats, setStats]       = useState<StatsOverviewResponse | null>(null);
  const [loading, setLoading]   = useState(true);
  const [lastSync, setLastSync] = useState<Date | null>(null);
  
  const [hasAgent, setHasAgent] = useState<boolean>(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [phase, setPhase] = useState(0);

  const loadData = useCallback(async () => {
    if (typeof window === "undefined") return;
    try {
      const agentId = localStorage.getItem("flux_agent_id");
      setHasAgent(!!agentId);
      
      const phaseStr = localStorage.getItem("flux_phase_5");
      setPhase(phaseStr === "true" ? 5 : 0);

      const [hData, sData] = await Promise.all([
        fetchHealth().catch(() => null),
        fetchStatsOverview().catch(() => null)
      ]);
      setHealth(hData);
      setStats(sData);
      setLastSync(new Date());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30_000);
    return () => clearInterval(interval);
  }, [loadData]);

  const services = health?.servicios ?? {};
  const serviceEntries = Object.entries(services);
  const allOnline = serviceEntries.length > 0 && serviceEntries.every(([, v]) =>
    ["ok", "saludable", "conectado", "disponible"].includes(v.estado)
  );

  const estadoIa = loading ? "Cargando..." : allOnline ? "Operativo" : "Degradado";

  const handleOnboardingComplete = () => {
    setIsModalOpen(false);
    setHasAgent(true);
    loadData();
    // Force a reload of the layout or just trigger a storage event
    window.dispatchEvent(new Event('storage'));
  };

  if (!loading && !hasAgent) {
    return (
      <div className="max-w-7xl mx-auto py-8">
        <HeroNuevoAgente onStart={() => setIsModalOpen(true)} />
        <QuickStartModal 
          isOpen={isModalOpen} 
          onClose={() => setIsModalOpen(false)} 
          onComplete={handleOnboardingComplete}
        />
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto">

      {/* ── Page header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-entry">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="flex h-2 w-2 rounded-full bg-indigo-500 animate-pulse" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-indigo-500/80">Monitor Activo</span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Panel de <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-purple-600">Ventas</span>
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-md">
            Seguimiento de rendimiento y salud operativa de tus agentes inteligentes.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-semibold">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Sincronizado
          </div>
          <button
            onClick={() => { setLoading(true); loadData(); }}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2.5 text-sm font-bold text-white bg-slate-900 dark:bg-white dark:text-slate-900 rounded-xl hover:scale-[1.02] active:scale-[0.98] transition-all shadow-lg disabled:opacity-50"
            aria-label="Actualizar datos"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            {loading ? "Sincronizando..." : "Sincronizar"}
          </button>
        </div>
      </div>

      {/* ── System alert ── */}
      {!loading && !allOnline && (
        <div
          className="flex items-center gap-3 px-4 py-3 text-sm animate-entry"
          style={{
            background: "var(--destructive)" + "18",
            border: "1px solid " + "var(--destructive)" + "44",
            color: "var(--destructive)",
          }}
        >
          <AlertTriangle size={16} />
          <span className="font-medium">Servicios degradados detectados.</span>
        </div>
      )}

      {/* ── Acciones Rápidas ── */}
      <div className="flex flex-wrap gap-3 animate-entry delay-100">
        <button className="flex items-center bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-5 rounded-xl transition shadow-sm text-sm">
          <Activity className="w-4 h-4 mr-2" /> Iniciar Agente
        </button>
        <button className="flex items-center bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/50 font-semibold py-2 px-5 rounded-xl transition shadow-sm text-sm">
          <Database className="w-4 h-4 mr-2" /> Reentrenar Modelo
        </button>
        <button className="flex items-center bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-500/20 font-semibold py-2 px-5 rounded-xl transition text-sm">
          Detener
        </button>
      </div>

      <div className="flex items-center justify-between mt-8 mb-4">
        <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">Métricas Clave</h2>
      </div>

      {/* ── KPI Grid — Métricas requeridas ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {loading && !stats ? (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        ) : (
          <>
            <KpiCard
              title="Conversaciones"
              value={stats?.kpis.total_conversaciones ?? 0}
              description="sesiones activas e históricas"
              icon={<MessageSquare size={16} />}
              delay={0}
            />
            <KpiCard
              title="Leads Capturados"
              value={stats?.kpis.leads_capturados ?? 0}
              description="contactos únicos generados"
              icon={<Users size={16} />}
              delay={100}
            />
            <KpiCard
              title="Uso de Tokens"
              value={stats?.kpis.uso_tokens ?? 0}
              description="tokens procesados por la IA"
              icon={<Activity size={16} />}
              delay={200}
            />
            <KpiCard
              title="Estado de IA"
              value={estadoIa}
              description={allOnline ? "Sistemas operativos" : "Verificando latencia..."}
              icon={
                <div className="relative">
                  <Cpu size={16} />
                  {allOnline && <span className="absolute -top-1 -right-1 w-2 h-2 bg-emerald-500 rounded-full animate-ping" />}
                </div>
              }
              trend={allOnline ? "Motor Flux v2.1" : "Revisar servicios"}
              trendPositive={allOnline}
              delay={300}
            />
          </>
        )}
      </div>

      {/* ── Gráficos Recharts ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-entry delay-200">
        <Card className="lg:col-span-2 border-slate-200 dark:border-slate-800 shadow-sm">
          <CardHeader>
            <CardTitle className="text-base font-bold text-slate-800 dark:text-slate-100">Volumen de Mensajes (Últimos 7 Días)</CardTitle>
            <CardDescription className="text-xs text-slate-500 dark:text-slate-400">
              Actividad registrada del tenant
            </CardDescription>
          </CardHeader>
          <CardContent className="h-72">
            {loading && !stats ? (
              <div className="w-full h-full bg-slate-100 dark:bg-slate-800 rounded-xl animate-pulse" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats?.mensajes_por_dia ?? []} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorConteo" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="fecha" stroke="var(--muted-foreground)" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="var(--muted-foreground)" fontSize={12} tickLine={false} axisLine={false} />
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "var(--card)", borderColor: "var(--border)", color: "var(--foreground)", borderRadius: "0.75rem", boxShadow: "var(--shadow-md)" }}
                    itemStyle={{ color: "var(--foreground)" }}
                  />
                  <Area type="monotone" dataKey="conteo" stroke="var(--primary)" fillOpacity={1} fill="url(#colorConteo)" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-200 dark:border-slate-800 shadow-sm">
          <CardHeader>
            <CardTitle className="text-base font-bold text-slate-800 dark:text-slate-100">Análisis de Sentimiento</CardTitle>
            <CardDescription className="text-xs text-slate-500 dark:text-slate-400">
              Métrica promedio: {stats?.kpis.sentimiento_promedio ?? 0}
            </CardDescription>
          </CardHeader>
          <CardContent className="h-72 flex flex-col items-center justify-center">
            {loading && !stats ? (
              <div className="w-40 h-40 rounded-full bg-slate-100 dark:bg-slate-800 animate-pulse" />
            ) : (stats?.sentimiento_distribucion.every(d => d.value === 0)) ? (
              <div className="text-sm text-center text-slate-500 font-medium">No hay datos de sentimiento aún</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats?.sentimiento_distribucion ?? []}
                    cx="50%"
                    cy="45%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {(stats?.sentimiento_distribucion ?? []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} stroke="var(--card)" />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: "var(--card)", borderColor: "var(--border)", color: "var(--foreground)", borderRadius: "0.75rem", boxShadow: "var(--shadow-md)" }}
                    itemStyle={{ color: "var(--foreground)" }}
                  />
                  <Legend verticalAlign="bottom" height={36} iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Actividad Reciente ── */}
      <div className="mt-8 animate-entry delay-300">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">Actividad Reciente</h2>
          <Button variant="ghost" size="sm" className="text-indigo-600 dark:text-indigo-400">Ver todo</Button>
        </div>
        <Card className="border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
          <div className="divide-y divide-slate-100 dark:divide-slate-800/50">
            {loading && !stats ? (
              <div className="p-4 space-y-4">
                <div className="h-4 w-3/4 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
                <div className="h-4 w-1/2 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
              </div>
            ) : (!stats?.actividad_reciente || stats.actividad_reciente.length === 0) ? (
              <div className="p-4 text-sm text-center text-slate-500 font-medium">No hay actividad reciente</div>
            ) : (
              stats.actividad_reciente.map((item) => {
                const date = new Date(item.time);
                const timeStr = isNaN(date.getTime()) ? item.time : date.toLocaleTimeString("es-EC", { hour: '2-digit', minute: '2-digit' });
                return (
                  <div key={item.id} className="p-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${item.status === 'success' ? 'bg-emerald-500' : 'bg-blue-500'}`} />
                      <div>
                        <p className="text-sm font-medium text-slate-800 dark:text-slate-200">{item.action}</p>
                        <p className="text-xs text-slate-500 dark:text-slate-400">{item.agent}</p>
                      </div>
                    </div>
                    <span className="text-xs text-slate-500 dark:text-slate-400">{timeStr}</span>
                  </div>
                );
              })
            )}
          </div>
        </Card>
      </div>

      {/* ── Active Agent Footer ── */}
      {phase >= 5 && (
        <div className="mt-8 mb-4 p-4 md:p-6 rounded-2xl bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-800 text-white shadow-lg flex flex-col md:flex-row items-center justify-between gap-4 animate-entry delay-400">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center backdrop-blur-md border border-white/30">
              <Bot size={24} className="text-white" />
            </div>
            <div>
              <h3 className="font-bold text-lg leading-tight">FluxBot Activo</h3>
              <p className="text-indigo-100 text-sm">El agente de ventas está procesando conversaciones en tiempo real.</p>
            </div>
          </div>
          <div className="flex gap-3 w-full md:w-auto">
            <Button className="bg-white/10 hover:bg-white/20 text-white border border-white/20 backdrop-blur-sm flex-1 md:flex-none">
              Entrenar
            </Button>
            <Button className="bg-white hover:bg-slate-100 text-indigo-700 font-semibold flex-1 md:flex-none shadow-sm">
              Configurar
            </Button>
          </div>
        </div>
      )}

      <QuickStartModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onComplete={handleOnboardingComplete}
      />

    </div>
  );
}
