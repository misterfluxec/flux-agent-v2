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
          { id: 'p1', name: 'Saludo y Presentación', description: 'Primera impresión con el cliente', objective: 'Conocer las necesidades', keyPhrases: ['¡Hola {nombre}! Soy {nombre_agente}', 'Gracias por escribirnos. ¿En qué te podemos ayudar hoy?'], enabled: true },
          { id: 'p2', name: 'Descubrimiento', description: 'Identificar necesidades del cliente', objective: 'Generar interés', keyPhrases: ['Para poder ayudarte mejor, ¿podrías indicarme...', '¿Cuál es tu mayor desafío actual...?'], enabled: true },
          { id: 'p3', name: 'Presentación', description: 'Mostrar la solución más adecuada', objective: 'Dar seguridad', keyPhrases: ['Basándome en lo que necesitas...', 'Nuestros servicios están diseñados para...'], enabled: true },
          { id: 'p4', name: 'Manejo de Objeciones', description: 'Resolver dudas y preocupaciones', objective: 'Cerrar el trato', keyPhrases: ['Entiendo tu preocupación sobre...', 'El sistema es modular y podemos adaptarlo...'], enabled: true },
          { id: 'p5', name: 'Cierre y Seguimiento', description: 'Finalizar la venta o agendar siguiente paso', objective: 'Asegurar venta', keyPhrases: ['¿Te gustaría proceder con la cotización formal?', 'Perfecto, te envío el enlace y el cronograma...'], enabled: true },
        ];

        const defaultScripts = [
          { id: 's1', name: 'Respuesta a precio', trigger: 'pregunta_precio', enabled: true, content: 'El precio varía según el plan seleccionado. ¿Podrías contarme primero qué necesidades tienes para poder darte una cotización precisa?', uses: 234 },
          { id: 's2', name: 'Respuesta a horario', trigger: 'pregunta_horario', enabled: true, content: 'Estamos disponibles de Lunes a Viernes de 9AM a 6PM. ¿Te gustaría que agendemos una llamada en algún horario específico?', uses: 156 },
          { id: 's3', name: 'Leads fríos', trigger: 'reengagement', enabled: false, content: 'Hola {nombre}, ¿cómo estás? Quería saber si aún estás interesado/a en {producto}. Tenemos una oferta especial por tiempo limitado.', uses: 89 },
          { id: 's4', name: 'Primer Contacto', trigger: 'first_contact', enabled: true, content: '¡Hola! Soy tu asesora virtual. Estoy aquí para ayudarte. ¿En qué puedo servirte hoy?', uses: 0 },
          { id: 's5', name: 'Cliente Retornando', trigger: 'returning', enabled: true, content: '¡Qué bueno verte de nuevo! ¿En qué te puedo ayudar esta vez?', uses: 0 },
          { id: 's6', name: 'Fuera de Horario', trigger: 'after_hours', enabled: true, content: '¡Hola! Actualmente estamos fuera de horario de atención, pero puedes dejar tu mensaje y te responderemos mañana a primera hora.', uses: 0 }
        ];
        
        const defaultKeywords = ['hablar con humano', 'hablar con persona', 'supervisor', 'gerente', 'no puedo'];

        if (agents && agents.length > 0) {
          const firstAgent = agents[0];
          setAgentId(firstAgent.id);
          const scriptData = firstAgent.script_ventas || {};
          
          setGoldenRules(scriptData.reglas?.length ? scriptData.reglas : defaultRules);
          setSalesPhases(scriptData.fases?.length ? scriptData.fases : defaultPhases);
          setCustomScripts(scriptData.scripts?.length ? scriptData.scripts : defaultScripts);
          setEscalationKeywords(scriptData.escalacion?.keywords?.length ? scriptData.escalacion.keywords : defaultKeywords);
          if (scriptData.chat_settings) {
            setChatSettings(scriptData.chat_settings);
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
        script_ventas: {
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
        const result = await createAgent({ nombre: "Nuevo Agente", ...payload });
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
    return <div className="space-y-4 max-w-6xl mx-auto p-4" suppressHydrationWarning>{[1,2,3].map(i => <Skeleton key={i} className="h-48 w-full rounded-2xl" />)}</div>;
  }
  return (
    <div className="space-y-6 animate-fade-in max-w-7xl mx-auto" suppressHydrationWarning>
      {/* Page Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 animate-entry">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-4 h-4 text-indigo-500" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-indigo-500/80">Estrategia Dinámica</span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-purple-600">Estrategia</span> de Ventas
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Configura las fases, reglas de oro y el comportamiento inteligente de tu agente.
          </p>
        </div>
        <button 
          onClick={handleSave}
          disabled={isSaving}
          className="flex items-center gap-2 px-6 py-3 bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-bold rounded-xl hover:scale-[1.02] active:scale-[0.98] transition-all shadow-lg">
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
      <div className="flex items-center gap-2 bg-white dark:bg-slate-800 rounded-xl p-2 border border-border overflow-x-auto">
        <button
          onClick={() => setActiveTab('phases')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium text-sm whitespace-nowrap transition-all ${
            activeTab === 'phases'
              ? 'bg-primary text-white shadow-glow'
              : 'hover:bg-muted'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          Fases de Venta
        </button>
        <button
          onClick={() => setActiveTab('rules')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium text-sm whitespace-nowrap transition-all ${
            activeTab === 'rules'
              ? 'bg-primary text-white shadow-glow'
              : 'hover:bg-muted'
          }`}
        >
          <Star className="w-4 h-4" />
          Reglas de Oro
        </button>
        <button
          onClick={() => setActiveTab('scripts')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium text-sm whitespace-nowrap transition-all ${
            activeTab === 'scripts'
              ? 'bg-primary text-white shadow-glow'
              : 'hover:bg-muted'
          }`}
        >
          <FileText className="w-4 h-4" />
          Respuestas Rápidas
        </button>
        <button
          onClick={() => setActiveTab('escalation')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium text-sm whitespace-nowrap transition-all ${
            activeTab === 'escalation'
              ? 'bg-primary text-white shadow-glow'
              : 'hover:bg-muted'
          }`}
        >
          <AlertCircle className="w-4 h-4" />
          Escalación
        </button>
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium text-sm whitespace-nowrap transition-all ${
            activeTab === 'chat'
              ? 'bg-primary text-white shadow-glow'
              : 'hover:bg-muted'
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          Ajustes del Chat
        </button>
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          {/* Sales Phases */}
          {activeTab === 'phases' && (
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-border overflow-hidden">
              <div className="p-5 border-b border-border">
                <h2 className="font-semibold flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-purple" />
                  Fases del Proceso de Venta
                </h2>
                <p className="text-sm text-muted-foreground mt-1">
                  Define cada etapa de la conversación para guiar al agente
                </p>
              </div>

              <div className="p-4 space-y-4">
                {salesPhases.map((phase, index) => (
                  <div
                    key={phase.id}
                    className={`p-5 rounded-xl border-2 transition-all ${
                      phase.enabled
                        ? 'border-border hover:border-primary/30 bg-muted/20'
                        : 'border-dashed border-muted-foreground/30 bg-muted/10 opacity-60'
                    }`}
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex items-center gap-2">
                        <GripVertical className="w-5 h-5 text-muted-foreground cursor-grab" />
                        <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center text-xl">
                          {getPhaseIcon(index)}
                        </div>
                      </div>

                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <h3 className="font-semibold">{phase.name}</h3>
                            <span className="px-2 py-1 rounded-full text-xs bg-secondary/10 text-secondary">
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
                            <div className="w-11 h-6 bg-slate-200 dark:bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                          </label>
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">{phase.description}</p>

                        <div className="mt-3 p-3 bg-white dark:bg-slate-700 rounded-xl">
                          <p className="text-xs text-muted-foreground mb-2">Frases clave:</p>
                          <div className="flex flex-wrap gap-2">
                            {phase.keyPhrases.map((phrase, i) => (
                              <span key={i} className="px-3 py-1.5 bg-primary/10 text-primary rounded-lg text-sm">
                                &quot;{phrase.substring(0, 30)}...&quot;
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
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-border overflow-hidden">
              <div className="p-5 border-b border-border">
                <h2 className="font-semibold flex items-center gap-2">
                  <Star className="w-5 h-5 text-accent" />
                  Reglas de Oro
                </h2>
                <p className="text-sm text-muted-foreground mt-1">
                  Principios inquebrantables que el agente debe seguir siempre
                </p>
              </div>

              <div className="p-4 space-y-3">
                {/* Add New Rule */}
                <div className="p-4 bg-muted/30 rounded-xl border border-dashed border-border">
                  <div className="flex items-center gap-3">
                    <input
                      type="text"
                      value={newRuleText}
                      onChange={(e) => setNewRuleText(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && addRule()}
                      placeholder="Escribe una nueva regla de oro..."
                      className="flex-1 px-4 py-2 bg-white dark:bg-slate-700 rounded-xl border border-border outline-none"
                    />
                    <button
                      onClick={addRule}
                      className="px-4 py-2 bg-primary text-white rounded-xl hover:bg-primary-dark transition-colors flex items-center gap-2"
                    >
                      <Plus className="w-4 h-4" />
                      Agregar
                    </button>
                  </div>
                </div>

                {goldenRules.map((rule, index) => (
                  <div
                    key={rule.id}
                    className={`p-4 rounded-xl border-2 transition-all ${
                      rule.enabled
                        ? 'border-border bg-white dark:bg-slate-700'
                        : 'border-dashed border-muted-foreground/30 bg-muted/10'
                    }`}
                  >
                    <div className="flex items-start gap-4">
                      <div className="w-6 h-6 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0 mt-1">
                        <Star className="w-3 h-3 text-accent" />
                      </div>

                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(rule.priority)}`}>
                              {rule.priority === 'high' && '⚡ Alta'}
                              {rule.priority === 'medium' && '📊 Media'}
                              {rule.priority === 'low' && '📉 Baja'}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <label className="relative inline-flex items-center cursor-pointer">
                              <input 
                                type="checkbox" 
                                checked={rule.enabled} 
                                onChange={() => toggleRule(rule.id)} 
                                className="sr-only peer" 
                              />
                              <div className="w-11 h-6 bg-slate-200 dark:bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                            </label>
                            <button
                              onClick={() => deleteRule(rule.id)}
                              className="p-2 hover:bg-pink/10 rounded-lg transition-colors text-pink"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                        <p className="font-medium mt-2">{rule.rule}</p>
                        <p className="text-sm text-muted-foreground mt-1">{rule.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Custom Scripts */}
          {activeTab === 'scripts' && (
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-border overflow-hidden">
              <div className="p-5 border-b border-border flex items-center justify-between">
                <div>
                  <h2 className="font-semibold flex items-center gap-2">
                    <FileText className="w-5 h-5 text-primary" />
                    Scripts Personalizados
                  </h2>
                  <p className="text-sm text-muted-foreground mt-1">
                    Respuestas predefinidas para situaciones específicas
                  </p>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-xl hover:bg-primary-dark transition-colors">
                  <Plus className="w-4 h-4" />
                  Nuevo Script
                </button>
              </div>

              <div className="p-4 space-y-4">
                {customScripts.map((script) => (
                  <div key={script.id} className="p-4 rounded-xl border border-border hover:border-primary/30 transition-colors">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-semibold">{script.name}</h3>
                        <p className="text-xs text-muted-foreground mt-1">{script.trigger}</p>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="px-3 py-1 bg-secondary/10 text-secondary rounded-full text-xs font-medium">
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
                          <div className="w-11 h-6 bg-slate-200 dark:bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                        </label>
                      </div>
                    </div>
                    <div className="mt-3 p-3 bg-muted/30 rounded-xl">
                      <p className="text-sm">{script.content}</p>
                    </div>
                    <div className="mt-3 flex items-center gap-2">
                      <button className="flex items-center gap-1 px-3 py-1.5 text-sm text-primary hover:bg-primary/10 rounded-lg transition-colors">
                        <Edit2 className="w-3 h-3" />
                        Editar
                      </button>
                      <button className="flex items-center gap-1 px-3 py-1.5 text-sm text-muted-foreground hover:bg-muted rounded-lg transition-colors">
                        <Copy className="w-3 h-3" />
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
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-border overflow-hidden">
              <div className="p-5 border-b border-border flex justify-between items-center">
                <div>
                  <h2 className="font-semibold flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-red-500" />
                    Palabras Clave de Escalación
                  </h2>
                  <p className="text-sm text-muted-foreground mt-1">
                    Si el cliente usa estas palabras, el agente transferirá la conversación a un humano.
                  </p>
                </div>
              </div>
              <div className="p-5">
                <div className="flex gap-3 mb-6">
                  <input
                    type="text"
                    value={newKeyword}
                    onChange={(e) => setNewKeyword(e.target.value)}
                    placeholder="Ej: hablar con supervisor..."
                    className="flex-1 px-4 py-3 bg-secondary/50 rounded-xl border border-border focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 outline-none"
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
                    className="px-6 py-3 bg-primary text-white rounded-xl hover:bg-primary-dark transition-all font-medium whitespace-nowrap">
                    Agregar
                  </button>
                </div>

                <div className="flex flex-wrap gap-2">
                  {escalationKeywords.map((keyword, index) => (
                    <div key={index} className="flex items-center gap-2 bg-secondary/50 px-4 py-2 rounded-full text-sm border border-border">
                      {keyword}
                      <button 
                        onClick={() => setEscalationKeywords(escalationKeywords.filter((_, i) => i !== index))}
                        className="text-muted-foreground hover:text-red-500 transition-colors">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  {escalationKeywords.length === 0 && (
                    <p className="text-sm text-muted-foreground p-4 text-center w-full">No hay palabras clave configuradas. El agente intentará resolver todo por sí mismo.</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Chat Settings */}
          {activeTab === 'chat' && (
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-border overflow-hidden">
              <div className="p-5 border-b border-border">
                <h2 className="font-semibold flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-blue-500" />
                  Ajustes del Widget de Chat
                </h2>
                <p className="text-sm text-muted-foreground mt-1">
                  Configura cómo se comporta el agente visualmente en el chat.
                </p>
              </div>
              <div className="p-5 space-y-6">
                
                {/* Typing Effect */}
                <div className="p-4 bg-secondary/30 rounded-xl border border-border">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h4 className="font-medium text-sm flex items-center gap-2">
                        Efecto &quot;Escribiendo...&quot;
                      </h4>
                      <p className="text-xs text-muted-foreground mt-1">Muestra un indicador de escritura antes de responder para simular comportamiento humano.</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        className="sr-only peer" 
                        checked={chatSettings.typing_effect}
                        onChange={() => setChatSettings({...chatSettings, typing_effect: !chatSettings.typing_effect})}
                      />
                      <div className="w-11 h-6 bg-slate-200 dark:bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    </label>
                  </div>
                  
                  {chatSettings.typing_effect && (
                    <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-border">
                      <div>
                        <label className="block text-xs font-medium mb-1 text-muted-foreground">Tiempo Mínimo (ms)</label>
                        <input 
                          type="number" 
                          value={chatSettings.typing_delay_min}
                          onChange={(e) => setChatSettings({...chatSettings, typing_delay_min: parseInt(e.target.value) || 1000})}
                          className="w-full px-3 py-2 bg-white dark:bg-slate-800 rounded-lg border border-border text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium mb-1 text-muted-foreground">Tiempo Máximo (ms)</label>
                        <input 
                          type="number" 
                          value={chatSettings.typing_delay_max}
                          onChange={(e) => setChatSettings({...chatSettings, typing_delay_max: parseInt(e.target.value) || 3000})}
                          className="w-full px-3 py-2 bg-white dark:bg-slate-800 rounded-lg border border-border text-sm"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Auto Greeting */}
                <div className="p-4 bg-secondary/30 rounded-xl border border-border">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h4 className="font-medium text-sm flex items-center gap-2">
                        Saludo Automático
                      </h4>
                      <p className="text-xs text-muted-foreground mt-1">El agente enviará el primer mensaje automáticamente cuando el usuario abra el chat.</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        className="sr-only peer" 
                        checked={chatSettings.auto_greeting}
                        onChange={() => setChatSettings({...chatSettings, auto_greeting: !chatSettings.auto_greeting})}
                      />
                      <div className="w-11 h-6 bg-slate-200 dark:bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    </label>
                  </div>
                  
                  {chatSettings.auto_greeting && (
                    <div className="mt-4 pt-4 border-t border-border">
                      <label className="block text-xs font-medium mb-1 text-muted-foreground">Retraso antes de enviar (ms)</label>
                      <input 
                        type="number" 
                        value={chatSettings.greeting_delay}
                        onChange={(e) => setChatSettings({...chatSettings, greeting_delay: parseInt(e.target.value) || 2000})}
                        className="w-full px-3 py-2 bg-white dark:bg-slate-800 rounded-lg border border-border text-sm"
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
          <div className="bg-gradient-mixed rounded-2xl p-6 text-white">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Sparkles className="w-5 h-5" />
              Resumen del Script
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center py-3 border-b border-white/20">
                <span className="text-white/80">Fases activas</span>
                <span className="font-bold text-xl">{salesPhases.filter(p => p.enabled).length}</span>
              </div>
              <div className="flex justify-between items-center py-3 border-b border-white/20">
                <span className="text-white/80">Reglas de oro</span>
                <span className="font-bold text-xl">{goldenRules.filter(r => r.enabled).length}</span>
              </div>
              <div className="flex justify-between items-center py-3 border-b border-white/20">
                <span className="text-white/80">Scripts custom</span>
                <span className="font-bold text-xl">{customScripts.length}</span>
              </div>
              <div className="flex justify-between items-center py-3">
                <span className="text-white/80">Frasas clave</span>
                <span className="font-bold text-xl">
                  {salesPhases.reduce((acc, p) => acc + p.keyPhrases.length, 0)}
                </span>
              </div>
            </div>
          </div>

          {/* Tips */}
          <div className="bg-accent/10 rounded-2xl p-5 border border-accent/20">
            <h3 className="font-semibold text-accent flex items-center gap-2 mb-4">
              <AlertCircle className="w-5 h-5" />
              Mejores Prácticas
            </h3>
            <ul className="space-y-3">
              <li className="flex items-start gap-2 text-sm">
                <CheckCircle2 className="w-4 h-4 text-secondary mt-0.5 flex-shrink-0" />
                <span>Usa frases cortas y directas para mejor engagement</span>
              </li>
              <li className="flex items-start gap-2 text-sm">
                <CheckCircle2 className="w-4 h-4 text-secondary mt-0.5 flex-shrink-0" />
                <span>Incluye el nombre del cliente para personalizar</span>
              </li>
              <li className="flex items-start gap-2 text-sm">
                <CheckCircle2 className="w-4 h-4 text-secondary mt-0.5 flex-shrink-0" />
                <span>Las reglas de alta prioridad deben ser claras</span>
              </li>
              <li className="flex items-start gap-2 text-sm">
                <CheckCircle2 className="w-4 h-4 text-secondary mt-0.5 flex-shrink-0" />
                <span>Siempre incluye opción de escalar a humano</span>
              </li>
            </ul>
          </div>

          {/* Preview */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-border p-5">
            <h3 className="font-semibold flex items-center gap-2 mb-4">
              <MessageSquare className="w-5 h-5 text-pink" />
              Vista Previa
            </h3>
            <div className="bg-muted/50 rounded-xl p-4">
              <div className="space-y-3">
                <div className="bg-white dark:bg-slate-700 rounded-xl p-3 text-sm">
                  <span className="text-primary font-medium">Fase 1:</span> Saludo
                </div>
                <div className="flex justify-center">
                  <ChevronRight className="w-4 h-4 text-muted-foreground rotate-90" />
                </div>
                <div className="bg-white dark:bg-slate-700 rounded-xl p-3 text-sm">
                  <span className="text-purple font-medium">Fase 2:</span> Descubrimiento
                </div>
                <div className="flex justify-center">
                  <ChevronRight className="w-4 h-4 text-muted-foreground rotate-90" />
                </div>
                <div className="bg-white dark:bg-slate-700 rounded-xl p-3 text-sm">
                  <span className="text-secondary font-medium">Fase 3:</span> Presentación
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
