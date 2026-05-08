"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Bot, User, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { sendChat, type ChatResponse } from "@/lib/api";
import { toast } from "sonner";

interface Message {
  id: string;
  rol: "usuario" | "asistente";
  contenido: string;
  fuentes?: string[];
  tokens?: number;
  timestamp: Date;
}

export default function ChatPage() {
  const [messages, setMessages]   = useState<Message[]>([]);
  const [input, setInput]         = useState("");
  const [loading, setLoading]     = useState(false);
  const [tenantId, setTenantId]   = useState("");
  const [showCommands, setShowCommands] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const SLASH_COMMANDS = [
    { cmd: "/metrics", desc: "Ver resumen de leads de hoy" },
    { cmd: "/config", desc: "Ajustar tono de IA a profesional" },
    { cmd: "/handoffs", desc: "Listar leads esperando humano" },
    { cmd: "/clear", desc: "Limpiar consola" }
  ];

  useEffect(() => {
    const id = localStorage.getItem("flux_tenant_id") ?? "11111111-1111-1111-1111-111111111111";
    setTenantId(id);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(async () => {
    const msg = input.trim();
    if (!msg || loading) return;

    const userMsg: Message = {
      id: crypto.randomUUID(),
      rol: "usuario",
      contenido: msg,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const historial = messages.slice(-6).map((m) => ({
        rol: m.rol,
        contenido: m.contenido,
      }));

      const res: ChatResponse = await sendChat({
        tenant_id: tenantId,
        session_id: "session-ui-1",
        mensaje: msg,
        historial,
        configuracion: { nombre: "FluxBot", humor: "profesional" },
      });

      const botMsg: Message = {
        id: crypto.randomUUID(),
        rol: "asistente",
        contenido: res.respuesta,
        fuentes: res.fuentes_rag,
        tokens: res.tokens,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch {
      toast.error("Error de conexión", {
        description: "No se pudo contactar al backend. Verifica que el servicio esté activo.",
      });
    } finally {
      setLoading(false);
    }
  }, [input, loading, messages, tenantId]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { 
      e.preventDefault(); 
      if (input === "/clear") {
        setMessages([]);
        setInput("");
        setShowCommands(false);
        return;
      }
      handleSend(); 
    }
  };

  const handleInputChange = (val: string) => {
    setInput(val);
    if (val.startsWith("/")) {
      setShowCommands(true);
    } else {
      setShowCommands(false);
    }
  };

  const selectCommand = (cmd: string) => {
    setInput(cmd + " ");
    setShowCommands(false);
    document.getElementById('chat-input')?.focus();
  };

  return (
    <div className="max-w-4xl mx-auto flex flex-col h-[calc(100dvh-7rem)] animate-in fade-in duration-700 relative">
      {/* Premium Background Effects */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-[120px] pointer-events-none -z-10" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-[120px] pointer-events-none -z-10" />

      {/* ── Header ── */}
      <div className="flex items-center gap-4 px-6 py-4 shrink-0 bg-black/40 backdrop-blur-xl border border-white/5 rounded-t-[24px] shadow-lg">
        <div className="w-10 h-10 rounded-2xl flex items-center justify-center bg-primary/20 border border-primary/30 shadow-[0_0_15px_rgba(6,182,212,0.2)] text-primary">
          <Bot size={20} />
        </div>
        <div>
          <p className="text-sm font-bold text-white/90">FluxBot Sandbox</p>
          <p className="text-xs font-mono text-emerald-400 font-medium">
            ● EN LÍNEA · qwen2.5:3b
          </p>
        </div>
        <div className="ml-auto text-xs font-mono text-white/40 font-medium">
          {messages.length} mensajes
        </div>
      </div>

      {/* ── Messages ── */}
      <div className="flex-1 overflow-y-auto py-6 px-6 space-y-6 bg-black/20 backdrop-blur-md border-x border-white/5">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center gap-4 text-center">
            <div className="w-20 h-20 rounded-full flex items-center justify-center bg-white/5 border border-white/10 text-white/40 shadow-xl">
              <Bot size={32} />
            </div>
            <div>
              <p className="font-bold text-lg text-white/80">
                Consola Yanua
              </p>
              <p className="text-sm mt-2 text-white/40 font-light max-w-sm">
                Interactúa con tu agente. Escribe <kbd className="bg-white/10 px-1 py-0.5 rounded font-mono">/</kbd> para ver comandos rápidos.
              </p>
            </div>
          </div>
        )}

        {messages.map((m) => {
          const isUser = m.rol === "usuario";
          return (
            <div
              key={m.id}
              className={`flex gap-3 animate-entry ${isUser ? "flex-row-reverse" : ""}`}
            >
              {/* Avatar */}
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-xs shadow-lg ${
                  isUser 
                    ? "bg-white/10 text-white/80 border border-white/10" 
                    : "bg-primary/20 text-primary border border-primary/30 shadow-[0_0_15px_rgba(6,182,212,0.3)]"
                }`}>
                {isUser ? <User size={14} /> : <Bot size={14} />}
              </div>

              {/* Bubble */}
              <div className={`max-w-[80%] ${isUser ? "items-end" : "items-start"} flex flex-col gap-1.5`}>
                <div className={`px-5 py-3.5 text-sm leading-relaxed rounded-2xl ${
                    isUser 
                      ? "bg-white/10 border border-white/5 text-white/90 rounded-tr-sm" 
                      : "bg-black/60 border border-white/5 border-l-2 border-l-primary text-white/80 rounded-tl-sm shadow-[0_0_20px_rgba(0,0,0,0.5)]"
                  }`}>
                  {m.contenido}
                </div>
                <div className="flex items-center gap-3 px-2">
                  <span className="text-[10px] font-mono text-white/30">
                    {m.timestamp.toLocaleTimeString("es-EC", { hour: "2-digit", minute: "2-digit" })}
                  </span>
                  {m.tokens != null && (
                    <span className="text-[10px] font-mono text-white/40 bg-white/5 px-2 py-0.5 rounded-full border border-white/10">
                      {m.tokens} tokens
                    </span>
                  )}
                  {m.fuentes && m.fuentes.length > 0 && (
                    <span className="text-[10px] font-mono text-primary bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20">
                      RAG: {m.fuentes.join(", ")}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {/* Typing indicator */}
        {loading && (
          <div className="flex gap-3 animate-in fade-in slide-in-from-bottom-4">
            <div className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 bg-primary/20 text-primary border border-primary/30 shadow-[0_0_15px_rgba(6,182,212,0.3)]">
              <Bot size={14} />
            </div>
            <div className="px-5 py-3.5 flex items-center gap-3 bg-black/60 border border-white/5 rounded-2xl rounded-tl-sm shadow-[0_0_20px_rgba(0,0,0,0.5)]">
              <Loader2 size={16} className="animate-spin text-primary" />
              <span className="text-xs font-mono text-white/50">
                Procesando IA...
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="shrink-0 relative bg-black/40 backdrop-blur-xl border border-white/5 rounded-b-[24px] shadow-xl">
        
        {/* Comando flotante */}
        {showCommands && (
          <div className="absolute bottom-full left-0 mb-2 w-64 bg-[#111827] border border-white/10 rounded-xl shadow-2xl overflow-hidden z-20 animate-in slide-in-from-bottom-2">
            <div className="px-3 py-2 border-b border-white/5 bg-white/5">
              <p className="text-[10px] font-bold uppercase tracking-wider text-white/50">Comandos de Consola</p>
            </div>
            <div className="p-1">
              {SLASH_COMMANDS.map((c) => (
                <button 
                  key={c.cmd}
                  onClick={() => selectCommand(c.cmd)}
                  className="w-full text-left px-3 py-2 hover:bg-white/5 rounded-lg transition-colors flex items-center justify-between group"
                >
                  <span className="font-mono text-xs text-primary">{c.cmd}</span>
                  <span className="text-[10px] text-white/40 group-hover:text-white/60">{c.desc}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="px-6 py-4 flex gap-4 items-center">
          <Input
            id="chat-input"
            value={input}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Escribe tu comando o pregunta (usa / para comandos)..."
            disabled={loading}
            className="h-12 flex-1 text-sm bg-black/20 border-white/10 text-white/90 placeholder:text-white/30 rounded-xl focus-visible:ring-1 focus-visible:ring-primary/50"
            autoComplete="off"
          />
          <Button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="h-12 w-12 rounded-xl p-0 shrink-0 transition-all hover:scale-105 active:scale-95 bg-primary hover:bg-primary/90 text-black shadow-[0_0_20px_rgba(6,182,212,0.4)] disabled:opacity-50 disabled:hover:scale-100 disabled:shadow-none"
            aria-label="Enviar mensaje"
          >
            <Send size={18} />
          </Button>
        </div>
      </div>
    </div>
  );
}
