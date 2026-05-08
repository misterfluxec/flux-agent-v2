"use client";

import { useState, useEffect } from "react";
import {
  Users2, Plus, Bot, Headphones, Calendar, Sparkles, Play, Pause,
  Trash2, Settings2, Loader2, MessageSquare, Brain, ChevronRight,
  Mic, Globe, ShoppingBag, X, Check, TestTube,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import {
  fetchAgents, createAgent, updateAgent, deleteAgent, testAgent,
  AgentResponse, AgentCreate,
} from "@/lib/api";

// =============================================================================
// CONFIG
// =============================================================================

const AGENT_TYPES = [
  { value: "sales", label: "Ventas", icon: ShoppingBag, color: "cyan", desc: "Califica leads y cierra ventas" },
  { value: "support", label: "Soporte", icon: Headphones, color: "emerald", desc: "Resuelve problemas y tickets" },
  { value: "bookings", label: "Reservas", icon: Calendar, color: "amber", desc: "Gestiona citas y agendas" },
  { value: "custom", label: "Custom", icon: Sparkles, color: "purple", desc: "Agente personalizado" },
];

const MODELS = [
  { value: "qwen2.5:3b", label: "Qwen 2.5 3B", speed: "Rápido" },
  { value: "qwen2.5:7b", label: "Qwen 2.5 7B", speed: "Balanceado" },
  { value: "llama3.1:8b", label: "Llama 3.1 8B", speed: "Preciso" },
];

const STATUS_CONFIG: Record<string, { dot: string; bg: string; label: string }> = {
  activo: { dot: "bg-emerald-500", bg: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20", label: "Activo" },
  pausado: { dot: "bg-amber-500", bg: "bg-amber-500/10 text-amber-400 border-amber-500/20", label: "Pausado" },
  entrenando: { dot: "bg-blue-500", bg: "bg-blue-500/10 text-blue-400 border-blue-500/20", label: "Entrenando" },
  archivado: { dot: "bg-white/20", bg: "bg-white/5 text-white/40 border-white/10", label: "Archivado" },
};

// =============================================================================
// MAIN PAGE
// =============================================================================

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [testInput, setTestInput] = useState("");
  const [testResult, setTestResult] = useState<string | null>(null);
  const [testLoading, setTestLoading] = useState(false);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const data = await fetchAgents();
      setAgents(data);
    } catch {
      toast.error("Error al cargar agentes");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAgents(); }, []);

  const handleToggleStatus = async (agent: AgentResponse) => {
    const newStatus = agent.estado === "activo" ? "pausado" : "activo";
    try {
      await updateAgent(agent.id, { estado: newStatus } as any);
      setAgents(prev => prev.map(a => a.id === agent.id ? { ...a, estado: newStatus } : a));
      toast.success(`${agent.nombre} ${newStatus === "activo" ? "activado" : "pausado"}`);
    } catch {
      toast.error("Error al cambiar estado");
    }
  };

  const handleDelete = async (agent: AgentResponse) => {
    if (!confirm(`¿Eliminar "${agent.nombre}"? Esta acción no se puede deshacer.`)) return;
    try {
      await deleteAgent(agent.id);
      setAgents(prev => prev.filter(a => a.id !== agent.id));
      toast.success("Agente eliminado");
    } catch {
      toast.error("Error al eliminar");
    }
  };

  const handleTest = async (agentId: string) => {
    if (!testInput.trim()) return;
    setTestLoading(true);
    setTestResult(null);
    try {
      const res = await testAgent(agentId, testInput);
      setTestResult(res.respuesta);
    } catch {
      setTestResult("Error al probar el agente. Verifica que el motor IA esté operativo.");
    } finally {
      setTestLoading(false);
    }
  };

  const typeConfig = (type: string) => AGENT_TYPES.find(t => t.value === type) || AGENT_TYPES[3];

  return (
    <div className="space-y-6 animate-in fade-in duration-700 pb-12 px-4 md:px-8 max-w-7xl mx-auto pt-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white/90">Agentes IA</h1>
          <p className="text-white/40 text-sm mt-1">Tu workforce digital — Crea, configura y supervisa cada agente.</p>
        </div>
        <Button
          onClick={() => setShowCreate(true)}
          className="bg-cyan-500 hover:bg-cyan-600 text-black font-bold rounded-xl px-5 gap-2"
        >
          <Plus className="h-4 w-4" /> Nuevo Agente
        </Button>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: "Total", value: agents.length, color: "text-white" },
          { label: "Activos", value: agents.filter(a => a.estado === "activo").length, color: "text-emerald-400" },
          { label: "Pausados", value: agents.filter(a => a.estado === "pausado").length, color: "text-amber-400" },
          { label: "Conocimiento", value: agents.reduce((s, a) => s + (a.knowledge_base_size || 0), 0) + " chunks", color: "text-cyan-400" },
        ].map(s => (
          <div key={s.label} className="bg-white/[0.03] border border-white/5 rounded-xl px-4 py-3">
            <p className="text-[10px] font-bold uppercase tracking-wider text-white/30">{s.label}</p>
            <p className={`text-xl font-black ${s.color} mt-1`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Agent Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="bg-white/[0.03] border border-white/5 rounded-2xl h-64 animate-pulse" />
          ))}
        </div>
      ) : agents.length === 0 ? (
        <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-16 text-center">
          <Bot className="h-12 w-12 text-white/10 mx-auto mb-4" />
          <h3 className="text-lg font-bold text-white/60">Sin agentes configurados</h3>
          <p className="text-sm text-white/30 mt-2 max-w-md mx-auto">
            Crea tu primer agente IA para comenzar a automatizar tu operación comercial.
          </p>
          <Button onClick={() => setShowCreate(true)} className="mt-6 bg-cyan-500 hover:bg-cyan-600 text-black font-bold rounded-xl gap-2">
            <Plus className="h-4 w-4" /> Crear Primer Agente
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map(agent => {
            const tc = typeConfig(agent.agent_type);
            const TypeIcon = tc.icon;
            const sc = STATUS_CONFIG[agent.estado] || STATUS_CONFIG.activo;
            const isTesting = testingId === agent.id;

            return (
              <div key={agent.id} className="bg-black/40 backdrop-blur-xl border border-white/5 rounded-2xl overflow-hidden group hover:border-white/10 transition-all duration-300">
                {/* Card Header */}
                <div className="p-5 pb-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className={`h-11 w-11 rounded-xl bg-${tc.color}-500/10 border border-${tc.color}-500/20 flex items-center justify-center`}
                        style={{ backgroundColor: `var(--${tc.color}-bg, rgba(6,182,212,0.1))` }}>
                        <TypeIcon className="h-5 w-5 text-cyan-400" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white">{agent.nombre}</h3>
                        <p className="text-[11px] text-white/40">{tc.label} · {agent.modelo}</p>
                      </div>
                    </div>
                    <span className={`text-[10px] font-bold px-2 py-1 rounded-lg border ${sc.bg} flex items-center gap-1.5`}>
                      <span className={`h-1.5 w-1.5 rounded-full ${sc.dot}`} />
                      {sc.label}
                    </span>
                  </div>

                  {/* Description */}
                  <p className="text-xs text-white/30 line-clamp-2 min-h-[2rem]">
                    {agent.descripcion || agent.specialty || tc.desc}
                  </p>

                  {/* Meta chips */}
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {agent.canales?.map(ch => (
                      <span key={ch} className="text-[10px] px-2 py-0.5 rounded-md bg-white/5 text-white/40 font-medium">
                        {ch === "web_chat" ? "Web" : ch === "whatsapp" ? "WhatsApp" : ch}
                      </span>
                    ))}
                    {(agent.knowledge_base_size || 0) > 0 && (
                      <span className="text-[10px] px-2 py-0.5 rounded-md bg-cyan-500/10 text-cyan-400/70 font-medium flex items-center gap-1">
                        <Brain className="h-2.5 w-2.5" /> {agent.knowledge_base_size} chunks
                      </span>
                    )}
                  </div>
                </div>

                {/* Test Area */}
                {isTesting && (
                  <div className="px-5 pb-4 border-t border-white/5 pt-3 animate-in fade-in duration-200">
                    <div className="flex gap-2">
                      <input
                        value={testInput}
                        onChange={e => setTestInput(e.target.value)}
                        onKeyDown={e => e.key === "Enter" && handleTest(agent.id)}
                        placeholder="Escribe un mensaje de prueba..."
                        className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-500/30"
                      />
                      <Button size="sm" onClick={() => handleTest(agent.id)} disabled={testLoading} className="bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30 rounded-lg h-8 px-3">
                        {testLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <ChevronRight className="h-3 w-3" />}
                      </Button>
                    </div>
                    {testResult && (
                      <div className="mt-2 p-3 bg-white/[0.03] rounded-lg text-xs text-white/60 max-h-24 overflow-y-auto">
                        {testResult}
                      </div>
                    )}
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center border-t border-white/5 divide-x divide-white/5">
                  <button
                    onClick={() => handleToggleStatus(agent)}
                    className="flex-1 flex items-center justify-center gap-1.5 py-3 text-[11px] font-bold text-white/40 hover:text-white/80 hover:bg-white/[0.03] transition-colors"
                  >
                    {agent.estado === "activo" ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
                    {agent.estado === "activo" ? "Pausar" : "Activar"}
                  </button>
                  <button
                    onClick={() => { setTestingId(isTesting ? null : agent.id); setTestResult(null); setTestInput(""); }}
                    className="flex-1 flex items-center justify-center gap-1.5 py-3 text-[11px] font-bold text-white/40 hover:text-cyan-400 hover:bg-cyan-500/5 transition-colors"
                  >
                    <TestTube className="h-3.5 w-3.5" /> Probar
                  </button>
                  <button
                    onClick={() => handleDelete(agent)}
                    className="px-4 flex items-center justify-center py-3 text-white/20 hover:text-red-400 hover:bg-red-500/5 transition-colors"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <CreateAgentModal
          onClose={() => setShowCreate(false)}
          onCreated={() => { setShowCreate(false); loadAgents(); }}
        />
      )}
    </div>
  );
}

// =============================================================================
// CREATE AGENT MODAL — Wizard 3 pasos
// =============================================================================

function CreateAgentModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    nombre: "",
    agent_type: "sales",
    specialty: "",
    tono: "profesional",
    idioma: "Español (Ecuador)",
    modelo: "qwen2.5:3b",
    canales: ["web_chat"],
    instrucciones: "",
  });

  const handleCreate = async () => {
    if (!form.nombre.trim()) { toast.error("Nombre es requerido"); return; }
    setSaving(true);
    try {
      const payload: AgentCreate = {
        nombre: form.nombre,
        agent_type: form.agent_type,
        specialty: form.specialty || undefined,
        tono: form.tono,
        idioma: form.idioma,
        modelo: form.modelo,
        canales: form.canales,
        instrucciones: form.instrucciones || undefined,
        humor: form.tono,
      };
      await createAgent(payload);
      toast.success(`Agente "${form.nombre}" creado exitosamente`);
      onCreated();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Error al crear agente");
    } finally {
      setSaving(false);
    }
  };

  const tc = AGENT_TYPES.find(t => t.value === form.agent_type) || AGENT_TYPES[0];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#111113] border border-white/10 rounded-3xl w-full max-w-lg mx-4 overflow-hidden shadow-2xl">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
          <div>
            <h2 className="text-lg font-black text-white">Nuevo Agente IA</h2>
            <p className="text-xs text-white/30 mt-0.5">Paso {step} de 3</p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-white/5 text-white/30 hover:text-white/60 transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Progress */}
        <div className="flex gap-1 px-6 pt-4">
          {[1, 2, 3].map(s => (
            <div key={s} className={`h-1 flex-1 rounded-full transition-colors ${s <= step ? "bg-cyan-500" : "bg-white/5"}`} />
          ))}
        </div>

        <div className="p-6 space-y-5 min-h-[300px]">
          {/* STEP 1: Type */}
          {step === 1 && (
            <div className="space-y-4 animate-in fade-in slide-in-from-right-2 duration-300">
              <div>
                <label className="text-sm font-bold text-white/60 mb-3 block">¿Qué tipo de agente necesitas?</label>
                <div className="grid grid-cols-2 gap-3">
                  {AGENT_TYPES.map(t => {
                    const Icon = t.icon;
                    const selected = form.agent_type === t.value;
                    return (
                      <button
                        key={t.value}
                        onClick={() => setForm(f => ({ ...f, agent_type: t.value }))}
                        className={`p-4 rounded-xl border text-left transition-all ${
                          selected
                            ? "bg-cyan-500/10 border-cyan-500/30 ring-1 ring-cyan-500/20"
                            : "bg-white/[0.02] border-white/5 hover:border-white/10"
                        }`}
                      >
                        <Icon className={`h-5 w-5 mb-2 ${selected ? "text-cyan-400" : "text-white/30"}`} />
                        <p className={`text-sm font-bold ${selected ? "text-white" : "text-white/60"}`}>{t.label}</p>
                        <p className="text-[11px] text-white/30 mt-0.5">{t.desc}</p>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: Identity */}
          {step === 2 && (
            <div className="space-y-4 animate-in fade-in slide-in-from-right-2 duration-300">
              <div>
                <label className="text-xs font-bold text-white/40 mb-1.5 block">Nombre del agente</label>
                <input value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))}
                  placeholder="Ej: Sofia, Max, Luna..."
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-500/40" />
              </div>
              <div>
                <label className="text-xs font-bold text-white/40 mb-1.5 block">Especialidad</label>
                <input value={form.specialty} onChange={e => setForm(f => ({ ...f, specialty: e.target.value }))}
                  placeholder={`Ej: ${tc.value === "sales" ? "Ventas de tecnología" : tc.value === "support" ? "Soporte técnico L1" : tc.value === "bookings" ? "Reservas médicas" : "Asistente general"}`}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-500/40" />
              </div>
              <div>
                <label className="text-xs font-bold text-white/40 mb-1.5 block">Tono de comunicación</label>
                <div className="flex gap-2 flex-wrap">
                  {["profesional", "amigable", "casual", "energético"].map(t => (
                    <button key={t} onClick={() => setForm(f => ({ ...f, tono: t }))}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-all ${
                        form.tono === t ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400" : "bg-white/[0.02] border-white/5 text-white/40 hover:text-white/60"
                      }`}>
                      {t.charAt(0).toUpperCase() + t.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-xs font-bold text-white/40 mb-1.5 block">Modelo IA</label>
                <div className="flex gap-2 flex-wrap">
                  {MODELS.map(m => (
                    <button key={m.value} onClick={() => setForm(f => ({ ...f, modelo: m.value }))}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-all ${
                        form.modelo === m.value ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400" : "bg-white/[0.02] border-white/5 text-white/40 hover:text-white/60"
                      }`}>
                      {m.label} <span className="text-white/20 ml-1">· {m.speed}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: Channels */}
          {step === 3 && (
            <div className="space-y-4 animate-in fade-in slide-in-from-right-2 duration-300">
              <div>
                <label className="text-xs font-bold text-white/40 mb-2 block">Canales de operación</label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { id: "web_chat", label: "Web Chat", icon: Globe },
                    { id: "whatsapp", label: "WhatsApp", icon: MessageSquare },
                    { id: "telegram", label: "Telegram", icon: MessageSquare },
                    { id: "voice", label: "Voz", icon: Mic },
                  ].map(ch => {
                    const Icon = ch.icon;
                    const selected = form.canales.includes(ch.id);
                    return (
                      <button key={ch.id}
                        onClick={() => setForm(f => ({
                          ...f,
                          canales: selected ? f.canales.filter(c => c !== ch.id) : [...f.canales, ch.id],
                        }))}
                        className={`flex items-center gap-2.5 p-3 rounded-xl border transition-all ${
                          selected ? "bg-cyan-500/10 border-cyan-500/30" : "bg-white/[0.02] border-white/5 hover:border-white/10"
                        }`}>
                        <Icon className={`h-4 w-4 ${selected ? "text-cyan-400" : "text-white/30"}`} />
                        <span className={`text-sm font-medium ${selected ? "text-white" : "text-white/50"}`}>{ch.label}</span>
                        {selected && <Check className="h-3 w-3 text-cyan-400 ml-auto" />}
                      </button>
                    );
                  })}
                </div>
              </div>
              <div>
                <label className="text-xs font-bold text-white/40 mb-1.5 block">Instrucciones personalizadas (opcional)</label>
                <textarea value={form.instrucciones} onChange={e => setForm(f => ({ ...f, instrucciones: e.target.value }))}
                  rows={3} placeholder="Ej: Siempre ofrece el producto premium primero..."
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-500/40 resize-none" />
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-white/5 bg-black/40">
          <Button variant="ghost" onClick={() => step > 1 ? setStep(s => s - 1) : onClose()}
            className="text-white/40 hover:text-white/70">
            {step > 1 ? "Anterior" : "Cancelar"}
          </Button>
          {step < 3 ? (
            <Button onClick={() => setStep(s => s + 1)}
              className="bg-cyan-500 hover:bg-cyan-600 text-black font-bold rounded-xl px-6 gap-1">
              Siguiente <ChevronRight className="h-4 w-4" />
            </Button>
          ) : (
            <Button onClick={handleCreate} disabled={saving || !form.nombre.trim()}
              className="bg-cyan-500 hover:bg-cyan-600 text-black font-bold rounded-xl px-6 gap-2">
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              Crear Agente
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
