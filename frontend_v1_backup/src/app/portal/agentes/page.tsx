"use client";

import { useEffect, useState, useCallback } from "react";
import { 
  Bot, Plus, Search, MoreVertical, Trash2, Edit3, Play,
  Settings, MessageSquare, Phone, Mail, Globe,
  CheckCircle, XCircle, Clock, AlertTriangle, Zap
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

interface Agent {
  id: string;
  nombre: string;
  area: string | null;
  descripcion: string | null;
  genero: string;
  humor: string;
  modelo: string;
  canales: string[];
  estado: string;
  coleccion_rag: string | null;
  objetivo: string | null;
}

const AREAS = [
  { id: "ventas", nombre: "Ventas", desc: "Atención al cliente y cierre de ventas" },
  { id: "soporte", nombre: "Soporte Técnico", desc: "Ayuda técnica y troubleshooting" },
  { id: "rrhh", nombre: "RRHH", desc: "Gestión de talento y nóminas" },
  { id: "finanzas", nombre: "Finanzas", desc: "Consultas financieras y facturación" },
  { id: "marketing", nombre: "Marketing", desc: "Promociones y campañas" },
];

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.labodegaec.com";

export default function AgentesPage() {
  const [agentes, setAgentes] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editando, setEditando] = useState<Agent | null>(null);
  const [testModalOpen, setTestModalOpen] = useState(false);
  const [testAgent, setTestAgent] = useState<Agent | null>(null);
  const [testMessage, setTestMessage] = useState("");
  const [testResponse, setTestResponse] = useState("");
  const [testing, setTesting] = useState(false);

  const [formNombre, setFormNombre] = useState("");
  const [formArea, setFormArea] = useState("ventas");
  const [formDescripcion, setFormDescripcion] = useState("");
  const [formGenero, setFormGenero] = useState("femenino");
  const [formHumor, setFormHumor] = useState("profesional");
  const [formObjetivo, setFormObjetivo] = useState("");
  const [formInstrucciones, setFormInstrucciones] = useState("");
  const [formModelo, setFormModelo] = useState("qwen2.5:3b");
  const [formColeccion, setFormColeccion] = useState("");
  const [formCanales, setFormCanales] = useState<string[]>(["web_chat"]);
  const [formHorarioIni, setFormHorarioIni] = useState("08:00");
  const [formHorarioFin, setFormHorarioFin] = useState("20:00");
  const [formMsgFuera, setFormMsgFuera] = useState("");
  const [saving, setSaving] = useState(false);

  const token = typeof window !== "undefined" ? localStorage.getItem("flux_token") : "";

  const loadAgentes = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/agents`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setAgentes(data);
      }
    } catch (e) {
      console.error("Error loading agents:", e);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadAgentes();
  }, [loadAgentes]);

  const filteredAgents = agentes.filter(a => 
    a.nombre.toLowerCase().includes(search.toLowerCase()) ||
    (a.area && a.area.toLowerCase().includes(search.toLowerCase()))
  );

  const openNewModal = () => {
    setEditando(null);
    setFormNombre("");
    setFormArea("ventas");
    setFormDescripcion("");
    setFormGenero("femenino");
    setFormHumor("profesional");
    setFormObjetivo("");
    setFormInstrucciones("");
    setFormModelo("qwen2.5:3b");
    setFormColeccion("");
    setFormCanales(["web_chat"]);
    setFormHorarioIni("08:00");
    setFormHorarioFin("20:00");
    setFormMsgFuera("Gracias por contactarnos. Fuera de nuestro horario, puede dejarnos un mensaje y le responderemos pronto.");
    setModalOpen(true);
  };

  const openEditModal = (agent: Agent) => {
    setEditando(agent);
    setFormNombre(agent.nombre);
    setFormArea(agent.area || "ventas");
    setFormDescripcion(agent.descripcion || "");
    setFormGenero(agent.genero);
    setFormHumor(agent.humor);
    setFormObjetivo(agent.objetivo || "");
    setFormInstrucciones("");
    setFormModelo(agent.modelo);
    setFormColeccion(agent.coleccion_rag || "");
    setFormCanales(agent.canales || ["web_chat"]);
    setFormHorarioIni("08:00");
    setFormHorarioFin("20:00");
    setFormMsgFuera("");
    setModalOpen(true);
  };

  const openTestModal = (agent: Agent) => {
    setTestAgent(agent);
    setTestMessage("");
    setTestResponse("");
    setTestModalOpen(true);
  };

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);

    const payload = {
      nombre: formNombre,
      area: formArea,
      descripcion: formDescripcion,
      genero: formGenero,
      humor: formHumor,
      objetivo: formObjetivo,
      instrucciones: formInstrucciones,
      modelo: formModelo,
      coleccion_rag: formColeccion || null,
      canales: formCanales,
      horario_inicio: formHorarioIni,
      horario_fin: formHorarioFin,
      mensaje_fuera_horario: formMsgFuera,
    };

    try {
      const url = editando 
        ? `${BACKEND_URL}/api/v1/agents/${editando.id}`
        : `${BACKEND_URL}/api/v1/agents`;
      
      const method = editando ? "PATCH" : "POST";

      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Error al guardar");
      }

      toast.success(editando ? "Agente actualizado" : "Agente creado");
      setModalOpen(false);
      loadAgentes();
    } catch (e: any) {
      toast.error("Error", { description: e.message });
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("¿Estás seguro de eliminar este agente?")) return;
    
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/agents/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (!res.ok) throw new Error("Error al eliminar");
      
      toast.success("Agente eliminado");
      loadAgentes();
    } catch (e: any) {
      toast.error("Error", { description: e.message });
    }
  }

  async function handleTest() {
    if (!testAgent || !testMessage.trim()) return;
    setTesting(true);
    
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/agents/${testAgent.id}/test`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ mensaje: testMessage }),
      });
      
      if (!res.ok) throw new Error("Error en la prueba");
      
      const data = await res.json();
      setTestResponse(data.respuesta || "Respuesta recibida");
    } catch (e: any) {
      setTestResponse("Error al procesar: " + e.message);
    } finally {
      setTesting(false);
    }
  }

  const getStatusBadge = (estado: string) => {
    const configs: Record<string, { bg: string; text: string; icon: any }> = {
      activo: { bg: "bg-emerald-500/10", text: "text-emerald-400", icon: CheckCircle },
      entrenando: { bg: "bg-amber-500/10", text: "text-amber-400", icon: Clock },
      pausado: { bg: "bg-slate-500/10", text: "text-slate-400", icon: XCircle },
      archivado: { bg: "bg-red-500/10", text: "text-red-400", icon: AlertTriangle },
    };
    const config = configs[estado] || configs.entrenando;
    const Icon = config.icon;
    
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium ${config.bg} ${config.text}`}>
        <Icon size={12} />
        {estado.charAt(0).toUpperCase() + estado.slice(1)}
      </span>
    );
  };

  return (
    <div className="animate-entry max-w-7xl mx-auto pb-20">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 44, height: 44, borderRadius: 12, background: "var(--primary-light)", display: "flex", alignItems: "center", justifyContent: "center", border: "1px solid var(--primary-mid)" }}>
            <Bot size={22} style={{ color: "var(--primary)" }} />
          </div>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 800, color: "var(--foreground)", margin: "0 0 8px" }}>
              Mis Agentes IA
            </h1>
            <p style={{ fontSize: 14, color: "var(--muted-foreground)", margin: 0 }}>
              Configura múltiples agentes para diferentes áreas de tu negocio
            </p>
          </div>
        </div>
        
        <Button onClick={openNewModal} style={{ background: "var(--primary)", color: "white" }}>
          <Plus size={16} />
          <span style={{ marginLeft: 6 }}>Nuevo agente</span>
        </Button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 16 }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: "center", gridColumn: "1 / -1" }}>
            <Bot size={32} style={{ color: "var(--muted-foreground)", opacity: 0.5, margin: "0 auto 12px" }} />
            <p style={{ color: "var(--muted-foreground)" }}>Cargando agentes...</p>
          </div>
        ) : filteredAgents.length === 0 ? (
          <Card style={{ padding: 40, textAlign: "center", gridColumn: "1 / -1", background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
            <Bot size={48} style={{ color: "var(--muted-foreground)", opacity: 0.5, margin: "0 auto 16px" }} />
            <p style={{ fontSize: 16, fontWeight: 600, color: "var(--foreground)", margin: "0 0 8px" }}>No hay agentes configurados</p>
            <p style={{ fontSize: 13, color: "var(--muted-foreground)", margin: "0 0 20px" }}>Crea tu primer agente IA para automatizar diferentes áreas de tu negocio</p>
            <Button onClick={openNewModal} style={{ background: "var(--primary)", color: "white" }}>
              <Plus size={16} />
              <span style={{ marginLeft: 6 }}>Crear primer agente</span>
            </Button>
          </Card>
        ) : (
          filteredAgents.map((agent) => (
            <Card key={agent.id} style={{ 
              padding: 20, 
              background: "var(--card)", 
              border: "1px solid var(--border)", 
              borderRadius: "var(--radius)" 
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{ 
                    width: 48, height: 48, 
                    borderRadius: 12, 
                    background: "var(--primary-light)", 
                    display: "flex", alignItems: "center", justifyContent: "center" 
                  }}>
                    <Bot size={24} style={{ color: "var(--primary)" }} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: 16, fontWeight: 700, color: "var(--foreground)", margin: "0 0 4px" }}>
                      {agent.nombre}
                    </h3>
                    <p style={{ fontSize: 12, color: "var(--muted-foreground)", margin: 0, textTransform: "capitalize" }}>
                      {agent.area || "Sin área"}
                    </p>
                  </div>
                </div>
                {getStatusBadge(agent.estado)}
              </div>

              {agent.descripcion && (
                <p style={{ fontSize: 13, color: "var(--muted-foreground)", margin: "0 0 16px" }}>
                  {agent.descripcion}
                </p>
              )}

              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 16 }}>
                <Badge style={{ background: "var(--secondary)", color: "var(--foreground)", border: "none" }}>
                  {agent.modelo}
                </Badge>
                {agent.canales?.map((c, i) => (
                  <Badge key={i} style={{ background: "var(--primary-light)", color: "var(--primary)", border: "none" }}>
                    {c}
                  </Badge>
                ))}
              </div>

              <div style={{ display: "flex", gap: 8 }}>
                <Button size="sm" variant="outline" onClick={() => openTestModal(agent)}>
                  <Play size={14} />
                  <span style={{ marginLeft: 4 }}>Probar</span>
                </Button>
                <Button size="sm" variant="outline" onClick={() => openEditModal(agent)}>
                  <Edit3 size={14} />
                </Button>
                <Button size="sm" variant="ghost" onClick={() => handleDelete(agent.id)} className="text-destructive">
                  <Trash2 size={14} />
                </Button>
              </div>
            </Card>
          ))
        )}
      </div>

      {modalOpen && (
        <div style={{
          position: "fixed", inset: 0, zIndex: 50,
          background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center",
          backdropFilter: "blur(4px)",
        }} onClick={() => setModalOpen(false)}>
          <div style={{
            background: "var(--card)", border: "1px solid var(--border)",
            borderRadius: "var(--radius)", padding: 24, width: "100%", maxWidth: 600,
            maxHeight: "90vh", overflowY: "auto",
          }} onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--foreground)", margin: "0 0 20px" }}>
              {editando ? "Editar agente" : "Nuevo agente IA"}
            </h2>
            
            <form onSubmit={handleSubmit}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
                <div>
                  <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Nombre *</label>
                  <Input 
                    value={formNombre} onChange={(e) => setFormNombre(e.target.value)}
                    required placeholder="Ej: Asistente de Ventas"
                    style={{ height: 40 }}
                  />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Área</label>
                  <select 
                    value={formArea} onChange={(e) => setFormArea(e.target.value)}
                    style={{ width: "100%", height: 40, padding: "0 12px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--input)" }}
                  >
                    {AREAS.map(a => <option key={a.id} value={a.id}>{a.nombre}</option>)}
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: 16 }}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Descripción</label>
                <Input 
                  value={formDescripcion} onChange={(e) => setFormDescripcion(e.target.value)}
                  placeholder="Breve descripción del agente"
                  style={{ height: 40 }}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
                <div>
                  <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Género</label>
                  <select 
                    value={formGenero} onChange={(e) => setFormGenero(e.target.value)}
                    style={{ width: "100%", height: 40, padding: "0 12px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--input)" }}
                  >
                    <option value="femenino">Femenino</option>
                    <option value="masculino">Masculino</option>
                    <option value="neutro">Neutro</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Tono</label>
                  <select 
                    value={formHumor} onChange={(e) => setFormHumor(e.target.value)}
                    style={{ width: "100%", height: 40, padding: "0 12px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--input)" }}
                  >
                    <option value="formal">Formal</option>
                    <option value="profesional">Profesional</option>
                    <option value="amigable">Amigable</option>
                    <option value="casual">Casual</option>
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: 16 }}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Objetivo</label>
                <Input 
                  value={formObjetivo} onChange={(e) => setFormObjetivo(e.target.value)}
                  placeholder="Ej: Cerrar ventas y calificar leads"
                  style={{ height: 40 }}
                />
              </div>

              <div style={{ marginBottom: 16 }}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Modelo</label>
                <select 
                  value={formModelo} onChange={(e) => setFormModelo(e.target.value)}
                  style={{ width: "100%", height: 40, padding: "0 12px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--input)" }}
                >
                  <option value="qwen2.5:3b">Qwen 2.5 (3B) - Rápido</option>
                  <option value="llama3:8b">Llama 3 (8B) - Equilibrado</option>
                  <option value="mistral:7b">Mistral (7B) - Mejor calidad</option>
                </select>
              </div>

              <div style={{ display: "flex", gap: 12 }}>
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setModalOpen(false)}
                  style={{ flex: 1 }}
                >
                  Cancelar
                </Button>
                <Button 
                  type="submit" 
                  disabled={saving}
                  style={{ flex: 1, background: "var(--primary)", color: "white" }}
                >
                  {saving ? "Guardando..." : (editando ? "Guardar cambios" : "Crear agente")}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {testModalOpen && (
        <div style={{
          position: "fixed", inset: 0, zIndex: 50,
          background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center",
          backdropFilter: "blur(4px)",
        }} onClick={() => setTestModalOpen(false)}>
          <div style={{
            background: "var(--card)", border: "1px solid var(--border)",
            borderRadius: "var(--radius)", padding: 24, width: "100%", maxWidth: 500,
          }} onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--foreground)", margin: "0 0 16px" }}>
              Probar agente: {testAgent?.nombre}
            </h2>
            
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Tu mensaje</label>
              <textarea 
                value={testMessage} onChange={(e) => setTestMessage(e.target.value)}
                placeholder="Escribe un mensaje de prueba..."
                style={{ 
                  width: "100%", height: 80, padding: 12, borderRadius: 8, 
                  border: "1px solid var(--border)", background: "var(--input)",
                  resize: "none", fontSize: 14
                }}
              />
            </div>

            <Button onClick={handleTest} disabled={testing || !testMessage.trim()} style={{ width: "100%", marginBottom: 16 }}>
              {testing ? "Procesando..." : "Enviar mensaje"}
            </Button>

            {testResponse && (
              <div style={{ 
                padding: 16, background: "var(--secondary)", borderRadius: 8,
                border: "1px solid var(--border)"
              }}>
                <p style={{ fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", margin: "0 0 8px" }}>Respuesta:</p>
                <p style={{ fontSize: 14, color: "var(--foreground)", margin: 0 }}>{testResponse}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}