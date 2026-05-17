"use client";

import { useState, useEffect } from 'react';
import {
  MessageSquare,
  Save,
  Plus,
  Trash2,
  GripVertical,
  Star,
  ChevronRight,
  Check,
  Sparkles,
  AlertCircle,
  FileText,
  Copy,
  Edit2,
  CheckCircle2,
  Loader2,
  Search,
  Bot
} from 'lucide-react';
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchAgents, createAgent, updateAgent } from "@/lib/api";

// Types
interface GoldenRule {
  id: string;
  rule: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  enabled: boolean;
}

interface SalesPhase {
  id: string;
  name: string;
  description: string;
  objective: string;
  keyPhrases: string[];
  enabled: boolean;
}

export default function SalesScript() {
  const [activeTab, setActiveTab] = useState<'phases' | 'rules' | 'scripts' | 'escalation' | 'chat'>('phases');
  
  const [agentId, setAgentId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  const [goldenRules, setGoldenRules] = useState<GoldenRule[]>([]);
  const [salesPhases, setSalesPhases] = useState<SalesPhase[]>([]);
  const [customScripts, setCustomScripts] = useState<any[]>([]);
  
  const [escalationKeywords, setEscalationKeywords] = useState<string[]>([]);
  const [newKeyword, setNewKeyword] = useState('');
  
  const [chatSettings, setChatSettings] = useState({
    typing_effect: true,
    typing_delay_min: 1000,
    typing_delay_max: 3000,
    auto_greeting: true,
    greeting_delay: 2000
  });

  useEffect(() => {
    async function loadData() {
      try {
        const agents = await fetchAgents();
        
        const defaultRules: GoldenRule[] = [
          { id: 'r1', rule: 'Empatía Primero', description: 'Siempre responde entendiendo la necesidad del cliente antes de vender.', priority: 'high', enabled: true },
          { id: 'r2', rule: 'Respuestas Concisas', description: 'Mantén los mensajes cortos, claros y directos.', priority: 'medium', enabled: true },
          { id: 'r3', rule: 'Llamado a la Acción (CTA)', description: 'Finaliza cada interacción invitando a un siguiente paso natural.', priority: 'high', enabled: true },
        ];

        const defaultPhases: SalesPhase[] = [
          { id: 'p1', name: 'Saludo y Presentación', description: 'Primera impresión con el cliente', objective: 'Conocer las necesidades', keyPhrases: ['¡Hola {name}! Soy {nombre_agente}', 'Gracias por escribirnos. ¿En qué te podemos ayudar hoy?'], enabled: true },
          { id: 'p2', name: 'Descubrimiento', description: 'Identificar necesidades del cliente', objective: 'Generar interés', keyPhrases: ['Para poder ayudarte mejor, ¿podrías indicarme...', '¿Cuál es tu mayor desafío actual...?'], enabled: true },
          { id: 'p3', name: 'Presentación', description: 'Mostrar la solución más adecuada', objective: 'Dar seguridad', keyPhrases: ['Basándome en lo que necesitas...', 'Nuestros servicios están diseñados para...'], enabled: true },
          { id: 'p4', name: 'Manejo de Objeciones', description: 'Resolver dudas y preocupaciones', objective: 'Cerrar el trato', keyPhrases: ['Entiendo tu preocupación sobre...', 'El sistema es modular y podemos adaptarlo...'], enabled: true },
          { id: 'p5', name: 'Cierre y Seguimiento', description: 'Finalizar la venta o agendar siguiente paso', objective: 'Asegurar venta', keyPhrases: ['¿Te gustaría proceder con la cotización formal?', 'Perfecto, te envío el enlace y el cronograma...'], enabled: true },
        ];

        const defaultScripts = [
          { id: 's1', name: 'Respuesta a price', trigger: 'pregunta_precio', enabled: true, content: 'El price varía según el plan seleccionado. ¿Podrías contarme primero qué necesidades tienes para poder darte una cotización precisa?', uses: 234 },
          { id: 's2', name: 'Respuesta a horario', trigger: 'pregunta_horario', enabled: true, content: 'Estamos disponibles de Lunes a Viernes de 9AM a 6PM. ¿Te gustaría que agendemos una llamada en algún horario específico?', uses: 156 },
          { id: 's3', name: 'Leads fríos', trigger: 'reengagement', enabled: false, content: 'Hola {name}, ¿cómo estás? Quería saber si aún estás interesado/a en {producto}. Tenemos una oferta especial por tiempo limitado.', uses: 89 },
          { id: 's4', name: 'Primer Contacto', trigger: 'first_contact', enabled: true, content: '¡Hola! Soy tu asesora virtual. Estoy aquí para ayudarte. ¿En qué puedo servirte hoy?', uses: 0 },
          { id: 's5', name: 'Cliente Retornando', trigger: 'returning', enabled: true, content: '¡Qué bueno verte de nuevo! ¿En qué te puedo ayudar esta vez?', uses: 0 },
          { id: 's6', name: 'Fuera de Horario', trigger: 'after_hours', enabled: true, content: '¡Hola! Actualmente estamos fuera de horario de atención, pero puedes dejar tu mensaje y te responderemos mañana a primera hora.', uses: 0 }
        ];
        
        const defaultKeywords = ['hablar con humano', 'hablar con persona', 'supervisor', 'gerente', 'no puedo'];

        if (agents && agents.length > 0) {
          const firstAgent = agents[0];
          setAgentId(firstAgent.id);
          const scriptData = firstAgent.sales_script || {};
          
          setGoldenRules(Array.isArray(scriptData.reglas) ? scriptData.reglas : defaultRules);
          setSalesPhases(Array.isArray(scriptData.fases) ? scriptData.fases : defaultPhases);
          setCustomScripts(Array.isArray(scriptData.scripts) ? scriptData.scripts : defaultScripts);
          setEscalationKeywords(Array.isArray(scriptData.escalacion?.keywords) ? scriptData.escalacion.keywords : defaultKeywords);
          
          if (scriptData.chat_settings) {
            setChatSettings(prev => ({ ...prev, ...scriptData.chat_settings }));
          }
        } else {
          setGoldenRules(defaultRules);
          setSalesPhases(defaultPhases);
          setCustomScripts(defaultScripts);
          setEscalationKeywords(defaultKeywords);
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
      const payload = {
        sales_script: {
          fases: salesPhases,
          reglas: goldenRules,
          scripts: customScripts,
          escalacion: {
            enabled: true,
            keywords: escalationKeywords,
            mensaje: "Entiendo, déjame transferirte con un asesor humano."
          },
          chat_settings: chatSettings
        }
      };

      if (agentId) {
        await updateAgent(agentId, payload);
      } else {
        const result = await createAgent({ name: "Nuevo Agente", ...payload });
        setAgentId(result.agente_id);
        localStorage.setItem("flux_agent_id", result.agente_id);
      }
      localStorage.setItem("flux_phase_2", "true");
      setSaved(true);
      toast.success(`✅ Script de ventas guardado exitosamente`);
      window.dispatchEvent(new Event('storage'));
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error("Error saving script:", error);
      toast.error("Error al guardar la configuración");
    } finally {
      setIsSaving(false);
    }
  };

  const [newRuleText, setNewRuleText] = useState('');

  const toggleRule = (id: string) => {
    setGoldenRules(rules => rules.map(r =>
      r.id === id ? { ...r, enabled: !r.enabled } : r
    ));
  };

  const deleteRule = (id: string) => {
    setGoldenRules(rules => rules.filter(r => r.id !== id));
  };

  const addRule = () => {
    if (!newRuleText.trim()) return;
    setGoldenRules(rules => [...rules, {
      id: Date.now().toString(),
      rule: newRuleText,
      description: 'Nueva regla agregada',
      priority: 'medium',
      enabled: true
    }]);
    setNewRuleText('');
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-pink/10 text-pink';
      case 'medium': return 'bg-accent/10 text-accent';
      case 'low': return 'bg-secondary/10 text-secondary';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  const getPhaseIcon = (index: number) => {
    const icons = [
      <MessageSquare key="p1" className="w-5 h-5 text-indigo-500" />,
      <Search key="p2" className="w-5 h-5 text-blue-500" />,
      <Sparkles key="p3" className="w-5 h-5 text-purple-500" />,
      <CheckCircle2 key="p4" className="w-5 h-5 text-emerald-500" />,
      <Bot key="p5" className="w-5 h-5 text-pink-500" />
    ];
    return icons[index] || <FileText className="w-5 h-5" />;
  };

  const [mounted, setMounted] = useState(false);
  
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className="min-h-screen" suppressHydrationWarning></div>;
  }

  if (loading) {
    return <div className="space-y-4 max-w-6xl mx-auto p-8"><div className="h-48 w-full bg-white/5 animate-pulse rounded-3xl" /></div>;
  }
  return (
    <div className="space-y-6 animate-fade-in max-w-7xl mx-auto" suppressHydrationWarning>
      {/* Premium Background Effects */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-[120px] pointer-events-none -z-10" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-[120px] pointer-events-none -z-10" />

      {/* Page Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 animate-entry relative z-10">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-[10px] font-black uppercase tracking-widest text-primary/80">Estrategia Dinámica</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-black text-white/90 tracking-tight">
            <span className="text-primary">Estrategia</span> de Ventas
          </h1>
          <p className="text-sm text-white/50 font-light mt-2">
            Configura las fases, reglas de oro y el comportamiento inteligente de tu agente.
          </p>
        </div>
        <button 
          onClick={handleSave}
          disabled={isSaving}
          className="flex items-center gap-2 px-6 py-3 bg-primary hover:bg-primary/90 text-black font-black rounded-xl hover:scale-[1.02] active:scale-[0.98] transition-all shadow-[0_0_20px_rgba(6,182,212,0.3)]">
          {isSaving ? (
            <><Loader2 className="w-5 h-5 animate-spin" /> Guardando...</>
          ) : saved ? (
            <><Check className="w-5 h-5" /> Guardado</>
          ) : (
            <><Save className="w-5 h-5" /> Guardar Todo</>
          )}
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="flex items-center gap-2 bg-black/40 backdrop-blur-xl rounded-[20px] p-2 border border-white/5 overflow-x-auto relative z-10 shadow-lg">
        <button
          onClick={() => setActiveTab('phases')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-sm whitespace-nowrap transition-all ${
            activeTab === 'phases'
              ? 'bg-primary text-black shadow-[0_0_15px_rgba(6,182,212,0.4)]'
              : 'text-white/60 hover:text-white/90 hover:bg-white/5'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          Fases de Venta
        </button>
        <button
          onClick={() => setActiveTab('rules')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-sm whitespace-nowrap transition-all ${
            activeTab === 'rules'
              ? 'bg-primary text-black shadow-[0_0_15px_rgba(6,182,212,0.4)]'
              : 'text-white/60 hover:text-white/90 hover:bg-white/5'
          }`}
        >
          <Star className="w-4 h-4" />
          Reglas de Oro
        </button>
        <button
          onClick={() => setActiveTab('scripts')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-sm whitespace-nowrap transition-all ${
            activeTab === 'scripts'
              ? 'bg-primary text-black shadow-[0_0_15px_rgba(6,182,212,0.4)]'
              : 'text-white/60 hover:text-white/90 hover:bg-white/5'
          }`}
        >
          <FileText className="w-4 h-4" />
          Respuestas Rápidas
        </button>
        <button
          onClick={() => setActiveTab('escalation')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-sm whitespace-nowrap transition-all ${
            activeTab === 'escalation'
              ? 'bg-primary text-black shadow-[0_0_15px_rgba(6,182,212,0.4)]'
              : 'text-white/60 hover:text-white/90 hover:bg-white/5'
          }`}
        >
          <AlertCircle className="w-4 h-4" />
          Escalación
        </button>
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-sm whitespace-nowrap transition-all ${
            activeTab === 'chat'
              ? 'bg-primary text-black shadow-[0_0_15px_rgba(6,182,212,0.4)]'
              : 'text-white/60 hover:text-white/90 hover:bg-white/5'
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          Ajustes del Chat
        </button>
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 relative z-10">
        <div className="lg:col-span-2">
          {/* Sales Phases */}
          {activeTab === 'phases' && (
            <div className="bg-black/40 backdrop-blur-xl rounded-[24px] border border-white/5 overflow-hidden shadow-xl">
              <div className="p-6 border-b border-white/5">
                <h2 className="font-bold text-white/90 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-primary" />
                  Fases del Proceso de Venta
                </h2>
                <p className="text-sm text-white/50 mt-1 font-light">
                  Define cada etapa de la conversación para guiar al agente
                </p>
              </div>

              <div className="p-6 space-y-4">
                {salesPhases.map((phase, index) => (
                  <div
                    key={phase.id}
                    className={`p-5 rounded-2xl border transition-all ${
                      phase.enabled
                        ? 'border-white/10 hover:border-primary/30 bg-white/5'
                        : 'border-dashed border-white/5 bg-black/20 opacity-60'
                    }`}
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex items-center gap-2">
                        <GripVertical className="w-5 h-5 text-white/30 cursor-grab" />
                        <div className="w-10 h-10 rounded-xl bg-primary/20 text-primary border border-primary/30 flex items-center justify-center text-xl shadow-[0_0_10px_rgba(6,182,212,0.2)]">
                          {getPhaseIcon(index)}
                        </div>
                      </div>

                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <h3 className="font-bold text-white/90">{phase.name}</h3>
                            <span className="px-3 py-1 rounded-full text-xs font-bold bg-primary/10 text-primary border border-primary/20">
                              Paso {index + 1}
                            </span>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input 
                              type="checkbox" 
                              checked={phase.enabled} 
                              onChange={() => {
                                const updated = salesPhases.map(p =>
                                  p.id === phase.id ? { ...p, enabled: !p.enabled } : p
                                );
                                setSalesPhases(updated);
                              }} 
                              className="sr-only peer" 
                            />
                            <div className="w-11 h-6 bg-white/10 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-white/20 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary shadow-inner"></div>
                          </label>
                        </div>
                        <p className="text-sm text-white/50 mt-1 font-light">{phase.description}</p>

                        <div className="mt-4 p-4 bg-black/40 border border-white/5 rounded-xl">
                          <p className="text-xs font-bold text-white/40 mb-3 uppercase tracking-widest">Frases clave:</p>
                          <div className="flex flex-wrap gap-2">
                            {phase.keyPhrases?.map((phrase, i) => (
                              <span key={i} className="px-3 py-1.5 bg-primary/10 border border-primary/20 text-primary/90 rounded-lg text-sm">
                                &quot;{phrase.substring(0, 40)}...&quot;
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Golden Rules */}
          {activeTab === 'rules' && (
            <div className="bg-black/40 backdrop-blur-xl rounded-[24px] border border-white/5 overflow-hidden shadow-xl">
              <div className="p-6 border-b border-white/5">
                <h2 className="font-bold text-white/90 flex items-center gap-2">
                  <Star className="w-5 h-5 text-accent" />
                  Reglas de Oro
                </h2>
                <p className="text-sm text-white/50 mt-1 font-light">
                  Principios inquebrantables que el agente debe seguir siempre
                </p>
              </div>

              <div className="p-6 space-y-4">
                {/* Add New Rule */}
                <div className="p-5 bg-white/5 rounded-2xl border border-dashed border-white/10">
                  <div className="flex flex-col sm:flex-row items-center gap-3">
                    <input
                      type="text"
                      value={newRuleText}
                      onChange={(e) => setNewRuleText(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && addRule()}
                      placeholder="Escribe una nueva regla de oro..."
                      className="flex-1 w-full px-5 py-3 bg-black/40 rounded-xl border border-white/10 text-white/90 placeholder:text-white/30 outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/30 transition-all"
                    />
                    <button
                      onClick={addRule}
                      className="w-full sm:w-auto px-6 py-3 bg-primary text-black font-bold rounded-xl hover:bg-primary/90 transition-all flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(6,182,212,0.3)]"
                    >
                      <Plus className="w-5 h-5" />
                      Agregar
                    </button>
                  </div>
                </div>

                {goldenRules.map((rule, index) => (
                  <div
                    key={rule.id}
                    className={`p-5 rounded-2xl border transition-all ${
                      rule.enabled
                        ? 'border-white/10 bg-white/5'
                        : 'border-dashed border-white/5 bg-black/20 opacity-60'
                    }`}
                  >
                    <div className="flex items-start gap-4">
                      <div className="w-8 h-8 rounded-xl bg-accent/20 flex items-center justify-center flex-shrink-0 mt-1 shadow-lg">
                        <Star className="w-4 h-4 text-accent" />
                      </div>

                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className={`px-3 py-1 rounded-full text-xs font-bold border border-current ${getPriorityColor(rule.priority)}`}>
                              {rule.priority === 'high' && '⚡ Alta'}
                              {rule.priority === 'medium' && '📊 Media'}
                              {rule.priority === 'low' && '📉 Baja'}
                            </span>
                          </div>
                          <div className="flex items-center gap-3">
                            <label className="relative inline-flex items-center cursor-pointer">
                              <input 
                                type="checkbox" 
                                checked={rule.enabled} 
                                onChange={() => toggleRule(rule.id)} 
                                className="sr-only peer" 
                              />
                              <div className="w-11 h-6 bg-white/10 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-white/20 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary shadow-inner"></div>
                            </label>
                            <button
                              onClick={() => deleteRule(rule.id)}
                              className="p-2 bg-black/40 hover:bg-pink-500/20 border border-white/5 hover:border-pink-500/50 rounded-xl transition-all text-pink-500"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                        <p className="font-bold text-white/90 text-[15px]">{rule.rule}</p>
                        <p className="text-sm text-white/50 mt-1 font-light">{rule.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Custom Scripts */}
          {activeTab === 'scripts' && (
            <div className="bg-black/40 backdrop-blur-xl rounded-[24px] border border-white/5 overflow-hidden shadow-xl">
              <div className="p-6 border-b border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="font-bold text-white/90 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-primary" />
                    Scripts Personalizados
                  </h2>
                  <p className="text-sm text-white/50 mt-1 font-light">
                    Respuestas predefinidas para situaciones específicas
                  </p>
                </div>
                <button className="flex items-center justify-center gap-2 px-5 py-2.5 bg-primary/10 border border-primary/20 text-primary font-bold rounded-xl hover:bg-primary hover:text-black transition-all shadow-[0_0_15px_rgba(6,182,212,0.15)]">
                  <Plus className="w-4 h-4" />
                  Nuevo Script
                </button>
              </div>

              <div className="p-6 space-y-4">
                {customScripts.map((script) => (
                  <div key={script.id} className="p-5 rounded-2xl border border-white/10 hover:border-primary/30 bg-white/5 transition-all">
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                      <div>
                        <h3 className="font-bold text-white/90 text-[15px]">{script.name}</h3>
                        <p className="text-xs font-bold text-primary/70 mt-1 uppercase tracking-wider">{script.trigger}</p>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="px-3 py-1 bg-white/10 border border-white/10 text-white/80 rounded-full text-xs font-bold">
                          {script.uses || 0} usos
                        </span>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input 
                            type="checkbox" 
                            checked={script.enabled} 
                            onChange={() => {
                              const updated = customScripts.map(s =>
                                s.id === script.id ? { ...s, enabled: !s.enabled } : s
                              );
                              setCustomScripts(updated);
                            }} 
                            className="sr-only peer" 
                          />
                          <div className="w-11 h-6 bg-white/10 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-white/20 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary shadow-inner"></div>
                        </label>
                      </div>
                    </div>
                    <div className="mt-4 p-4 bg-black/40 border border-white/5 rounded-xl">
                      <p className="text-sm text-white/80 font-light leading-relaxed">{script.content}</p>
                    </div>
                    <div className="mt-4 flex items-center gap-3">
                      <button className="flex items-center gap-2 px-4 py-2 text-sm font-bold text-primary bg-primary/10 hover:bg-primary/20 border border-primary/10 rounded-xl transition-all">
                        <Edit2 className="w-4 h-4" />
                        Editar
                      </button>
                      <button className="flex items-center gap-2 px-4 py-2 text-sm font-bold text-white/60 bg-white/5 hover:bg-white/10 border border-white/5 rounded-xl transition-all">
                        <Copy className="w-4 h-4" />
                        Duplicar
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Escalation */}
          {activeTab === 'escalation' && (
            <div className="bg-black/40 backdrop-blur-xl rounded-[24px] border border-white/5 overflow-hidden shadow-xl">
              <div className="p-6 border-b border-white/5 flex justify-between items-center">
                <div>
                  <h2 className="font-bold text-white/90 flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-red-500" />
                    Palabras Clave de Escalación
                  </h2>
                  <p className="text-sm text-white/50 mt-1 font-light">
                    Si el cliente usa estas palabras, el agente transferirá la conversación a un humano.
                  </p>
                </div>
              </div>
              <div className="p-6">
                <div className="flex flex-col sm:flex-row gap-3 mb-6">
                  <input
                    type="text"
                    value={newKeyword}
                    onChange={(e) => setNewKeyword(e.target.value)}
                    placeholder="Ej: hablar con supervisor..."
                    className="flex-1 px-5 py-3 bg-black/40 rounded-xl border border-white/10 text-white/90 placeholder:text-white/30 outline-none focus:border-red-500/50 focus:ring-1 focus:ring-red-500/30 transition-all"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && newKeyword.trim()) {
                        if (!escalationKeywords.includes(newKeyword.trim())) {
                          setEscalationKeywords([...escalationKeywords, newKeyword.trim()]);
                        }
                        setNewKeyword('');
                      }
                    }}
                  />
                  <button 
                    onClick={() => {
                      if (newKeyword.trim() && !escalationKeywords.includes(newKeyword.trim())) {
                        setEscalationKeywords([...escalationKeywords, newKeyword.trim()]);
                        setNewKeyword('');
                      }
                    }}
                    className="px-6 py-3 bg-red-500/20 border border-red-500/30 text-red-400 rounded-xl hover:bg-red-500 hover:text-white transition-all font-bold whitespace-nowrap shadow-[0_0_15px_rgba(239,68,68,0.15)]">
                    Agregar Palabra
                  </button>
                </div>

                <div className="flex flex-wrap gap-3">
                  {escalationKeywords.map((keyword, index) => (
                    <div key={index} className="flex items-center gap-3 bg-white/5 px-4 py-2.5 rounded-full text-sm border border-white/10 text-white/80 font-medium">
                      {keyword}
                      <button 
                        onClick={() => setEscalationKeywords(escalationKeywords.filter((_, i) => i !== index))}
                        className="text-white/30 hover:text-red-400 hover:bg-red-500/10 p-1 rounded-full transition-all">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  {escalationKeywords.length === 0 && (
                    <p className="text-sm text-white/30 p-4 text-center w-full border border-dashed border-white/10 rounded-xl bg-white/5">No hay palabras clave configuradas. El agente intentará resolver todo por sí mismo.</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Chat Settings */}
          {activeTab === 'chat' && (
            <div className="bg-black/40 backdrop-blur-xl rounded-[24px] border border-white/5 overflow-hidden shadow-xl">
              <div className="p-6 border-b border-white/5">
                <h2 className="font-bold text-white/90 flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-blue-400" />
                  Ajustes del Widget de Chat
                </h2>
                <p className="text-sm text-white/50 mt-1 font-light">
                  Configura cómo se comporta el agente visualmente en el chat.
                </p>
              </div>
              <div className="p-6 space-y-6">
                
                {/* Typing Effect */}
                <div className="p-5 bg-white/5 rounded-2xl border border-white/10 hover:border-white/20 transition-all">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h4 className="font-bold text-[15px] text-white/90 flex items-center gap-2">
                        Efecto &quot;Escribiendo...&quot;
                      </h4>
                      <p className="text-sm text-white/50 font-light mt-1">Muestra un indicador de escritura antes de responder para simular comportamiento humano.</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        className="sr-only peer" 
                        checked={chatSettings.typing_effect}
                        onChange={() => setChatSettings({...chatSettings, typing_effect: !chatSettings.typing_effect})}
                      />
                      <div className="w-11 h-6 bg-white/10 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-white/20 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary shadow-inner"></div>
                    </label>
                  </div>
                  
                  {chatSettings.typing_effect && (
                    <div className="grid grid-cols-2 gap-4 mt-5 pt-5 border-t border-white/5">
                      <div>
                        <label className="block text-xs font-bold uppercase tracking-wider text-white/40 mb-2">Tiempo Mínimo (ms)</label>
                        <input 
                          type="number" 
                          value={chatSettings.typing_delay_min}
                          onChange={(e) => setChatSettings({...chatSettings, typing_delay_min: parseInt(e.target.value) || 1000})}
                          className="w-full px-4 py-3 bg-black/40 rounded-xl border border-white/10 text-white/90 outline-none focus:border-primary/50 transition-all"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-bold uppercase tracking-wider text-white/40 mb-2">Tiempo Máximo (ms)</label>
                        <input 
                          type="number" 
                          value={chatSettings.typing_delay_max}
                          onChange={(e) => setChatSettings({...chatSettings, typing_delay_max: parseInt(e.target.value) || 3000})}
                          className="w-full px-4 py-3 bg-black/40 rounded-xl border border-white/10 text-white/90 outline-none focus:border-primary/50 transition-all"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Auto Greeting */}
                <div className="p-5 bg-white/5 rounded-2xl border border-white/10 hover:border-white/20 transition-all">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h4 className="font-bold text-[15px] text-white/90 flex items-center gap-2">
                        Saludo Automático
                      </h4>
                      <p className="text-sm text-white/50 font-light mt-1">El agente enviará el primer mensaje automáticamente cuando el usuario abra el chat.</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        className="sr-only peer" 
                        checked={chatSettings.auto_greeting}
                        onChange={() => setChatSettings({...chatSettings, auto_greeting: !chatSettings.auto_greeting})}
                      />
                      <div className="w-11 h-6 bg-white/10 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-white/20 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary shadow-inner"></div>
                    </label>
                  </div>
                  
                  {chatSettings.auto_greeting && (
                    <div className="mt-5 pt-5 border-t border-white/5">
                      <label className="block text-xs font-bold uppercase tracking-wider text-white/40 mb-2">Retraso antes de enviar (ms)</label>
                      <input 
                        type="number" 
                        value={chatSettings.greeting_delay}
                        onChange={(e) => setChatSettings({...chatSettings, greeting_delay: parseInt(e.target.value) || 2000})}
                        className="w-full px-4 py-3 bg-black/40 rounded-xl border border-white/10 text-white/90 outline-none focus:border-primary/50 transition-all"
                      />
                    </div>
                  )}
                </div>

              </div>
            </div>
          )}

        </div>

        {/* Right Column - Tips & Summary */}
        <div className="space-y-6">
          {/* Quick Stats */}
          <div className="bg-gradient-to-br from-primary/20 via-blue-600/20 to-purple-600/20 backdrop-blur-xl border border-white/10 rounded-[24px] p-6 text-white shadow-xl">
            <h3 className="font-bold mb-5 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary" />
              Resumen del Script
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center py-3 border-b border-white/5">
                <span className="text-white/60 font-light">Fases activas</span>
                <span className="font-black text-2xl text-white/90">{salesPhases.filter(p => p.enabled).length}</span>
              </div>
              <div className="flex justify-between items-center py-3 border-b border-white/5">
                <span className="text-white/60 font-light">Reglas de oro</span>
                <span className="font-black text-2xl text-white/90">{goldenRules.filter(r => r.enabled).length}</span>
              </div>
              <div className="flex justify-between items-center py-3 border-b border-white/5">
                <span className="text-white/60 font-light">Scripts custom</span>
                <span className="font-black text-2xl text-white/90">{customScripts.length}</span>
              </div>
              <div className="flex justify-between items-center py-3">
                <span className="text-white/60 font-light">Frases clave</span>
                <span className="font-black text-2xl text-primary">
                  {salesPhases.reduce((acc, p) => acc + (p.keyPhrases?.length || 0), 0)}
                </span>
              </div>
            </div>
          </div>

          {/* Tips */}
          <div className="bg-emerald-500/10 backdrop-blur-xl rounded-[24px] p-6 border border-emerald-500/20 shadow-lg">
            <h3 className="font-bold text-emerald-400 flex items-center gap-2 mb-4">
              <AlertCircle className="w-5 h-5" />
              Mejores Prácticas
            </h3>
            <ul className="space-y-4">
              <li className="flex items-start gap-3 text-sm text-white/80 font-light">
                <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                <span>Usa frases cortas y directas para mejor engagement</span>
              </li>
              <li className="flex items-start gap-3 text-sm text-white/80 font-light">
                <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                <span>Incluye el name del cliente para personalizar</span>
              </li>
              <li className="flex items-start gap-3 text-sm text-white/80 font-light">
                <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                <span>Las reglas de alta priority deben ser claras</span>
              </li>
              <li className="flex items-start gap-3 text-sm text-white/80 font-light">
                <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                <span>Siempre incluye opción de escalar a humano</span>
              </li>
            </ul>
          </div>

          {/* Preview */}
          <div className="bg-black/40 backdrop-blur-xl rounded-[24px] border border-white/5 p-6 shadow-xl">
            <h3 className="font-bold text-white/90 flex items-center gap-2 mb-5">
              <MessageSquare className="w-5 h-5 text-pink-500" />
              Vista Previa
            </h3>
            <div className="bg-white/5 border border-white/5 rounded-2xl p-5">
              <div className="space-y-3">
                <div className="bg-black/40 border border-white/5 rounded-xl p-3 text-sm text-white/80">
                  <span className="text-primary font-bold tracking-wide">Fase 1:</span> Saludo
                </div>
                <div className="flex justify-center">
                  <ChevronRight className="w-4 h-4 text-white/30 rotate-90" />
                </div>
                <div className="bg-black/40 border border-white/5 rounded-xl p-3 text-sm text-white/80">
                  <span className="text-purple-400 font-bold tracking-wide">Fase 2:</span> Descubrimiento
                </div>
                <div className="flex justify-center">
                  <ChevronRight className="w-4 h-4 text-white/30 rotate-90" />
                </div>
                <div className="bg-black/40 border border-white/5 rounded-xl p-3 text-sm text-white/80">
                  <span className="text-emerald-400 font-bold tracking-wide">Fase 3:</span> Presentación
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
