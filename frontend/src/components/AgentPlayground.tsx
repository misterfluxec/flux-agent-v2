"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { Send, Bot, User, Loader2, Trash2, Zap, FileText, Database, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { sendChat } from "@/lib/api";

interface Message {
  rol: "usuario" | "asistente";
  contenido: string;
  tokens?: number;
  fuentes?: string[];
  chunks?: number;
}

const SESSION_ID = `playground-${Date.now()}`;

function SourceIcon({ fuente }: { fuente: string }) {
  if (fuente.includes("http")) return <Globe size={10} />;
  if (fuente.match(/\.(xlsx|xls|csv)/i)) return <Database size={10} />;
  return <FileText size={10} />;
}

export default function AgentPlayground() {
  const [messages, setMessages] = useState<Message[]>([{
    rol: "asistente",
    contenido: "👋 Hola, soy tu agente. Pregúntame sobre los documentos entrenados.",
  }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);


  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  const sendMessage = useCallback(async () => {
    const texto = input.trim();
    if (!texto || loading) return;
    setInput("");
    setMessages(p => [...p, { rol: "usuario", contenido: texto }]);
    setLoading(true);
    try {
      const res = await sendChat({
        session_id: SESSION_ID, mensaje: texto,
        historial: messages.map(m => ({ rol: m.rol, contenido: m.contenido })),
        configuracion: { nombre: "FluxBot", humor: "profesional" },
      });
      setMessages(p => [...p, { rol: "asistente", contenido: res.respuesta, tokens: res.tokens, fuentes: res.fuentes_rag, chunks: res.chunks_usados }]);
    } catch {
      setMessages(p => [...p, { rol: "asistente", contenido: "⚠️ Sin conexión con el backend." }]);
    } finally { setLoading(false); }
  }, [input, loading, messages]);

  return (
    <div style={{
      background: "var(--card)", border: "1px solid var(--border)",
      borderRadius: "var(--radius)", boxShadow: "var(--shadow-md)",
      display: "flex", flexDirection: "column",
      height: "100%", minHeight: 560, maxHeight: 720,
      position: "sticky", top: 24, overflow: "hidden",
    }}>
      {/* Header */}
      <div style={{
        padding: "14px 16px", borderBottom: "1px solid var(--border)",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        background: "var(--secondary)", flexShrink: 0,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: "var(--radius)",
            background: "var(--primary-light)", display: "flex",
            alignItems: "center", justifyContent: "center",
            border: "1px solid var(--primary-mid)",
          }}>
            <Zap size={16} style={{ color: "var(--primary)" }} />
          </div>
          <div>
            <p style={{ fontSize: 13, fontWeight: 700, color: "var(--foreground)", margin: 0 }}>Simulador</p>
            <p style={{ fontSize: 10, color: "var(--muted-foreground)", margin: 0 }}>🔬 Rayos X activo</p>
          </div>
        </div>
        <button onClick={() => setMessages([{ rol: "asistente", contenido: "👋 Chat reiniciado." }])}
          title="Limpiar chat"
          style={{ padding: 6, borderRadius: 6, border: "none", background: "transparent", cursor: "pointer", color: "var(--muted-foreground)" }}>
          <Trash2 size={13} />
        </button>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: 14, display: "flex", flexDirection: "column", gap: 12 }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ display: "flex", flexDirection: msg.rol === "usuario" ? "row-reverse" : "row", gap: 8, alignItems: "flex-end" }}>
            <div style={{
              width: 28, height: 28, borderRadius: "50%", flexShrink: 0,
              display: "flex", alignItems: "center", justifyContent: "center",
              background: "var(--primary-light)", border: "1px solid var(--primary-mid)",
            }}>
              {msg.rol === "asistente"
                ? <Bot size={13} style={{ color: "var(--primary)" }} />
                : <User size={13} style={{ color: "var(--primary)" }} />}
            </div>
            <div style={{ maxWidth: "78%" }}>
              <div style={{
                padding: "9px 13px",
                borderRadius: msg.rol === "usuario" ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
                fontSize: 13, lineHeight: 1.55,
                background: msg.rol === "usuario" ? "var(--primary)" : "var(--card)",
                color: msg.rol === "usuario" ? "var(--primary-foreground)" : "var(--foreground)",
                border: msg.rol === "asistente" ? "1px solid var(--border)" : "none",
                boxShadow: msg.rol === "asistente" ? "var(--shadow-sm)" : "none",
              }}>
                {msg.contenido}
              </div>
              {msg.fuentes && msg.fuentes.length > 0 && (
                <div style={{ marginTop: 5, display: "flex", flexWrap: "wrap", gap: 4 }}>
                  {msg.fuentes.slice(0, 3).map((f, fi) => (
                    <div key={fi} style={{
                      display: "inline-flex", alignItems: "center", gap: 4,
                      padding: "2px 8px", borderRadius: 20, fontSize: 10,
                      background: "var(--success-light)", border: "1px solid var(--success)",
                      color: "var(--success)", opacity: 0.9,
                    }}>
                      <SourceIcon fuente={f} />
                      {f.length > 28 ? f.slice(0, 28) + "…" : f}
                    </div>
                  ))}
                  {msg.chunks && msg.chunks > 0 && (
                    <span style={{ fontSize: 10, color: "var(--muted-foreground)", alignSelf: "center" }}>
                      {msg.chunks} fragmentos · {msg.tokens} tokens
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
            <div style={{ width: 28, height: 28, borderRadius: "50%", background: "var(--primary-light)", border: "1px solid var(--primary-mid)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Bot size={13} style={{ color: "var(--primary)" }} />
            </div>
            <div style={{ padding: "10px 14px", background: "var(--card)", border: "1px solid var(--border)", borderRadius: "14px 14px 14px 4px", display: "flex", gap: 5, alignItems: "center" }}>
              {[0, 1, 2].map(i => (
                <div key={i} style={{
                  width: 6, height: 6, borderRadius: "50%", background: "var(--primary)",
                  animation: "pulse-dot-light 1s ease-in-out infinite",
                  animationDelay: `${i * 0.18}s`,
                }} />
              ))}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ padding: 12, borderTop: "1px solid var(--border)", display: "flex", gap: 8, background: "var(--secondary)", flexShrink: 0 }}>
        <Input
          value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && !e.shiftKey && sendMessage()}
          placeholder="Pregunta sobre los documentos..." disabled={loading}
          style={{ flex: 1, height: 38, fontSize: 13, borderRadius: 8, border: "1px solid var(--border)", background: "var(--input)", color: "var(--foreground)" }}
        />
        <Button onClick={sendMessage} disabled={!input.trim() || loading}
          style={{ height: 38, width: 38, padding: 0, borderRadius: 8, background: "var(--primary)", color: "var(--primary-foreground)", flexShrink: 0, border: "none", cursor: "pointer" }}>
          {loading ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />}
        </Button>
      </div>
    </div>
  );
}
