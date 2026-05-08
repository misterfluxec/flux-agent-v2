"use client";

import { useState } from "react";
import {
  FileText, Search, Download, RefreshCw,
  AlertTriangle, Info, XCircle, CheckCircle, Clock,
  Database, Server, Bot, Users
} from "lucide-react";
import { toast } from "sonner";

interface LogEntry {
  id: string;
  timestamp: string;
  nivel: "info" | "warn" | "error" | "debug";
  servicio: string;
  mensaje: string;
  usuario?: string;
  tenant?: string;
}

const NIVELES = [
  { id: "info",  label: "INFO",  icon: Info,          cls: "bg-blue-500/10  text-blue-400"  },
  { id: "warn",  label: "WARN",  icon: AlertTriangle,  cls: "bg-amber-500/10 text-amber-400" },
  { id: "error", label: "ERROR", icon: XCircle,        cls: "bg-red-500/10   text-red-400"   },
  { id: "debug", label: "DEBUG", icon: CheckCircle,    cls: "bg-slate-500/10 text-slate-400" },
];

const SERVICIOS = [
  { id: "backend",  label: "Backend",     icon: Server   },
  { id: "database", label: "PostgreSQL",  icon: Database },
  { id: "ia",       label: "Agentes IA",  icon: Bot      },
  { id: "auth",     label: "Auth",        icon: Users    },
];

const LOGS_EJEMPLO: LogEntry[] = [
  { id: "1", timestamp: "2026-04-30T10:35:22.123Z", nivel: "info",  servicio: "backend",  mensaje: "Health check ejecutado correctamente", usuario: "system" },
  { id: "2", timestamp: "2026-04-30T10:35:15.456Z", nivel: "info",  servicio: "auth",     mensaje: "Login exitoso para admin@labodegaec.com", tenant: "LaBodegaEC" },
  { id: "3", timestamp: "2026-04-30T10:34:58.789Z", nivel: "warn",  servicio: "backend",  mensaje: "Rate limit cercano para tenant LaBodegaEC (95%)" },
  { id: "4", timestamp: "2026-04-30T10:34:42.012Z", nivel: "error", servicio: "ia",       mensaje: "Ollama no respondió después de 30s", tenant: "TechShop" },
  { id: "5", timestamp: "2026-04-30T10:34:30.345Z", nivel: "info",  servicio: "database", mensaje: "Query ejecutada en 45ms (leads)" },
  { id: "6", timestamp: "2026-04-30T10:34:15.678Z", nivel: "debug", servicio: "backend",  mensaje: "Cache hit para documento: catalogo_productos.pdf" },
  { id: "7", timestamp: "2026-04-30T10:33:58.901Z", nivel: "info",  servicio: "auth",     mensaje: "Token refresh para soporte@fluxagent.com" },
  { id: "8", timestamp: "2026-04-30T10:33:45.234Z", nivel: "warn",  servicio: "backend",  mensaje: "Instancia WhatsApp desconectada: evolution-instance-1" },
];

type TabType = "logs" | "auditoria";

function NivelBadge({ nivel }: { nivel: string }) {
  const cfg = NIVELES.find(n => n.id === nivel) || NIVELES[0];
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase ${cfg.cls}`}>
      {nivel}
    </span>
  );
}

export default function LogsPage() {
  const [logs,            setLogs]            = useState<LogEntry[]>(LOGS_EJEMPLO);
  const [search,          setSearch]          = useState("");
  const [nivelFilter,     setNivelFilter]     = useState<string | null>(null);
  const [servicioFilter,  setServicioFilter]  = useState<string | null>(null);
  const [activeTab,       setActiveTab]       = useState<TabType>("logs");

  const filtered = logs.filter(log => {
    const q = search.toLowerCase();
    const matchSearch   = !q || log.mensaje.toLowerCase().includes(q) || (log.usuario || "").toLowerCase().includes(q) || (log.tenant || "").toLowerCase().includes(q);
    const matchNivel    = !nivelFilter    || log.nivel    === nivelFilter;
    const matchServicio = !servicioFilter || log.servicio === servicioFilter;
    return matchSearch && matchNivel && matchServicio;
  });

  return (
    <div className="space-y-8 animate-entry pb-20">
      {/* Cabecera */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Logs &amp; Auditoría</h1>
          <p className="text-slate-500 text-sm mt-1">Visor de logs del sistema y auditoría de acciones críticas</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => setLogs(LOGS_EJEMPLO)}
            className="flex items-center gap-2 border border-slate-700 hover:border-slate-600 text-slate-400 hover:text-slate-200 px-3 py-2 rounded-lg text-sm transition-all">
            <RefreshCw size={14} />
            Actualizar
          </button>
          <button onClick={() => toast.info("Exportando logs...")}
            className="flex items-center gap-2 border border-slate-700 hover:border-slate-600 text-slate-300 hover:text-slate-100 px-4 py-2 rounded-lg text-sm font-medium transition-all">
            <Download size={14} />
            Exportar
          </button>
        </div>
      </div>

      {/* KPIs rápidos */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {NIVELES.map(n => {
          const count = logs.filter(l => l.nivel === n.id).length;
          const Icon  = n.icon;
          return (
            <button key={n.id} onClick={() => setNivelFilter(nivelFilter === n.id ? null : n.id)}
              className={`bg-slate-900 border rounded-2xl p-5 text-left transition-all hover:translate-y-[-1px] ${nivelFilter === n.id ? 'border-slate-600 ring-1 ring-slate-500/30' : 'border-slate-800'}`}>
              <Icon className={`w-5 h-5 mb-3 ${n.cls.split(' ')[1]}`} />
              <div className="text-2xl font-bold text-slate-100">{count}</div>
              <div className="text-xs text-slate-500 mt-0.5">Eventos {n.label}</div>
            </button>
          );
        })}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-slate-900 border border-slate-800 rounded-xl w-fit">
        {(["logs", "auditoria"] as TabType[]).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
              activeTab === tab ? "bg-slate-700 text-slate-100 shadow" : "text-slate-500 hover:text-slate-300"
            }`}>
            {tab === "logs" ? <FileText size={14} /> : <Users size={14} />}
            {tab === "logs" ? "Logs del Sistema" : "Auditoría de Acciones"}
          </button>
        ))}
      </div>

      {/* Filtros */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-[200px] max-w-xs">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar en logs..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 pl-9 pr-4 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
            />
          </div>

          <div className="flex gap-2 flex-wrap">
            {SERVICIOS.map(s => {
              const Icon = s.icon;
              return (
                <button key={s.id} onClick={() => setServicioFilter(servicioFilter === s.id ? null : s.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
                    servicioFilter === s.id
                      ? "border-blue-500/40 bg-blue-500/10 text-blue-400"
                      : "border-slate-800 text-slate-500 hover:border-slate-700 hover:text-slate-300"
                  }`}>
                  <Icon size={12} /> {s.label}
                </button>
              );
            })}
          </div>
        </div>
        {(nivelFilter || servicioFilter || search) && (
          <div className="mt-3 pt-3 border-t border-slate-800 flex items-center gap-2">
            <span className="text-xs text-slate-500">Filtros activos:</span>
            {nivelFilter && <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full">{nivelFilter}</span>}
            {servicioFilter && <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full">{servicioFilter}</span>}
            <button onClick={() => { setNivelFilter(null); setServicioFilter(null); setSearch(""); }}
              className="text-xs text-red-400 hover:text-red-300 ml-2">Limpiar filtros</button>
          </div>
        )}
      </div>

      {/* Tabla de Logs */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
        <div className="grid grid-cols-[160px_70px_110px_1fr_130px] px-6 py-3 bg-slate-950/60 text-[10px] font-bold uppercase tracking-widest text-slate-500">
          <span>Timestamp</span>
          <span>Nivel</span>
          <span>Servicio</span>
          <span>Mensaje</span>
          <span>Usuario / Tenant</span>
        </div>

        <div className="divide-y divide-slate-800" style={{ maxHeight: "52vh", overflowY: "auto" }}>
          {filtered.length === 0 ? (
            <div className="py-16 text-center">
              <FileText size={32} className="text-slate-700 mx-auto mb-3" />
              <p className="text-slate-500 text-sm">No hay logs que coincidan con los filtros</p>
            </div>
          ) : (
            filtered.map(log => (
              <div key={log.id} className="grid grid-cols-[160px_70px_110px_1fr_130px] px-6 py-3 text-sm items-center hover:bg-slate-800/20 transition-colors">
                <span className="font-mono text-[11px] text-slate-500">
                  {new Date(log.timestamp).toLocaleString("es-EC", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                </span>
                <span><NivelBadge nivel={log.nivel} /></span>
                <span className="text-slate-400 capitalize text-xs">{log.servicio}</span>
                <span className="text-slate-300 text-xs truncate pr-4">{log.mensaje}</span>
                <span className="text-slate-500 text-[11px] truncate">{log.usuario || log.tenant || "—"}</span>
              </div>
            ))
          )}
        </div>
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-950/30 flex justify-between items-center">
          <span className="text-xs text-slate-500">Mostrando {filtered.length} de {logs.length} entradas</span>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Clock size={12} />
            Logs de los últimos 7 días
          </div>
        </div>
      </div>
    </div>
  );
}