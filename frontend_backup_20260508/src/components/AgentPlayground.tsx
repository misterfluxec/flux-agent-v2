"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { Send, Bot, User, Loader2, Trash2, Zap, FileText, Database, Globe, Mic } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { VoiceTestClient } from "./voice/VoiceTestClient";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

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

export default function AgentPlayground({ agentId, tenantId }: { agentId?: string, tenantId?: string }) {
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
    
    const newMessages = [...messages, { rol: "usuario" as const, contenido: texto }];
    setMessages([...newMessages, { rol: "asistente" as const, contenido: "" }]);
    setLoading(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:9000'}/api/v1/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("flux_token") || ""}`,
        },
        body: JSON.stringify({
          session_id: SESSION_ID,
          mensaje: texto,
          agent_id: agentId,
          historial: messages.map(m => ({ rol: m.rol, contenido: m.contenido })),
          configuracion: { nombre: "FluxBot", humor: "profesional" },
        }),
      });

      if (!response.ok) throw new Error("Error en la conexión con el servidor");
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { done, value } = await reader!.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");
        
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.replace("data: ", "").trim();
            if (dataStr === "[DONE]") {
              setLoading(false);
              break;
            }
            try {
              const data = JSON.parse(dataStr);
              if (data.event === "token" && data.texto) {
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1] = {
                    ...updated[updated.length - 1],
                    contenido: updated[updated.length - 1].contenido + data.texto
                  };
                  return updated;
                });
              } else if (data.event === "fuentes") {
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1] = {
                    ...updated[updated.length - 1],
                    fuentes: data.urls,
                    chunks: data.chunks
                  };
                  return updated;
                });
              }
            } catch (e) {
              // Ignore partial JSON parsing errors
            }
          }
        }
      }
    } catch (err) {
      console.error(err);
      setMessages(p => {
        const updated = [...p];
        updated[updated.length - 1].contenido = "⚠️ Error de conexión con el stream.";
        return updated;
      });
    } finally {
      setLoading(false);
    }
  }, [input, loading, messages, agentId]);

  return (
    <div className="flex flex-col h-[600px] border border-border bg-card rounded-xl shadow-md overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-secondary shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center">
            <Zap className="w-4 h-4 text-primary" />
          </div>
          <div>
            <p className="text-sm font-bold m-0">Simulador</p>
            <p className="text-[10px] text-muted-foreground m-0">🔬 Rayos X activo</p>
          </div>
        </div>
        <button 
          onClick={() => setMessages([{ rol: "asistente", contenido: "👋 Chat reiniciado." }])}
          title="Limpiar chat"
          className="p-1.5 rounded-md hover:bg-muted text-muted-foreground transition-colors"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      <Tabs defaultValue="chat" className="flex flex-col flex-1 overflow-hidden">
        <div className="px-4 py-2 border-b bg-muted/30">
          <TabsList className="w-full grid grid-cols-2">
            <TabsTrigger value="chat">Texto</TabsTrigger>
            <TabsTrigger value="voice" className="flex items-center gap-2">
              <Mic className="w-4 h-4" /> Voz
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="chat" className="flex flex-col flex-1 m-0 overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-2 items-end ${msg.rol === "usuario" ? "flex-row-reverse" : "flex-row"}`}>
                <div className="w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center bg-primary/10 border border-primary/20">
                  {msg.rol === "asistente" ? (
                    <Bot className="w-3.5 h-3.5 text-primary" />
                  ) : (
                    <User className="w-3.5 h-3.5 text-primary" />
                  )}
                </div>
                <div className="max-w-[78%]">
                  <div className={`px-3 py-2 text-sm leading-relaxed ${
                    msg.rol === "usuario" 
                      ? "rounded-[14px_14px_4px_14px] bg-primary text-primary-foreground" 
                      : "rounded-[14px_14px_14px_4px] bg-card text-foreground border shadow-sm"
                  }`}>
                    {msg.contenido}
                  </div>
                  {msg.fuentes && msg.fuentes.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {msg.fuentes.slice(0, 3).map((f, fi) => (
                        <div key={fi} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] bg-green-500/10 border border-green-500/20 text-green-600">
                          <SourceIcon fuente={f} />
                          {f.length > 20 ? f.slice(0, 20) + "…" : f}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && messages[messages.length - 1]?.contenido === "" && (
              <div className="flex gap-2 items-end">
                <div className="w-7 h-7 rounded-full flex items-center justify-center bg-primary/10 border border-primary/20">
                  <Bot className="w-3.5 h-3.5 text-primary" />
                </div>
                <div className="px-3 py-3 bg-card border rounded-[14px_14px_14px_4px] flex gap-1 items-center">
                  {[0, 1, 2].map(i => (
                    <div key={i} className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" style={{ animationDelay: `${i * 0.15}s` }} />
                  ))}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t bg-secondary flex gap-2 shrink-0">
            <Input
              value={input} 
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && !e.shiftKey && sendMessage()}
              placeholder="Pregunta a tu agente..." 
              disabled={loading}
              className="flex-1 h-9 text-sm"
            />
            <Button 
              onClick={sendMessage} 
              disabled={!input.trim() || loading}
              className="h-9 w-9 p-0 shrink-0"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="voice" className="flex-1 p-4 m-0 bg-muted/10 overflow-y-auto">
          <VoiceTestClient tenantId={tenantId || "default"} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
