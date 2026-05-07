"use client";

import { useState, useRef, useEffect } from "react";
import {
  Terminal as TerminalIcon, Play, Trash2, Copy, ChevronRight,
  Database, Server, Bot, Cloud, AlertTriangle, CheckCircle, Wifi
} from "lucide-react";
import { toast } from "sonner";

interface TerminalLine {
  id: string;
  type: "cmd" | "out" | "err" | "sys";
  text: string;
  ts: string;
}

const HEALTH_SERVICES = [
  { id: "postgres",  label: "PostgreSQL",    status: "healthy",  latency: "12ms",  icon: Database },
  { id: "redis",     label: "Redis Cache",   status: "healthy",  latency: "3ms",   icon: Server   },
  { id: "ollama",    label: "Ollama IA",     status: "healthy",  latency: "45ms",  icon: Bot      },
  { id: "evolution", label: "Evolution API", status: "warning",  latency: "230ms", icon: Cloud    },
  { id: "nginx",     label: "Nginx Proxy",   status: "healthy",  latency: "8ms",   icon: Server   },
];

const QUICK_COMMANDS = [
  { cmd: "check:health",      label: "Health Check",        desc: "Verifica todos los servicios"  },
  { cmd: "restart:evolution", label: "Reiniciar Evolution", desc: "Reinicia instancias WhatsApp"  },
  { cmd: "restart:backend",   label: "Reiniciar Backend",   desc: "Reinicia el servidor FastAPI"  },
  { cmd: "clear:redis",       label: "Limpiar Caché",       desc: "Purga caché Redis del sistema" },
  { cmd: "reindex:rag",       label: "Reindexar RAG",       desc: "Reconstruye índices de búsqueda"},
  { cmd: "logs:tail",         label: "Ver últimos Logs",    desc: "Muestra últimas 50 líneas"     },
];

const CMD_RESPONSES: Record<string, string> = {
  "check:health":      "✓ PostgreSQL: OK (12ms)\n✓ Redis: OK (3ms)\n✓ Ollama: OK (45ms)\n⚠ Evolution: ADVERTENCIA (230ms)\n✓ Nginx: OK (8ms)",
  "clear:redis":       "✓ Caché limpiada correctamente\n✓ 1,234 claves eliminadas\n✓ Tiempo: 45ms",
  "restart:evolution": "⏳ Deteniendo Evolution API…\n✓ Servicio detenido\n⏳ Iniciando servicio…\n✓ Evolution API operativa (puerto 8080)",
  "restart:backend":   "⏳ Deteniendo uvicorn…\n✓ Servidor detenido\n⏳ Iniciando workers…\n✓ Backend operativo en puerto 8000",
  "reindex:rag":       "⏳ Reindexando colección RAG…\n✓ 1,523 documentos procesados\n✓ Índices pgvector actualizados\n✓ Búsqueda semántica operativa",
  "logs:tail":         "[10:35:22] INFO: Health check ejecutado\n[10:35:15] INFO: Login - admin@labodegaec.com\n[10:34:58] WARN: Rate limit cercano (95%)\n[10:34:42] ERROR: Ollama timeout — TechShop",
};

function ts() {
  return new Date().toLocaleTimeString("es-EC");
}

export default function TerminalPage() {
  const [lines,    setLines]    = useState<TerminalLine[]>([
    { id: "0", type: "sys", text: "FluxAgent V2 — Terminal de Emergencia. Solo personal autorizado.", ts: ts() },
  ]);
  const [input,    setInput]    = useState("");
  const [running,  setRunning]  = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [lines]);

  const addLine = (line: Omit<TerminalLine, "id" | "ts">) =>
    setLines(prev => [...prev, { ...line, id: Date.now().toString() + Math.random(), ts: ts() }]);

  const exec = (cmd: string) => {
    if (!cmd.trim() || running) return;
    setRunning(true);
    addLine({ type: "cmd", text: cmd });
    setTimeout(() => {
      const out = CMD_RESPONSES[cmd.trim()];
      if (out) {
        addLine({ type: "out", text: out });
      } else {
        addLine({ type: "err", text: `bash: ${cmd}: command not found` });
      }
      setRunning(false);
    }, 1200);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    exec(input.trim());
    setInput("");
  };

  return (
    <div className="space-y-8 animate-entry pb-20">
      {/* Cabecera */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Terminal de Emergencia</h1>
          <p className="text-slate-500 text-sm mt-1">Consola de administración para comandos rápidos del sistema</p>
        </div>
        <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-3 py-1.5 rounded-lg text-xs font-semibold">
          <Wifi size={12} className="animate-pulse" />
          SESIÓN SEGURA ACTIVA
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6">
        {/* Terminal */}
        <div className="bg-[#0d1117] border border-slate-800 rounded-2xl overflow-hidden shadow-2xl flex flex-col">
          {/* Barra de título estilo macOS */}
          <div className="flex items-center justify-between px-4 py-3 bg-[#161b22] border-b border-slate-800">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500/80" />
              <div className="w-3 h-3 rounded-full bg-amber-500/80" />
              <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
              <span className="text-slate-500 text-xs ml-3 font-mono">root@fluxagent-v2 ~ $</span>
            </div>
            <div className="flex gap-2">
              <button onClick={() => { navigator.clipboard.writeText(lines.map(l => l.text).join("\n")); toast.success("Copiado al portapapeles"); }}
                className="p-1.5 hover:bg-slate-700 rounded text-slate-500 hover:text-slate-300 transition-colors" title="Copiar todo">
                <Copy size={13} />
              </button>
              <button onClick={() => setLines([{ id: "clear", type: "sys", text: "Terminal limpiada.", ts: ts() }])}
                className="p-1.5 hover:bg-slate-700 rounded text-slate-500 hover:text-slate-300 transition-colors" title="Limpiar terminal">
                <Trash2 size={13} />
              </button>
            </div>
          </div>

          {/* Output */}
          <div className="flex-1 p-5 font-mono text-sm overflow-y-auto space-y-3 min-h-[380px] max-h-[480px]">
            {lines.map(line => (
              <div key={line.id}>
                {line.type === "sys" && (
                  <p className="text-emerald-500/70 text-xs"># {line.text}</p>
                )}
                {line.type === "cmd" && (
                  <div className="flex items-center gap-2">
                    <ChevronRight size={13} className="text-emerald-400 shrink-0" />
                    <span className="text-sky-400">{line.text}</span>
                  </div>
                )}
                {line.type === "out" && (
                  <pre className="text-slate-300 text-xs leading-relaxed pl-5 whitespace-pre-wrap">{line.text}</pre>
                )}
                {line.type === "err" && (
                  <pre className="text-red-400 text-xs leading-relaxed pl-5 whitespace-pre-wrap">{line.text}</pre>
                )}
              </div>
            ))}
            {running && (
              <div className="flex items-center gap-2 text-xs text-slate-500 pl-5">
                <span className="inline-block w-1.5 h-3.5 bg-slate-400 animate-pulse" />
              </div>
            )}
            <div ref={endRef} />
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="flex items-center gap-2 p-4 border-t border-slate-800 bg-[#161b22]">
            <ChevronRight size={14} className="text-emerald-400 shrink-0" />
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              disabled={running}
              placeholder={running ? "Ejecutando…" : "Escribe un comando (ej: check:health)…"}
              autoFocus
              className="flex-1 bg-transparent text-slate-200 text-sm font-mono focus:outline-none placeholder:text-slate-600 disabled:opacity-50"
            />
            <button type="submit" disabled={running || !input.trim()}
              className="shrink-0 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white px-3 py-1.5 rounded-lg text-xs font-semibold transition-all">
              Ejecutar
            </button>
          </form>
        </div>

        {/* Panel lateral */}
        <div className="space-y-5">
          {/* Estado de servicios */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h3 className="text-sm font-bold text-slate-300 mb-4">Estado de Servicios</h3>
            <div className="space-y-3">
              {HEALTH_SERVICES.map(svc => {
                const Icon      = svc.icon;
                const isHealthy = svc.status === "healthy";
                return (
                  <div key={svc.id} className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <Icon size={14} className={isHealthy ? "text-emerald-400" : "text-amber-400"} />
                      <span className="text-sm text-slate-300">{svc.label}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      {isHealthy
                        ? <CheckCircle  size={13} className="text-emerald-400" />
                        : <AlertTriangle size={13} className="text-amber-400" />}
                      <span className={`text-xs font-mono ${isHealthy ? "text-emerald-400" : "text-amber-400"}`}>
                        {svc.latency}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Comandos rápidos */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h3 className="text-sm font-bold text-slate-300 mb-4">Comandos Rápidos</h3>
            <div className="space-y-2">
              {QUICK_COMMANDS.map(qc => (
                <button key={qc.cmd} onClick={() => exec(qc.cmd)} disabled={running}
                  className="w-full flex items-center gap-3 p-3 rounded-xl border border-slate-800 hover:border-slate-700 hover:bg-slate-800/50 disabled:opacity-50 disabled:cursor-not-allowed text-left transition-all group">
                  <Play size={12} className="text-emerald-400 group-hover:scale-110 transition-transform shrink-0" />
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-slate-200 truncate">{qc.label}</p>
                    <p className="text-[10px] text-slate-500 truncate">{qc.desc}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}