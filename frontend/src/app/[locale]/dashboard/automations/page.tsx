"use client";

import { useState } from "react";
import { 
  ShieldAlert, Settings, Zap, ArrowRight, Save, RotateCcw,
  Check, Loader2, Bot, AlertTriangle, Info, ToggleLeft, ToggleRight
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

export default function PolicyEnginePage() {
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Policy States
  const [handoffRetries, setHandoffRetries] = useState(3);
  const [idleTimeout, setIdleTimeout] = useState(15);
  const [strictMode, setStrictMode] = useState(true);
  const [maxTokens, setMaxTokens] = useState(1500);

  const handleSave = async () => {
    setIsSaving(true);
    // Simulate API Call
    await new Promise(r => setTimeout(r, 1200));
    
    // In a real scenario:
    // await updatePolicyEngineConfig({ handoffRetries, idleTimeout, strictMode, maxTokens });
    
    setIsSaving(false);
    setSaved(true);
    toast.success("Reglas de Automatización actualizadas correctamente");
    setTimeout(() => setSaved(false), 3000);
  };

  const reset = () => {
    setHandoffRetries(3);
    setIdleTimeout(15);
    setStrictMode(true);
    setMaxTokens(1500);
    toast.info("Valores por defecto restaurados");
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-7xl mx-auto pb-20">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ShieldAlert className="w-4 h-4 text-emerald-500" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-emerald-500/80">Policy Engine</span>
          </div>
          <h1 className="text-3xl font-black text-white/90 tracking-tight">
            Reglas de <span className="text-emerald-500">Automatización</span>
          </h1>
          <p className="text-sm text-white/50 font-light mt-1">
            Configura los límites operacionales, seguridad y reglas de escalamiento de Yanua.
          </p>
        </div>
        <div className="flex items-center gap-3 w-full md:w-auto">
          <Button variant="outline" onClick={reset} className="flex-1 md:flex-none rounded-xl border-white/10 bg-black/20 text-white/70 hover:text-white hover:bg-white/5 h-11 transition-all">
            <RotateCcw className="w-4 h-4 mr-2" /> Resetear
          </Button>
          <Button
            onClick={handleSave}
            disabled={isSaving}
            className="flex-1 md:flex-none rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white h-11 px-6 shadow-[0_0_20px_rgba(16,185,129,0.3)] transition-all font-bold"
          >
            {isSaving ? (
              <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Aplicando...</>
            ) : saved ? (
              <><Check className="w-4 h-4 mr-2" /> Aplicado</>
            ) : (
              <><Save className="w-4 h-4 mr-2" /> Guardar Reglas</>
            )}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Settings */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Card 1: Handoff & Escalamiento */}
          <div className="bg-black/40 backdrop-blur-xl rounded-[24px] border border-white/5 p-8 shadow-xl">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-white/90 flex items-center gap-2">
                <Bot className="w-5 h-5 text-emerald-500" />
                Escalamiento a Humano (Handoff)
              </h2>
            </div>

            <div className="space-y-8">
              <div>
                <div className="flex justify-between items-center mb-4">
                  <label className="text-sm font-medium text-white/80">Reintentos de Fallback</label>
                  <span className="text-sm font-black text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
                    {handoffRetries} {handoffRetries === 1 ? 'vez' : 'veces'}
                  </span>
                </div>
                <input 
                  type="range" 
                  min="1" max="5" 
                  value={handoffRetries} 
                  onChange={(e) => setHandoffRetries(Number(e.target.value))}
                  className="w-full accent-emerald-500 h-1.5 bg-white/10 rounded-full appearance-none cursor-pointer"
                />
                <p className="text-xs text-white/40 mt-3">
                  Si Yanua no entiende al cliente después de {handoffRetries} intentos consecutivos, pausará el flujo y alertará a un supervisor en la Torre de Control.
                </p>
              </div>

              <div>
                <div className="flex justify-between items-center mb-4">
                  <label className="text-sm font-medium text-white/80">Timeout por Inactividad (Minutos)</label>
                  <span className="text-sm font-black text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
                    {idleTimeout} min
                  </span>
                </div>
                <input 
                  type="range" 
                  min="5" max="60" step="5"
                  value={idleTimeout} 
                  onChange={(e) => setIdleTimeout(Number(e.target.value))}
                  className="w-full accent-emerald-500 h-1.5 bg-white/10 rounded-full appearance-none cursor-pointer"
                />
                <p className="text-xs text-white/40 mt-3">
                  Tiempo que la IA esperará la respuesta del lead antes de archivar la conversación en estado inactivo.
                </p>
              </div>
            </div>
          </div>

          {/* Card 2: Security & Guardrails */}
          <div className="bg-black/40 backdrop-blur-xl rounded-[24px] border border-white/5 p-8 shadow-xl">
            <h2 className="text-lg font-bold text-white/90 flex items-center gap-2 mb-6">
              <ShieldAlert className="w-5 h-5 text-emerald-500" />
              Guardrails de Comportamiento
            </h2>

            <div className="space-y-6">
              <div className="flex items-start justify-between p-4 bg-white/5 border border-white/5 rounded-2xl">
                <div>
                  <h3 className="text-sm font-bold text-white/90">Modo Estricto de Tópicos</h3>
                  <p className="text-xs text-white/50 mt-1 max-w-sm">
                    Bloquea respuestas a temas no relacionados con tu empresa (ej. política, programación, chistes). Yanua dirá cortésmente que solo puede asistir con ventas.
                  </p>
                </div>
                <button 
                  onClick={() => setStrictMode(!strictMode)}
                  className="flex-shrink-0 ml-4 transition-transform active:scale-90 text-emerald-500"
                >
                  {strictMode ? <ToggleRight className="w-10 h-10" /> : <ToggleLeft className="w-10 h-10 text-white/20" />}
                </button>
              </div>

              <div>
                <div className="flex justify-between items-center mb-4 mt-6">
                  <label className="text-sm font-medium text-white/80">Límite de Tokens por Conversación</label>
                  <span className="text-sm font-black text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
                    {maxTokens.toLocaleString()} tokens
                  </span>
                </div>
                <input 
                  type="range" 
                  min="500" max="5000" step="100"
                  value={maxTokens} 
                  onChange={(e) => setMaxTokens(Number(e.target.value))}
                  className="w-full accent-emerald-500 h-1.5 bg-white/10 rounded-full appearance-none cursor-pointer"
                />
                <p className="text-xs text-white/40 mt-3">
                  Previene ataques de "prompt injection" infinito. Si un usuario consume más de este límite en una sola sesión, la IA pasará al humano.
                </p>
              </div>
            </div>
          </div>

        </div>

        {/* Right Column - Status */}
        <div className="space-y-6">
          <div className="rounded-[24px] p-8 text-white relative overflow-hidden" style={{ background: `linear-gradient(135deg, #10b981 0%, #064e3b 100%)`, boxShadow: `0 10px 40px rgba(16, 185, 129, 0.2)` }}>
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none"></div>
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Zap className="w-5 h-5" />
              Impacto de Políticas
            </h3>
            <p className="text-sm text-emerald-100 font-light mb-6">
              Estas reglas afectan directamente cómo el orquestador interactúa en tiempo real con los usuarios finales.
            </p>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between items-center py-2 border-b border-emerald-400/20">
                <span className="text-emerald-100">Protección de Gasto</span>
                <span className="font-bold">Activo</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-emerald-400/20">
                <span className="text-emerald-100">Handoffs Proyectados</span>
                <span className="font-bold text-white bg-emerald-900/50 px-2 py-0.5 rounded">~12% / día</span>
              </div>
            </div>
          </div>

          <div className="bg-amber-500/5 rounded-[24px] p-6 border border-amber-500/20 backdrop-blur-sm">
            <h3 className="font-bold text-amber-500 flex items-center gap-2 mb-4">
              <AlertTriangle className="w-5 h-5" />
              Advertencia Operacional
            </h3>
            <p className="text-sm text-white/60 font-light leading-relaxed">
              Disminuir los reintentos de Fallback a 1 incrementará la carga de trabajo de tu equipo humano drásticamente. Úsalo solo en periodos de alto nivel de soporte personalizado.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
