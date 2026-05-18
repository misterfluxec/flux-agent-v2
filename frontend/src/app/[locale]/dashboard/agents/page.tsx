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
  fetchAgents, createAgent, updateAgent, deleteAgent, testAgent, generateAgentIdentity,
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
  is_active: { dot: "bg-emerald-500", bg: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20", label: "Activo" },
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
    const newStatus = (agent.status === "is_active" || agent.status === "activo") ? "pausado" : "is_active";
    try {
      await updateAgent(agent.id, { status: newStatus } as any);
      setAgents(prev => prev.map(a => a.id === agent.id ? { ...a, status: newStatus } : a));
      toast.success(`${agent.name} ${newStatus === "is_active" ? "activado" : "pausado"}`);
    } catch {
      toast.error("Error al cambiar status");
    }
  };

  const handleDelete = async (agent: AgentResponse) => {
    if (!confirm(`¿Eliminar "${agent.name}"? Esta acción no se puede deshacer.`)) return;
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
          { label: "Activos", value: agents.filter(a => a.status === "is_active" || a.status === "activo").length, color: "text-emerald-400" },
          { label: "Pausados", value: agents.filter(a => a.status === "pausado").length, color: "text-amber-400" },
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
            const sc = STATUS_CONFIG[agent.status] || STATUS_CONFIG.is_active;
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
                        <h3 className="text-sm font-bold text-white">{agent.name}</h3>
                        <p className="text-[11px] text-white/40">{tc.label} · {agent.model}</p>
                      </div>
                    </div>
                    <span className={`text-[10px] font-bold px-2 py-1 rounded-lg border ${sc.bg} flex items-center gap-1.5`}>
                      <span className={`h-1.5 w-1.5 rounded-full ${sc.dot}`} />
                      {sc.label}
                    </span>
                  </div>

                  {/* Description */}
                  <p className="text-xs text-white/30 line-clamp-2 min-h-[2rem]">
                    {agent.description || agent.specialty || tc.desc}
                  </p>

                  {/* Meta chips */}
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {agent.channels?.map(ch => (
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
                    {(agent.status === "is_active" || agent.status === "activo") ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
                    {(agent.status === "is_active" || agent.status === "activo") ? "Pausar" : "Activar"}
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
// CREATE AGENT MODAL — Premium Wizard
// =============================================================================
import { motion, AnimatePresence } from 'framer-motion';
import { ScanLine, UploadCloud, Rocket, BrainCircuit, MessageCircle, Smile, SmilePlus, Network } from 'lucide-react';
import { uploadDocument } from '@/lib/api';

const PREDEFINED_AVATARS = [
  { id: 'man', label: 'Él', icon: Smile, color: 'text-blue-400', glow: 'shadow-[0_0_30px_rgba(59,130,246,0.3)]', gradient: 'from-blue-500/20 to-cyan-500/10' },
  { id: 'woman', label: 'Ella', icon: SmilePlus, color: 'text-pink-400', glow: 'shadow-[0_0_30px_rgba(236,72,153,0.3)]', gradient: 'from-pink-500/20 to-purple-500/10' },
  { id: 'agent', label: 'Agente', icon: Bot, color: 'text-emerald-400', glow: 'shadow-[0_0_30px_rgba(16,185,129,0.3)]', gradient: 'from-emerald-500/20 to-teal-500/10' },
];

const INDUSTRIES = [
  { id: 'seguridad', label: 'Seguridad' },
  { id: 'restaurante', label: 'Restaurante' },
  { id: 'ecommerce', label: 'Ecommerce' },
  { id: 'clinica', label: 'Clínica' },
  { id: 'servicios', label: 'Servicios' },
  { id: 'automotriz', label: 'Automotriz' },
  { id: 'retail', label: 'Retail' },
  { id: 'tecnologia', label: 'Tecnología' },
];

function CreateAgentModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [agentId, setAgentId] = useState<string | null>(null);

  // Form States
  const [name, setName] = useState('');
  const [avatar, setAvatar] = useState('agent');
  const [industry, setIndustry] = useState('');
  
  // Magic Prompt States
  const [businessDesc, setBusinessDesc] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  
  // Knowledge States
  const [file, setFile] = useState<File | null>(null);
  
  // Channel States
  const [channel, setChannel] = useState<'whatsapp' | 'web' | 'api'>('web');
  
  // Test Chat
  const [testMessage, setTestMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<{ role: 'user' | 'assistant'; content: string }[]>([]);

  const handleMagicPrompt = async () => {
    if (!businessDesc) {
      toast.error('Agrega una breve descripción de tu negocio.');
      return;
    }
    setIsSynthesizing(true);
    // Simulating endpoint delay for MVP
    setTimeout(() => {
      setSystemPrompt(`Eres ${name || 'un experto'}, un asistente especializado en ${industry || 'servicios'} para la empresa. 
Misión: ${businessDesc}
Tono: Amigable, persuasivo y profesional.
Reglas:
1. Responde de manera concisa.
2. Orienta al usuario a agendar o comprar.
3. No inventes información fuera del catálogo.`);
      setIsSynthesizing(false);
      toast.success('Prompt Mágico generado con éxito.');
    }, 3000);
  };

  const handleNext = async () => {
    if (step === 1 && name.trim().length < 2) {
      toast.error('Por favor, ingresa un nombre para tu agente');
      return;
    }
    if (step === 2 && !industry) {
      toast.error('Selecciona una industria.');
      return;
    }

    if (step === 3) {
      if (!systemPrompt) {
        toast.error('Genera o escribe las reglas de negocio (Prompt) antes de continuar.');
        return;
      }
      setSaving(true);
      try {
        const payload: AgentCreate = {
          name: name,
          agent_type: 'custom',
          business_type: industry,
          mood: 'profesional',
          tone: 'amigable',
          gender: avatar === 'woman' ? 'femenino' : 'masculino',
          personality: systemPrompt,
          model: 'qwen2.5:3b',
          temperature: 0.7,
          max_tokens: 512,
          channels: ['web_chat'],
        };
        const result = await createAgent(payload);
        setAgentId(result.agente_id);
        
        localStorage.setItem('flux_agent_id', result.agente_id);
        localStorage.setItem('flux_agent_nombre', name);
        setStep(4);
      } catch (error: any) {
        toast.error('Error al crear el agente en el backend.');
      } finally {
        setSaving(false);
      }
      return;
    }

    if (step === 4) {
      if (file && agentId) {
        setSaving(true);
        try {
          await uploadDocument(file, agentId);
          toast.success('Conocimiento ingerido.');
        } catch (error) {
          toast.error('Error al cargar archivo.');
        } finally {
          setSaving(false);
        }
      }
      setStep(5);
      return;
    }

    if (step === 5) {
      setStep(6);
      return;
    }

    if (step === 6) {
      onCreated();
    } else {
      setStep(step + 1);
    }
  };

  const handleSendMessage = async () => {
    if (!testMessage || !agentId) return;
    
    const newMsg = { role: 'user' as const, content: testMessage };
    setChatHistory([...chatHistory, newMsg]);
    setTestMessage('');
    setSaving(true);

    try {
      const response = await testAgent(agentId, testMessage);
      setChatHistory(prev => [...prev, { role: 'assistant', content: response.respuesta }]);
    } catch (error: any) {
      toast.error(`Error de conexión.`);
      setChatHistory(prev => [...prev, { role: 'assistant', content: 'Lo siento, tuve un problema técnico. Intenta de nuevo.' }]);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-xl animate-in fade-in duration-300">
      <motion.div 
        initial={{ scale: 0.95, y: 20, opacity: 0 }} animate={{ scale: 1, y: 0, opacity: 1 }} transition={{ type: 'spring', damping: 25 }}
        className="relative w-full max-w-3xl rounded-[2rem] border border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.8)] flex flex-col max-h-[90vh] bg-[#0A0A0B] overflow-hidden"
      >
        {/* Header */}
        <div className="px-8 py-6 border-b border-white/5 flex items-center justify-between bg-white/[0.02] backdrop-blur-md relative z-20">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 flex items-center justify-center border border-cyan-500/20 shadow-[0_0_15px_rgba(6,182,212,0.15)]">
              <Sparkles className="w-6 h-6 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white to-white/60 tracking-tight">
                Génesis del Agente
              </h2>
              <div className="flex items-center gap-1.5 mt-1.5">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div 
                    key={i} 
                    className={`h-1 rounded-full transition-all duration-500 ${
                      i === step ? 'w-8 bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]' : i < step ? 'w-4 bg-cyan-500/40' : 'w-2 bg-white/10'
                    }`} 
                  />
                ))}
                <span className="text-[9px] text-cyan-400 ml-3 font-black uppercase tracking-[0.2em]">Fase {step} de 6</span>
              </div>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-2.5 rounded-full text-white/30 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X size={20} strokeWidth={2.5} />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-8 relative z-10 custom-scrollbar">
          <AnimatePresence mode="wait">
            
            {/* STEP 1: Entidad */}
            {step === 1 && (
              <motion.div key="step1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-10">
                <div className="text-center space-y-2">
                  <h3 className="text-2xl font-bold text-white tracking-tight">Forma Física Virtual</h3>
                  <p className="text-white/40 text-sm">Define el avatar y el identificador de tu sistema.</p>
                </div>
                
                <div className="flex justify-center gap-6">
                  {PREDEFINED_AVATARS.map((av) => {
                    const Icon = av.icon;
                    const isSelected = avatar === av.id;
                    return (
                      <motion.button
                        key={av.id}
                        onClick={() => setAvatar(av.id)}
                        whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                        className="flex flex-col items-center group outline-none"
                      >
                        <div className={`relative w-20 h-20 rounded-full border flex items-center justify-center transition-all duration-500 ${
                          isSelected ? `border-white/40 bg-gradient-to-br ${av.gradient} ${av.glow}` : 'border-white/5 bg-white/[0.02] hover:border-white/20'
                        }`}>
                          <Icon className={`w-10 h-10 transition-colors ${isSelected ? av.color : 'text-white/20'}`} strokeWidth={1.5} />
                        </div>
                        <span className={`mt-4 text-[10px] font-black uppercase tracking-[0.2em] transition-colors ${isSelected ? 'text-white' : 'text-white/30'}`}>
                          {av.label}
                        </span>
                      </motion.button>
                    )
                  })}
                </div>
                
                <div className="max-w-sm mx-auto pt-4 relative group">
                  <label className="absolute -top-2 left-4 px-2 bg-[#0A0A0B] text-[9px] font-black text-cyan-400 uppercase tracking-[0.2em] z-10">
                    Nombre del Agente
                  </label>
                  <input 
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Ej: Sofia"
                    className="w-full h-14 rounded-2xl bg-white/[0.02] border border-white/10 text-white text-center text-sm font-semibold focus:outline-none focus:border-cyan-500/50 focus:bg-cyan-500/[0.02] transition-all placeholder:text-white/20"
                  />
                </div>
              </motion.div>
            )}

            {/* STEP 2: Industria */}
            {step === 2 && (
              <motion.div key="step2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-10">
                <div className="text-center space-y-2">
                  <h3 className="text-2xl font-bold text-white tracking-tight">Dominio Operativo</h3>
                  <p className="text-white/40 text-sm">Selecciona la industria para pre-cargar los modelos base.</p>
                </div>
                
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  {INDUSTRIES.map(ind => (
                    <motion.button 
                      key={ind.id}
                      onClick={() => setIndustry(ind.id)}
                      whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                      className={`p-4 rounded-2xl border transition-all duration-300 text-center ${
                        industry === ind.id ? 'border-cyan-500/50 bg-cyan-500/10 shadow-[0_0_20px_rgba(6,182,212,0.15)] text-cyan-400' : 'border-white/5 bg-white/[0.02] text-white/50 hover:bg-white/5 hover:text-white'
                      }`}
                    >
                      <span className="text-xs font-bold uppercase tracking-[0.1em]">{ind.label}</span>
                    </motion.button>
                  ))}
                </div>
              </motion.div>
            )}

            {/* STEP 3: Magic Prompt */}
            {step === 3 && (
              <motion.div key="step3" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-8">
                <div className="text-center space-y-2">
                  <h3 className="text-2xl font-bold text-white tracking-tight">Cerebro Mágico</h3>
                  <p className="text-white/40 text-sm">Describe tu negocio y la IA sintetizará las reglas operativas perfectas.</p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <label className="text-[10px] font-black text-white/50 uppercase tracking-[0.2em] ml-2">¿De qué trata tu negocio?</label>
                    <textarea 
                      value={businessDesc}
                      onChange={(e) => setBusinessDesc(e.target.value)}
                      placeholder="Ej: Somos una clínica dental enfocada en ortodoncia. Queremos que el agente agende citas y resuelva dudas de precios..."
                      className="w-full h-40 bg-white/[0.02] border border-white/10 rounded-2xl p-4 text-sm text-white resize-none outline-none focus:border-purple-500/50 focus:bg-purple-500/[0.02] transition-all placeholder:text-white/20"
                    />
                    <Button 
                      onClick={handleMagicPrompt}
                      disabled={isSynthesizing || !businessDesc}
                      className="w-full h-12 bg-purple-600 hover:bg-purple-500 text-white font-black uppercase tracking-[0.1em] text-[11px] rounded-xl relative overflow-hidden group"
                    >
                      {isSynthesizing ? (
                        <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Sintetizando...</>
                      ) : (
                        <><BrainCircuit className="w-4 h-4 mr-2" /> Generar Reglas Mágicas ✨</>
                      )}
                    </Button>
                  </div>
                  <div className="space-y-4">
                    <label className="text-[10px] font-black text-cyan-400 uppercase tracking-[0.2em] ml-2 flex items-center gap-2">
                      <Sparkles className="w-3 h-3" /> System Prompt Generado
                    </label>
                    <textarea 
                      value={systemPrompt}
                      onChange={(e) => setSystemPrompt(e.target.value)}
                      placeholder="Las reglas generadas aparecerán aquí y podrás editarlas antes de continuar..."
                      className="w-full h-full min-h-[220px] bg-black/50 border border-cyan-500/20 rounded-2xl p-4 text-xs font-mono text-cyan-400/90 resize-none outline-none focus:border-cyan-500 transition-all"
                    />
                  </div>
                </div>
              </motion.div>
            )}

            {/* STEP 4: Knowledge */}
            {step === 4 && (
              <motion.div key="step4" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-8">
                <div className="text-center space-y-2">
                  <h3 className="text-2xl font-bold text-white tracking-tight">Portal de Ingesta</h3>
                  <p className="text-white/40 text-sm">Sube tu catálogo, PDF de productos o lista de precios.</p>
                </div>

                <div 
                  className="max-w-md mx-auto p-12 border border-dashed border-white/20 rounded-[2rem] bg-white/[0.01] hover:border-cyan-500/50 hover:bg-cyan-500/[0.02] transition-all text-center group relative overflow-hidden"
                >
                  <ScanLine className="w-12 h-12 mx-auto text-white/20 group-hover:text-cyan-400 transition-colors mb-4" />
                  <p className="text-white font-bold tracking-wide">{file ? file.name : 'Click para subir archivo'}</p>
                  <p className="text-[10px] text-white/30 uppercase tracking-widest mt-2">PDF, XLSX o CSV hasta 50MB</p>
                  <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} className="absolute inset-0 opacity-0 cursor-pointer" />
                </div>
              </motion.div>
            )}

            {/* STEP 5: Canales */}
            {step === 5 && (
              <motion.div key="step5" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-8">
                <div className="text-center space-y-2">
                  <h3 className="text-2xl font-bold text-white tracking-tight">Nodos de Transmisión</h3>
                  <p className="text-white/40 text-sm">Selecciona dónde se desplegará el agente en el MVP.</p>
                </div>

                <div className="grid gap-4 max-w-lg mx-auto">
                  {[
                    { id: 'web', title: 'Widget Web (Prueba Mágica)', icon: Globe, color: 'text-cyan-400' },
                    { id: 'whatsapp', title: 'WhatsApp Business', icon: MessageCircle, color: 'text-green-400' },
                  ].map(item => (
                    <button 
                      key={item.id}
                      onClick={() => setChannel(item.id as any)}
                      className={`p-5 rounded-2xl border transition-all text-left flex items-center gap-4 ${
                        channel === item.id ? 'border-cyan-500/40 bg-cyan-500/10 shadow-[0_0_20px_rgba(6,182,212,0.15)]' : 'border-white/10 bg-white/[0.02] hover:border-white/20'
                      }`}
                    >
                      <div className={`p-3 rounded-xl bg-black/40 border border-white/5 ${item.color}`}>
                        <item.icon size={24} />
                      </div>
                      <h4 className="font-bold text-white tracking-wide">{item.title}</h4>
                      {channel === item.id && <Check className="ml-auto text-cyan-400" />}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {/* STEP 6: Chat de Prueba */}
            {step === 6 && (
              <motion.div key="step6" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="flex flex-col h-full space-y-6">
                <div className="text-center space-y-2">
                  <h3 className="text-2xl font-bold text-white tracking-tight">Secuencia Activa 🚀</h3>
                  <p className="text-white/40 text-sm">Tu agente {name} está vivo. Envíale un mensaje de prueba.</p>
                </div>

                <div className="flex-1 bg-black/50 rounded-[2rem] border border-white/10 flex flex-col p-6 min-h-[350px]">
                  <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2 custom-scrollbar">
                    {chatHistory.length === 0 && (
                      <div className="h-full flex items-center justify-center">
                        <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white/20 border border-white/5 px-4 py-2 rounded-full">
                          A la espera de comandos
                        </span>
                      </div>
                    )}
                    {chatHistory.map((m, i) => (
                      <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] p-4 text-sm font-medium leading-relaxed ${
                          m.role === 'user' 
                            ? 'bg-cyan-600 text-white rounded-2xl rounded-tr-sm shadow-[0_5px_15px_rgba(6,182,212,0.2)]' 
                            : 'bg-white/10 text-white/90 rounded-2xl rounded-tl-sm border border-white/5 backdrop-blur-md'
                        }`}>
                          {m.content}
                        </div>
                      </div>
                    ))}
                    {saving && (
                      <div className="flex justify-start">
                        <div className="bg-white/5 border border-white/5 p-4 rounded-2xl rounded-tl-sm backdrop-blur-md">
                          <Loader2 size={16} className="animate-spin text-cyan-400" />
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div className="relative">
                    <input 
                      value={testMessage}
                      onChange={(e) => setTestMessage(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                      placeholder="Pregúntale algo sobre el negocio..."
                      className="w-full h-14 pr-14 pl-4 rounded-2xl bg-white/[0.03] border border-white/10 text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-500/50 focus:bg-cyan-500/[0.02]"
                    />
                    <button 
                      onClick={handleSendMessage}
                      disabled={saving || !testMessage}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-2.5 bg-cyan-500 rounded-xl text-black hover:bg-cyan-400 disabled:opacity-30 disabled:bg-white/10 disabled:text-white transition-colors shadow-[0_0_15px_rgba(6,182,212,0.3)]"
                    >
                      <Rocket size={18} />
                    </button>
                  </div>
                </div>
              </motion.div>
            )}

          </AnimatePresence>
        </div>

        {/* Footer Actions */}
        <div className="px-8 py-6 border-t border-white/5 flex items-center justify-between bg-white/[0.01] relative z-20">
          <Button 
            variant="ghost" 
            onClick={() => step > 1 ? setStep(step - 1) : onClose()}
            disabled={saving}
            className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 hover:text-white hover:bg-transparent"
          >
            {step > 1 ? "Atrás" : "Cancelar"}
          </Button>
          
          <Button 
            onClick={handleNext}
            disabled={saving}
            variant="outline"
            className="h-12 px-8 rounded-full border-cyan-500/40 text-cyan-400 hover:bg-cyan-500/10 text-[11px] font-black uppercase tracking-[0.2em] backdrop-blur-md transition-all shadow-[0_0_20px_rgba(6,182,212,0.15)] group relative overflow-hidden"
          >
            <span className="relative z-10 flex items-center">
              {saving ? (
                <><Loader2 size={14} className="mr-2 animate-spin" /> Procesando...</>
              ) : step === 6 ? (
                <>Cerrar y Usar <Check size={14} className="ml-2" /></>
              ) : (
                <>Siguiente Fase <ChevronRight size={14} className="ml-1 group-hover:translate-x-1 transition-transform" /></>
              )}
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/0 via-cyan-500/10 to-cyan-500/0 -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]" />
          </Button>
        </div>
      </motion.div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
      `}</style>
    </div>
  );
}

