"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Bot, LayoutDashboard, MessageSquare, BarChart3, Plug, LogOut,
  Zap, Brain, Users2, Building2, Send, Loader2, Sparkles,
  AlertTriangle, ArrowRight,
} from "lucide-react";
import { sendChat } from "@/lib/api";

// =============================================================================
// YANUA OVERLAY — Cmd+K Global Intelligence Layer
// No es solo navegación. Es un copiloto operacional.
// =============================================================================

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<"nav" | "chat">("nav");
  const [chatMessages, setChatMessages] = useState<{ role: string; text: string }[]>([]);
  const [isThinking, setIsThinking] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen(o => !o);
      }
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  useEffect(() => {
    if (open) {
      setQuery("");
      setMode("nav");
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  const runCommand = (cmd: () => void) => { setOpen(false); cmd(); };

  const handleSubmit = async () => {
    if (!query.trim()) return;

    if (mode === "nav") {
      // Check if it's a question — switch to chat mode
      const isQuestion = query.includes("?") || query.length > 30 ||
        /^(qué|cómo|por qué|muéstrame|dime|explica|analiza|resume)/i.test(query);

      if (isQuestion) {
        setMode("chat");
        const userMsg = query;
        setChatMessages([{ role: "user", text: userMsg }]);
        setQuery("");
        setIsThinking(true);

        try {
          const res = await sendChat({
            session_id: "yanua-overlay",
            mensaje: userMsg,
            historial: [],
            configuracion: { nombre: "Yanua", humor: "profesional" },
          });
          setChatMessages(prev => [...prev, { role: "assistant", text: res.respuesta }]);
        } catch {
          setChatMessages(prev => [...prev, { role: "assistant", text: "Error al conectar con el motor IA. Verifica que esté operativo." }]);
        } finally {
          setIsThinking(false);
        }
        return;
      }
    }

    if (mode === "chat") {
      const userMsg = query;
      setChatMessages(prev => [...prev, { role: "user", text: userMsg }]);
      setQuery("");
      setIsThinking(true);

      try {
        const res = await sendChat({
          session_id: "yanua-overlay",
          mensaje: userMsg,
          historial: chatMessages.map(m => ({ rol: m.role === "user" ? "user" : "assistant", contenido: m.text })),
          configuracion: { nombre: "Yanua", humor: "profesional" },
        });
        setChatMessages(prev => [...prev, { role: "assistant", text: res.respuesta }]);
      } catch {
        setChatMessages(prev => [...prev, { role: "assistant", text: "Error de conexión con Yanua." }]);
      } finally {
        setIsThinking(false);
      }
    }
  };

  // Navigation items
  const NAV_ITEMS = [
    { icon: LayoutDashboard, label: "Control — Torre de Control", href: "/dashboard", group: "Navegar" },
    { icon: MessageSquare, label: "Operaciones — Centro de Comando", href: "/dashboard/operations", group: "Navegar" },
    { icon: Users2, label: "Agentes IA — Workforce", href: "/dashboard/agents", group: "Navegar" },
    { icon: Brain, label: "Inteligencia — Conocimiento", href: "/dashboard/data-ingestion", group: "Navegar" },
    { icon: Plug, label: "Canales — Conectores", href: "/dashboard/connectors", group: "Navegar" },
    { icon: Zap, label: "Flujos — Automatizaciones", href: "/dashboard/automations", group: "Navegar" },
    { icon: BarChart3, label: "Resultados — Analytics", href: "/dashboard/analytics", group: "Navegar" },
    { icon: Building2, label: "Organización — Configuración", href: "/dashboard/settings", group: "Navegar" },
  ];

  const ACTIONS = [
    { icon: Sparkles, label: "Preguntarle a Yanua...", action: () => { setMode("chat"); setQuery(""); }, group: "IA", color: "text-cyan-400" },
    { icon: AlertTriangle, label: "Ver handoffs pendientes", action: () => runCommand(() => router.push("/dashboard/operations?tab=queue")), group: "Urgente", color: "text-red-400" },
    { icon: Zap, label: "Aumentar límite de tokens", action: () => runCommand(() => router.push("/dashboard/settings")), group: "Urgente", color: "text-amber-400" },
  ];

  const filteredNav = query
    ? NAV_ITEMS.filter(i => i.label.toLowerCase().includes(query.toLowerCase()))
    : NAV_ITEMS;

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setOpen(false)} />

      {/* Modal */}
      <div className="relative w-full max-w-xl mx-4 bg-[#0D0D0F] border border-white/10 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">

        {/* Input */}
        <div className="flex items-center gap-3 px-5 py-4 border-b border-white/5">
          {mode === "chat" ? (
            <Bot className="h-5 w-5 text-cyan-400 shrink-0" />
          ) : (
            <div className="h-5 w-5 flex items-center justify-center">
              <span className="text-white/20 text-xs font-bold">⌘K</span>
            </div>
          )}
          <input
            ref={inputRef}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSubmit()}
            placeholder={mode === "chat" ? "Pregúntale algo a Yanua..." : "Buscar o preguntar..."}
            className="flex-1 bg-transparent text-sm text-white placeholder:text-white/25 focus:outline-none"
          />
          {mode === "chat" && (
            <button onClick={handleSubmit} disabled={isThinking || !query.trim()}
              className="p-1.5 rounded-lg bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30 disabled:opacity-30 transition-colors">
              {isThinking ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </button>
          )}
        </div>

        {/* Content */}
        <div className="max-h-[50vh] overflow-y-auto">
          {mode === "chat" ? (
            /* Chat Mode */
            <div className="p-4 space-y-3">
              {chatMessages.map((msg, i) => (
                <div key={i} className={`flex gap-2.5 ${msg.role === "user" ? "justify-end" : ""}`}>
                  {msg.role === "assistant" && (
                    <div className="h-6 w-6 rounded-lg bg-cyan-500/10 flex items-center justify-center shrink-0 mt-0.5">
                      <Bot className="h-3.5 w-3.5 text-cyan-400" />
                    </div>
                  )}
                  <div className={`max-w-[85%] px-3 py-2 rounded-xl text-xs leading-relaxed ${
                    msg.role === "user"
                      ? "bg-white/5 text-white/70"
                      : "bg-cyan-500/5 text-white/60 border border-cyan-500/10"
                  }`}>
                    {msg.text}
                  </div>
                </div>
              ))}
              {isThinking && (
                <div className="flex gap-2.5">
                  <div className="h-6 w-6 rounded-lg bg-cyan-500/10 flex items-center justify-center shrink-0">
                    <Bot className="h-3.5 w-3.5 text-cyan-400 animate-pulse" />
                  </div>
                  <div className="bg-cyan-500/5 border border-cyan-500/10 px-3 py-2 rounded-xl">
                    <div className="flex gap-1">
                      <div className="w-1.5 h-1.5 rounded-full bg-cyan-400/40 animate-bounce" style={{ animationDelay: "0ms" }} />
                      <div className="w-1.5 h-1.5 rounded-full bg-cyan-400/40 animate-bounce" style={{ animationDelay: "150ms" }} />
                      <div className="w-1.5 h-1.5 rounded-full bg-cyan-400/40 animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          ) : (
            /* Navigation Mode */
            <div className="py-2">
              {/* Smart Actions */}
              <div className="px-3 pb-1 pt-2">
                <p className="text-[10px] font-bold text-white/15 uppercase tracking-wider px-2 mb-1">Acciones IA</p>
              </div>
              {ACTIONS.map((a, i) => (
                <button key={i} onClick={() => a.action()}
                  className="w-full flex items-center gap-3 px-5 py-2.5 text-sm text-white/50 hover:bg-white/5 hover:text-white/80 transition-colors">
                  <a.icon className={`h-4 w-4 ${a.color}`} />
                  <span>{a.label}</span>
                </button>
              ))}

              <div className="border-t border-white/5 my-2" />

              {/* Navigation */}
              <div className="px-3 pb-1 pt-2">
                <p className="text-[10px] font-bold text-white/15 uppercase tracking-wider px-2 mb-1">Navegación</p>
              </div>
              {filteredNav.map(item => (
                <button key={item.href} onClick={() => runCommand(() => router.push(item.href))}
                  className="w-full flex items-center gap-3 px-5 py-2.5 text-sm text-white/40 hover:bg-white/5 hover:text-white/70 transition-colors group">
                  <item.icon className="h-4 w-4 text-white/20 group-hover:text-white/50" />
                  <span>{item.label}</span>
                  <ArrowRight className="h-3 w-3 ml-auto text-white/10 opacity-0 group-hover:opacity-100" />
                </button>
              ))}

              <div className="border-t border-white/5 my-2" />

              {/* Logout */}
              <button onClick={() => runCommand(() => { localStorage.removeItem('flux_token'); router.push('/login'); })}
                className="w-full flex items-center gap-3 px-5 py-2.5 text-sm text-red-400/50 hover:bg-red-500/5 hover:text-red-400 transition-colors">
                <LogOut className="h-4 w-4" />
                <span>Cerrar Sesión</span>
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-5 py-2.5 border-t border-white/5 bg-black/40">
          <div className="flex items-center gap-3 text-[10px] text-white/15 font-medium">
            {mode === "chat" ? (
              <button onClick={() => setMode("nav")} className="hover:text-white/30 transition-colors">
                ← Volver a navegación
              </button>
            ) : (
              <span>Escribe una pregunta para hablar con Yanua</span>
            )}
          </div>
          <div className="flex items-center gap-2 text-[10px] text-white/15">
            <kbd className="px-1.5 py-0.5 bg-white/5 rounded text-[9px] font-mono">ESC</kbd>
            <span>cerrar</span>
          </div>
        </div>
      </div>
    </div>
  );
}
