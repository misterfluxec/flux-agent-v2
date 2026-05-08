"use client";

import { useState, useEffect, useRef } from "react";
import {
  User, Save, ImageIcon, Mic, MessageSquare, Building, Sparkles,
  ChevronRight, Check, AlertCircle, Bot, Briefcase, RotateCcw, Loader2,
  CheckCircle2, ArrowRight, Activity, Book, Store, ShoppingCart, ShoppingBag,
  DollarSign, Home, Car, Laptop, Plane, Utensils, UserRound
} from "lucide-react";
import { useParams, useRouter } from 'next/navigation';
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { AvatarSelector } from "./components/AvatarSelector";

// Industry types
const industries = [
  { value: 'healthcare', label: 'Salud', icon: Activity },
  { value: 'education', label: 'Educación', icon: Book },
  { value: 'b2b', label: 'B2B', icon: Building },
  { value: 'retail', label: 'Retail', icon: Store },
  { value: 'ecommerce', label: 'E-commerce', icon: ShoppingBag },
  { value: 'finance', label: 'Finanzas', icon: DollarSign },
  { value: 'realestate', label: 'Real Estate', icon: Home },
  { value: 'automotive', label: 'Automotriz', icon: Car },
  { value: 'technology', label: 'Tecnología', icon: Laptop },
  { value: 'travel', label: 'Viajes', icon: Plane },
  { value: 'food', label: 'Alimentos', icon: Utensils },
  { value: 'services', label: 'Servicios', icon: Briefcase },
];

const communicationTones = [
  { value: 'professional', label: 'Profesional', description: 'Formal y corporativo', color: '#6366f1' },
  { value: 'friendly', label: 'Amigable', description: 'Cercano y cálido', color: '#22c55e' },
  { value: 'casual', label: 'Casual', description: 'Relajado y conversacional', color: '#f59e0b' },
  { value: 'energetic', label: 'Energético', description: 'Dinámico y entusiasta', color: '#ec4899' },
  { value: 'empathetic', label: 'Empático', description: 'Comprensivo y paciente', color: '#8b5cf6' },
  { value: 'authoritative', label: 'Autoritativo', description: 'Experto y confiable', color: '#06b6d4' },
];

const genderOptions = [
  { value: 'female', label: 'Femenino', icon: UserRound },
  { value: 'male', label: 'Masculino', icon: User },
  { value: 'neutral', label: 'Neutro', icon: Bot },
];

interface AgentData {
  name: string;
  gender: string;
  tone: string;
  industry: string;
  tagline: string;
  bio: string;
  instructions: string;
  language: string;
  avatar: string | null;
  role: 'orchestrator' | 'specialist';
}

const DEFAULT: AgentData = {
  name: 'Sofia',
  gender: 'female',
  tone: 'friendly',
  industry: 'services',
  tagline: 'Tu asistente virtual de confianza',
  bio: 'Soy Sofia, tu asesora virtual. Estoy aquí para ayudarte a encontrar exactamente lo que necesitas.',
  instructions: 'Ayuda al cliente de manera amable y siempre busca dirigir la conversación hacia una venta.',
  language: 'es',
  avatar: null,
  role: 'orchestrator',
};


import { fetchAgents, createAgent, updateAgent, uploadAgentAvatar } from "@/lib/api";

export default function AgentIdentity() {
  const router = useRouter();
  const [agentData, setAgentData] = useState<AgentData>(DEFAULT);
  const [agentId, setAgentId] = useState<string | null>(null);
  const [fullScriptData, setFullScriptData] = useState<any>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !agentId) return;

    try {
      const toastId = toast.loading('Subiendo avatar...');
      const response = await uploadAgentAvatar(agentId, file);
      
      // Mantenemos la URL actualizada en el estado
      setAgentData(prev => ({ ...prev, avatar: response.avatar_url }));
      
      // Actualizamos fullScriptData para no perderlo
      setFullScriptData((prev: any) => ({
        ...(prev || {}),
        avatar: response.avatar_url
      }));

      toast.success('Avatar subido correctamente', { id: toastId });
    } catch (error) {
      console.error('Error subiendo avatar:', error);
      toast.error('Error al subir el avatar');
    }
  };

  useEffect(() => {
    async function loadData() {
      try {
        const agents = await fetchAgents();
        if (agents && agents.length > 0) {
          const firstAgent = agents[0];
          setAgentId(firstAgent.id);
          const scriptData = firstAgent.script_ventas || {};
          setFullScriptData(scriptData);
          
          setAgentData({
            name: firstAgent.nombre || DEFAULT.name,
            gender: firstAgent.genero || DEFAULT.gender,
            tone: firstAgent.humor || DEFAULT.tone, // Usa humor en lugar de tono
            industry: firstAgent.tipo_negocio || DEFAULT.industry,
            tagline: firstAgent.descripcion || DEFAULT.tagline,
            bio: firstAgent.personalidad || DEFAULT.bio, // Bio es ahora personalidad
            instructions: firstAgent.instrucciones || DEFAULT.instructions,
            language: firstAgent.idioma || DEFAULT.language,
            avatar: scriptData.avatar || DEFAULT.avatar,
            role: scriptData.rol_agente?.tipo || DEFAULT.role,
          });
        }
      } catch (error) {
        console.error("Error fetching agents:", error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const updatedScriptVentas = {
        ...(fullScriptData || {}),
        avatar: agentData.avatar,
        rol_agente: {
          tipo: agentData.role,
          area: agentData.role === 'specialist' ? agentData.industry : null
        }
      };

      const payload = {
        nombre: agentData.name,
        genero: agentData.gender,
        humor: agentData.tone, // Mapea tone al campo humor de DB
        tono: agentData.tone, // Mantenemos tono por compatibilidad si es necesario, o lo igualamos
        idioma: agentData.language,
        tipo_negocio: agentData.industry,
        area: agentData.industry,
        descripcion: agentData.tagline,
        personalidad: agentData.bio, // Bio es la personalidad
        instrucciones: agentData.instructions,
        script_ventas: updatedScriptVentas
      };

      if (agentId) {
        await updateAgent(agentId, payload);
      } else {
        const result = await createAgent(payload);
        setAgentId(result.agente_id);
        localStorage.setItem("flux_agent_id", result.agente_id);
        localStorage.setItem("flux_agent_nombre", agentData.name);
      }
      localStorage.setItem("flux_phase_1", "true");
      setSaved(true);
      toast.success(`✅ Identidad del agente "${agentData.name}" guardada exitosamente`);
      window.dispatchEvent(new Event('storage'));
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error("Error saving agent:", error);
      toast.error("Error al guardar la configuración");
    } finally {
      setIsSaving(false);
    }
  };

  const reset = () => { setAgentData(DEFAULT); setSaved(false); toast.info("Formulario limpiado"); };

  const selectedIndustry = industries.find(i => i.value === agentData.industry);
  const selectedTone = communicationTones.find(t => t.value === agentData.tone);
  const selectedGender = genderOptions.find(g => g.value === agentData.gender);

  if (loading) {
    return <div className="space-y-4 max-w-6xl mx-auto p-4">{[1,2,3].map(i => <Skeleton key={i} className="h-48 w-full rounded-2xl" />)}</div>;
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-7xl mx-auto" suppressHydrationWarning={true}>
      {/* Page Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 animate-entry">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Bot className="w-4 h-4 text-primary" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-primary/80">Personalidad y Rol</span>
          </div>
          <h1 className="text-3xl font-black text-white/90 tracking-tight">
            <span className="text-primary">Identidad</span> del Agente
          </h1>
          <p className="text-sm text-white/50 font-light mt-1">
            Define el rol, especialidad y la apariencia de tu agente de ventas IA.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={reset} className="rounded-xl border-white/10 bg-black/20 text-white/70 hover:text-white hover:bg-white/5 h-11 transition-all">
            <RotateCcw className="w-4 h-4 mr-2" /> Resetear
          </Button>
          <Button
            onClick={handleSave}
            disabled={isSaving}
            className="rounded-xl bg-primary hover:bg-primary/90 text-white h-11 px-6 shadow-[0_0_20px_rgba(6,182,212,0.3)] transition-all font-bold"
          >
            {isSaving ? (
              <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Guardando...</>
            ) : saved ? (
              <><Check className="w-4 h-4 mr-2" /> Guardado</>
            ) : (
              <><Save className="w-4 h-4 mr-2" /> Guardar Cambios</>
            )}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Settings */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Info Card */}
          <div className="bg-black/40 backdrop-blur-xl rounded-[24px] border border-white/5 p-8 shadow-xl">
            <h2 className="text-lg font-bold text-white/90 flex items-center gap-2 mb-6">
              <User className="w-5 h-5 text-primary" />
              Información Básica
            </h2>

            <div className="space-y-6">
              {/* Name Input */}
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">Nombre del Agente</label>
                <input
                  type="text"
                  value={agentData.name}
                  onChange={(e) => setAgentData({ ...agentData, name: e.target.value })}
                  className="w-full px-4 py-3 bg-black/20 rounded-xl border border-white/10 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all text-lg font-semibold text-white/90 placeholder-white/20"
                  placeholder="Ej: Sofia, Carlos, Luna..."
                />
              </div>

              {/* Gender Selection */}
              <div>
                <label className="block text-sm font-medium text-white/70 mb-3">Género de Voz</label>
                <div className="grid grid-cols-3 gap-3">
                  {genderOptions.map((gender) => (
                    <button
                      key={gender.value}
                      onClick={() => setAgentData({ ...agentData, gender: gender.value })}
                      className={`p-4 rounded-xl border transition-all flex flex-col items-center justify-center gap-2 ${
                        agentData.gender === gender.value
                          ? 'border-primary bg-primary/10 text-primary shadow-[inset_0_1px_0_0_rgba(6,182,212,0.1)]'
                          : 'border-white/5 bg-white/5 hover:bg-white/10 text-white/50 hover:text-white/80'
                      }`}
                    >
                      <gender.icon size={24} strokeWidth={1.5} />
                      <p className="text-sm font-medium">{gender.label}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Industry Selection */}
              <div>
                <label className="block text-sm font-medium text-white/70 mb-3">
                  <Briefcase className="w-4 h-4 inline mr-1" />
                  Giro del Negocio
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                  {industries.map((industry) => (
                    <button
                      key={industry.value}
                      onClick={() => setAgentData({ ...agentData, industry: industry.value })}
                      className={`p-3 rounded-xl border transition-all text-left flex items-center gap-3 ${
                        agentData.industry === industry.value
                          ? 'border-primary bg-primary/10 text-primary shadow-[inset_0_1px_0_0_rgba(6,182,212,0.1)]'
                          : 'border-white/5 bg-white/5 hover:bg-white/10 text-white/50 hover:text-white/80'
                      }`}
                    >
                      <industry.icon size={18} strokeWidth={1.5} />
                      <p className="text-sm font-medium">{industry.label}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Communication Tone */}
              <div>
                <label className="block text-sm font-medium text-white/70 mb-3">Tono de Comunicación</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {communicationTones.map((tone) => (
                    <button
                      key={tone.value}
                      onClick={() => setAgentData({ ...agentData, tone: tone.value })}
                      className={`p-4 rounded-xl border transition-all text-left ${
                        agentData.tone === tone.value
                          ? 'border-current bg-current/10 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.1)]'
                          : 'border-white/5 bg-white/5 hover:bg-white/10 text-white/50'
                      }`}
                      style={{ color: agentData.tone === tone.value ? tone.color : 'inherit' }}
                    >
                      <p className="text-sm font-semibold text-white/90">{tone.label}</p>
                      <p className="text-xs mt-1" style={{ color: agentData.tone === tone.value ? tone.color : 'rgba(255,255,255,0.4)' }}>{tone.description}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Tagline */}
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">Tagline / Lema</label>
                <input
                  type="text"
                  value={agentData.tagline}
                  onChange={(e) => setAgentData({ ...agentData, tagline: e.target.value })}
                  className="w-full px-4 py-3 bg-black/20 rounded-xl border border-white/10 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all text-white/90 placeholder-white/20"
                  placeholder="Ej: Tu asistente virtual de confianza"
                />
                <p className="text-xs text-white/40 mt-2 font-light">
                  Frase corta que define la esencia del agente
                </p>
              </div>

              {/* Bio */}
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">Biografía (Personalidad)</label>
                <textarea
                  value={agentData.bio}
                  onChange={(e) => setAgentData({ ...agentData, bio: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-3 bg-black/20 rounded-xl border border-white/10 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all resize-none text-white/90 placeholder-white/20"
                  placeholder="Soy Sofia, tu asesora virtual..."
                />
                <p className="text-xs text-white/40 mt-2 font-light">
                  Cómo se presenta el agente (se usa para darle personalidad)
                </p>
              </div>

              {/* Instructions */}
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">Instrucciones Operativas</label>
                <textarea
                  value={agentData.instructions}
                  onChange={(e) => setAgentData({ ...agentData, instructions: e.target.value })}
                  rows={4}
                  className="w-full px-4 py-3 bg-black/20 rounded-xl border border-white/10 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all resize-none text-white/90 placeholder-white/20"
                  placeholder="Ayuda al cliente a encontrar lo que necesita, no des descuentos..."
                />
                <p className="text-xs text-white/40 mt-2 font-light">
                  Directivas generales sobre qué debe y no debe hacer el agente
                </p>
              </div>

              {/* Language Selection */}
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">Idioma Principal</label>
                <select
                  value={agentData.language}
                  onChange={(e) => setAgentData({ ...agentData, language: e.target.value })}
                  className="w-full px-4 py-3 bg-black/20 rounded-xl border border-white/10 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all text-white/90"
                >
                  <option value="es" className="bg-[#0A0A0B]">Español</option>
                  <option value="en" className="bg-[#0A0A0B]">English</option>
                  <option value="pt" className="bg-[#0A0A0B]">Português</option>
                  <option value="fr" className="bg-[#0A0A0B]">Français</option>
                </select>
              </div>
            </div>
          </div>

          {/* Avatar & Role Settings */}
          <div className="bg-black/40 backdrop-blur-xl rounded-[24px] border border-white/5 p-8 shadow-xl">
            <h2 className="text-lg font-bold text-white/90 flex items-center gap-2 mb-6">
              <UserRound className="w-5 h-5 text-primary" />
              Rol y Avatar
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {/* Role Selection */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">Rol del Agente</label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      onClick={() => setAgentData({ ...agentData, role: 'orchestrator' })}
                      className={`flex flex-col items-center justify-center p-4 rounded-xl border transition-all ${
                        agentData.role === 'orchestrator'
                          ? 'border-primary bg-primary/10 text-primary shadow-[inset_0_1px_0_0_rgba(6,182,212,0.1)]'
                          : 'border-white/5 bg-white/5 hover:bg-white/10 text-white/50 hover:text-white/80'
                      }`}
                    >
                      <Sparkles className="w-6 h-6 mb-2" />
                      <span className="text-sm font-medium">Orquestador</span>
                    </button>
                    <button
                      onClick={() => setAgentData({ ...agentData, role: 'specialist' })}
                      className={`flex flex-col items-center justify-center p-4 rounded-xl border transition-all ${
                        agentData.role === 'specialist'
                          ? 'border-primary bg-primary/10 text-primary shadow-[inset_0_1px_0_0_rgba(6,182,212,0.1)]'
                          : 'border-white/5 bg-white/5 hover:bg-white/10 text-white/50 hover:text-white/80'
                      }`}
                    >
                      <Briefcase className="w-6 h-6 mb-2" />
                      <span className="text-sm font-medium">Especialista</span>
                    </button>
                  </div>
                  <p className="text-xs text-white/40 mt-2 font-light">
                    {agentData.role === 'orchestrator' 
                      ? "El primer punto de contacto. Enruta las conversaciones." 
                      : "Experto en un área específica. Recibe delegaciones."}
                  </p>
                </div>

                {/* Expertise Area (Only if specialist) */}
                {agentData.role === 'specialist' && (
                  <div className="animate-fade-in">
                    <label className="block text-sm font-medium text-white/70 mb-2">Área de Especialidad</label>
                    <select
                      value={agentData.industry}
                      onChange={(e) => setAgentData({ ...agentData, industry: e.target.value })}
                      className="w-full px-4 py-3 bg-black/20 rounded-xl border border-white/10 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all text-white/90"
                    >
                      {industries.map(ind => (
                        <option key={ind.value} value={ind.value} className="bg-[#0A0A0B]">{ind.label}</option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

                <AvatarSelector 
                  agentId={agentId || ''} 
                  currentAvatar={agentData.avatar}
                  onAvatarChange={(url) => {
                    setAgentData(prev => ({ ...prev, avatar: url }));
                    setFullScriptData((prev: any) => ({ ...(prev || {}), avatar: url }));
                  }}
                />
            </div>
          </div>
        </div>

        {/* Right Column - Preview & Stats */}
        <div className="space-y-6">
          {/* Agent Preview Card */}
          <div className="bg-black/40 backdrop-blur-xl rounded-[24px] border border-white/5 p-8 shadow-xl border-t-2" style={{ borderTopColor: '#06b6d4' }}>
            <h2 className="text-lg font-bold text-white/90 flex items-center gap-2 mb-6">
              <Bot className="w-5 h-5 text-primary" />
              Vista Previa
            </h2>

            {/* Chat Preview */}
            <div className="bg-black/20 rounded-2xl p-4 space-y-4 border border-white/10">
              {/* Agent Message */}
              <div className="flex items-start gap-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center text-black font-black text-sm flex-shrink-0 bg-primary bg-cover bg-center shadow-[0_0_15px_rgba(6,182,212,0.4)]"
                  style={agentData.avatar ? { backgroundImage: `url(${agentData.avatar.startsWith('/') ? `${process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:9000'}${agentData.avatar}` : agentData.avatar})`, color: 'transparent' } : {}}
                >
                  {!agentData.avatar && (agentData.name.substring(0, 2).toUpperCase() || "AI")}
                </div>
                <div className="flex-1">
                  <div className="bg-white/5 backdrop-blur-sm rounded-2xl rounded-tl-sm p-4 shadow-sm border border-white/10">
                    <p className="text-sm font-bold text-primary">{agentData.name}</p>
                    <p className="text-xs text-white/40 italic mt-1 font-light">{agentData.tagline || "Tagline del agente..."}</p>
                    <p className="text-sm mt-2 text-white/80">{agentData.bio || "Biografía del agente..."}</p>
                  </div>
                </div>
              </div>

              {/* User Message */}
              <div className="flex items-start gap-3 justify-end">
                <div className="text-black font-medium rounded-2xl rounded-tr-sm p-4 max-w-[80%] shadow-sm bg-primary">
                  <p className="text-sm">Hola, ¿qué productos tienen?</p>
                </div>
              </div>

              {/* Typing Indicator */}
              <div className="flex items-start gap-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center text-black font-black text-sm flex-shrink-0 bg-primary bg-cover bg-center shadow-[0_0_15px_rgba(6,182,212,0.4)]"
                  style={agentData.avatar ? { backgroundImage: `url(${agentData.avatar})`, color: 'transparent' } : {}}
                >
                  {!agentData.avatar && (agentData.name.substring(0, 2).toUpperCase() || "AI")}
                </div>
                <div className="bg-white/5 backdrop-blur-sm rounded-2xl rounded-tl-sm p-4 shadow-sm border border-white/10 flex items-center">
                  <div className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Stats Gradient */}
          <div className="rounded-[24px] p-8 text-white relative overflow-hidden" style={{ background: `linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)`, boxShadow: `0 10px 40px rgba(6, 182, 212, 0.2)` }}>
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none"></div>
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Sparkles className="w-5 h-5" />
              Configuración Actual
            </h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between items-center py-2 border-b border-white/20">
                <span className="text-white/80">Nombre</span>
                <span className="font-bold">{agentData.name || "N/A"}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-white/20">
                <span className="text-white/80">Género</span>
                <span className="font-bold flex items-center gap-2">
                  {selectedGender && <selectedGender.icon size={14} />} {selectedGender?.label}
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-white/20">
                <span className="text-white/80">Industria</span>
                <span className="font-bold flex items-center gap-2">
                  {selectedIndustry && <selectedIndustry.icon size={14} />} {selectedIndustry?.label}
                </span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-white/80">Tono</span>
                <span className="font-bold">{selectedTone?.label}</span>
              </div>
            </div>
          </div>

          {/* Tips */}
          <div className="bg-primary/5 rounded-[24px] p-6 border border-primary/20 backdrop-blur-sm">
            <h3 className="font-bold text-primary flex items-center gap-2 mb-4">
              <AlertCircle className="w-5 h-5" />
              Consejos
            </h3>
            <ul className="space-y-3 text-sm text-white/60 font-light">
              <li className="flex items-start gap-2">
                <ChevronRight className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                <span>Elige un nombre memorable y fácil de recordar para tus clientes.</span>
              </li>
              <li className="flex items-start gap-2">
                <ChevronRight className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                <span>El tono debe coincidir con la imagen corporativa de tu negocio.</span>
              </li>
              <li className="flex items-start gap-2">
                <ChevronRight className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                <span>La biografía es clave: se usará como contexto principal en las conversaciones.</span>
              </li>
            </ul>
          </div>

          {/* Sugerencia de Siguiente Paso */}
          <Button 
            className="w-full rounded-[20px] h-14 flex items-center justify-between px-6 border border-white/10 bg-white/5 hover:bg-white/10 text-white transition-all group backdrop-blur-sm shadow-xl"
            onClick={() => router.push("/dashboard/scripts")}
          >
            <span className="font-bold flex items-center gap-2">
              Siguiente: Script de Ventas
            </span>
            <ArrowRight className="w-5 h-5 group-hover:translate-x-2 group-hover:text-primary transition-all duration-300" />
          </Button>

        </div>
      </div>
    </div>
  );
}
