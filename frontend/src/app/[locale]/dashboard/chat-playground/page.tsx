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
  const messagesEndRef = useRef<HTMLDivElement>(null);

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
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <div className="max-w-3xl mx-auto flex flex-col h-[calc(100dvh-7rem)] animate-entry">
      {/* ── Header ── */}
      <div
        className="flex items-center gap-3 px-4 py-3 shrink-0"
        style={{ borderBottom: "1px solid var(--border)", background: "var(--card)" }}
      >
        <div
          className="w-8 h-8 flex items-center justify-center"
          style={{ background: "var(--primary)", color: "var(--primary-foreground)" }}
        >
          <Bot size={16} />
        </div>
        <div>
          <p className="text-sm font-medium" style={{ color: "var(--foreground)" }}>FluxBot</p>
          <p className="text-xs font-mono-data" style={{ color: "var(--chart-2)" }}>
            ● EN LÍNEA · qwen2.5:3b
          </p>
        </div>
        <div className="ml-auto text-xs font-mono-data" style={{ color: "var(--muted-foreground)" }}>
          {messages.length} mensajes
        </div>
      </div>

      {/* ── Messages ── */}
      <div
        className="flex-1 overflow-y-auto py-4 px-4 space-y-4"
        style={{ background: "var(--background)" }}
      >
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center gap-4 text-center">
            <div
              className="w-16 h-16 flex items-center justify-center"
              style={{ border: "1px solid var(--border)", color: "var(--muted-foreground)" }}
            >
              <Bot size={24} />
            </div>
            <div>
              <p className="font-medium text-sm" style={{ color: "var(--foreground)" }}>
                Agente listo
              </p>
              <p className="text-xs mt-1" style={{ color: "var(--muted-foreground)" }}>
                Hazme una pregunta sobre los productos indexados.
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
              <div
                className="w-7 h-7 flex items-center justify-center shrink-0 text-xs font-bold"
                style={{
                  background: isUser ? "var(--secondary)" : "var(--primary)",
                  color: isUser ? "var(--foreground)" : "var(--primary-foreground)",
                }}
              >
                {isUser ? <User size={12} /> : <Bot size={12} />}
              </div>

              {/* Bubble */}
              <div className={`max-w-[80%] ${isUser ? "items-end" : "items-start"} flex flex-col gap-1`}>
                <div
                  className="px-4 py-3 text-sm leading-relaxed"
                  style={{
                    background: isUser ? "var(--secondary)" : "var(--card)",
                    border: `1px solid ${isUser ? "var(--border)" : "var(--primary)"}30`,
                    borderLeft: isUser ? undefined : "2px solid var(--primary)",
                    color: "var(--foreground)",
                  }}
                >
                  {m.contenido}
                </div>
                <div className="flex items-center gap-2 px-1">
                  <span className="text-[10px] font-mono-data" style={{ color: "var(--muted-foreground)" }}>
                    {m.timestamp.toLocaleTimeString("es-EC", { hour: "2-digit", minute: "2-digit" })}
                  </span>
                  {m.tokens != null && (
                    <span className="text-[10px] font-mono-data" style={{ color: "var(--muted-foreground)" }}>
                      · {m.tokens} tokens
                    </span>
                  )}
                  {m.fuentes && m.fuentes.length > 0 && (
                    <span className="text-[10px] font-mono-data" style={{ color: "var(--primary)" }}>
                      · RAG: {m.fuentes.join(", ")}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {/* Typing indicator */}
        {loading && (
          <div className="flex gap-3 animate-entry">
            <div
              className="w-7 h-7 flex items-center justify-center shrink-0"
              style={{ background: "var(--primary)", color: "var(--primary-foreground)" }}
            >
              <Bot size={12} />
            </div>
            <div
              className="px-4 py-3 flex items-center gap-1"
              style={{ border: "1px solid var(--border)", background: "var(--card)" }}
            >
              <Loader2 size={14} className="animate-spin" style={{ color: "var(--primary)" }} />
              <span className="text-xs font-mono-data" style={{ color: "var(--muted-foreground)" }}>
                Procesando...
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* ── Input bar ── */}
      <div
        className="shrink-0 px-4 py-3 flex gap-3 items-center"
        style={{ borderTop: "1px solid var(--border)", background: "var(--card)" }}
      >
        <Input
          id="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Escribe tu pregunta..."
          disabled={loading}
          className="h-10 flex-1 text-sm"
          style={{
            background: "var(--input)",
            border: "1px solid var(--border)",
            color: "var(--foreground)",
          }}
          autoComplete="off"
        />
        <Button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="h-10 w-10 p-0 shrink-0 transition-all hover:opacity-90 active:scale-95"
          style={{ background: "var(--primary)", color: "var(--primary-foreground)" }}
          aria-label="Enviar mensaje"
        >
          <Send size={16} />
        </Button>
      </div>
    </div>
  );
}
