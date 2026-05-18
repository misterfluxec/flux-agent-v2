'use client';

import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, Bot, Sparkles, Rocket, ChevronRight, ChevronLeft, 
  UploadCloud, ArrowLeft, MessageSquare, Check, 
  Loader2, Globe, MessageCircle, Smile, SmilePlus, Network, BrainCircuit, ScanLine
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { createAgent, uploadAgentAvatar, uploadDocument, sendChat, fetchAgents } from '@/lib/api';
import { useRouter } from 'next/navigation';

interface QuickStartModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (agentId: string) => void;
}

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

export default function QuickStartModal({ isOpen, onClose, onComplete }: QuickStartModalProps) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
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

  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!isOpen || !mounted) return null;

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
      setLoading(true);
      try {
        const payload = {
          name: name,
          area: industry,
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
        setLoading(false);
      }
      return;
    }

    if (step === 4) {
      if (file && agentId) {
        setLoading(true);
        try {
          await uploadDocument(file, agentId);
          toast.success('Conocimiento ingerido.');
        } catch (error) {
          toast.error('Error al cargar archivo.');
        } finally {
          setLoading(false);
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
      onComplete(agentId!);
    } else {
      setStep(step + 1);
    }
  };

  const handleSendMessage = async () => {
    if (!testMessage || !agentId) return;
    
    const newMsg = { role: 'user' as const, content: testMessage };
    setChatHistory([...chatHistory, newMsg]);
    setTestMessage('');
    setLoading(true);

    try {
      const response = await sendChat({
        session_id: 'test-quickstart',
        mensaje: testMessage,
        agent_id: agentId,
        historial: chatHistory.map(m => ({ role: m.role === 'user' ? 'user' : 'assistant', contenido: m.content })),
        configuracion: { name: name, mood: 'profesional', business_type: industry }
      });
      
      setChatHistory(prev => [...prev, { role: 'assistant', content: response.respuesta }]);
    } catch (error: any) {
      toast.error(`Error de conexión.`);
      setChatHistory(prev => [...prev, { role: 'assistant', content: 'Lo siento, tuve un problema técnico. Intenta de nuevo.' }]);
    } finally {
      setLoading(false);
    }
  };

  return createPortal(
    <motion.div 
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="fixed inset-0 w-screen h-screen z-[9999999] flex items-center justify-center p-4 bg-black/90 backdrop-blur-xl"
      onClick={onClose}
    >
      <motion.div 
        initial={{ scale: 0.95, y: 20, opacity: 0 }} animate={{ scale: 1, y: 0, opacity: 1 }} transition={{ type: 'spring', damping: 25 }}
        className="relative w-full max-w-3xl rounded-[2rem] border border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.8)] flex flex-col max-h-[90vh] bg-[#0A0A0B] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-8 py-6 border-b border-white/5 flex items-center justify-between bg-white/[0.02] backdrop-blur-md relative z-20">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center border border-primary/20 shadow-[0_0_15px_rgba(6,182,212,0.15)]">
              <Sparkles className="w-6 h-6 text-primary" />
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
                      i === step ? 'w-8 bg-primary shadow-[0_0_10px_rgba(6,182,212,0.5)]' : i < step ? 'w-4 bg-primary/40' : 'w-2 bg-white/10'
                    }`} 
                  />
                ))}
                <span className="text-[9px] text-primary ml-3 font-black uppercase tracking-[0.2em]">Fase {step} de 6</span>
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
                  <label className="absolute -top-2 left-4 px-2 bg-[#0A0A0B] text-[9px] font-black text-primary uppercase tracking-[0.2em] z-10">
                    Nombre del Agente
                  </label>
                  <Input 
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Ej: Sofia"
                    className="h-14 rounded-2xl bg-white/[0.02] border-white/10 text-white text-center text-sm font-semibold focus:border-primary/50 focus:bg-primary/[0.02] transition-all placeholder:text-white/20"
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
                        industry === ind.id ? 'border-primary/50 bg-primary/10 shadow-[0_0_20px_rgba(6,182,212,0.15)] text-primary' : 'border-white/5 bg-white/[0.02] text-white/50 hover:bg-white/5 hover:text-white'
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
                    <label className="text-[10px] font-black text-primary uppercase tracking-[0.2em] ml-2 flex items-center gap-2">
                      <Sparkles className="w-3 h-3" /> System Prompt Generado
                    </label>
                    <textarea 
                      value={systemPrompt}
                      onChange={(e) => setSystemPrompt(e.target.value)}
                      placeholder="Las reglas generadas aparecerán aquí y podrás editarlas antes de continuar..."
                      className="w-full h-full min-h-[220px] bg-black/50 border border-primary/20 rounded-2xl p-4 text-xs font-mono text-primary/90 resize-none outline-none focus:border-primary transition-all"
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
                  onClick={() => fileInputRef.current?.click()}
                  className="max-w-md mx-auto p-12 border border-dashed border-white/20 rounded-[2rem] bg-white/[0.01] hover:border-primary/50 hover:bg-primary/[0.02] transition-all text-center cursor-pointer group relative overflow-hidden"
                >
                  <ScanLine className="w-12 h-12 mx-auto text-white/20 group-hover:text-primary transition-colors mb-4" />
                  <p className="text-white font-bold tracking-wide">{file ? file.name : 'Click para subir archivo'}</p>
                  <p className="text-[10px] text-white/30 uppercase tracking-widest mt-2">PDF, XLSX o CSV hasta 50MB</p>
                  <input type="file" ref={fileInputRef} onChange={(e) => setFile(e.target.files?.[0] || null)} className="hidden" />
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
                    { id: 'web', title: 'Widget Web (Prueba Mágica)', icon: Globe, color: 'text-primary' },
                    { id: 'whatsapp', title: 'WhatsApp Business', icon: MessageCircle, color: 'text-green-400' },
                  ].map(item => (
                    <button 
                      key={item.id}
                      onClick={() => setChannel(item.id as any)}
                      className={`p-5 rounded-2xl border transition-all text-left flex items-center gap-4 ${
                        channel === item.id ? 'border-primary/40 bg-primary/10 shadow-[0_0_20px_rgba(6,182,212,0.15)]' : 'border-white/10 bg-white/[0.02] hover:border-white/20'
                      }`}
                    >
                      <div className={`p-3 rounded-xl bg-black/40 border border-white/5 ${item.color}`}>
                        <item.icon size={24} />
                      </div>
                      <h4 className="font-bold text-white tracking-wide">{item.title}</h4>
                      {channel === item.id && <Check className="ml-auto text-primary" />}
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
                            ? 'bg-primary text-white rounded-2xl rounded-tr-sm shadow-[0_5px_15px_rgba(6,182,212,0.2)]' 
                            : 'bg-white/10 text-white/90 rounded-2xl rounded-tl-sm border border-white/5 backdrop-blur-md'
                        }`}>
                          {m.content}
                        </div>
                      </div>
                    ))}
                    {loading && (
                      <div className="flex justify-start">
                        <div className="bg-white/5 border border-white/5 p-4 rounded-2xl rounded-tl-sm backdrop-blur-md">
                          <Loader2 size={16} className="animate-spin text-primary" />
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div className="relative">
                    <Input 
                      value={testMessage}
                      onChange={(e) => setTestMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                      placeholder="Pregúntale algo sobre el negocio..."
                      className="h-14 pr-14 rounded-2xl bg-white/[0.03] border-white/10 text-white placeholder:text-white/20 focus:border-primary/50 focus:bg-primary/[0.02]"
                    />
                    <button 
                      onClick={handleSendMessage}
                      disabled={loading || !testMessage}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-2.5 bg-primary rounded-xl text-white hover:bg-primary/90 disabled:opacity-30 disabled:bg-white/10 transition-colors shadow-[0_0_15px_rgba(6,182,212,0.3)]"
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
            onClick={() => setStep(step - 1)}
            disabled={step === 1 || loading}
            className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 hover:text-white hover:bg-transparent"
          >
            <ArrowLeft className="w-3 h-3 mr-2" /> Atrás
          </Button>
          
          <Button 
            onClick={handleNext}
            disabled={loading}
            variant="outline"
            className="h-12 px-8 rounded-full border-primary/40 text-primary hover:bg-primary/10 text-[11px] font-black uppercase tracking-[0.2em] backdrop-blur-md transition-all shadow-[0_0_20px_rgba(6,182,212,0.15)] group relative overflow-hidden"
          >
            <span className="relative z-10 flex items-center">
              {loading ? (
                <><Loader2 size={14} className="mr-2 animate-spin" /> Procesando...</>
              ) : step === 6 ? (
                <>Cerrar y Usar <Check size={14} className="ml-2" /></>
              ) : (
                <>Siguiente Fase <ChevronRight size={14} className="ml-1 group-hover:translate-x-1 transition-transform" /></>
              )}
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-primary/0 via-primary/10 to-primary/0 -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]" />
          </Button>
        </div>
      </motion.div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
      `}</style>
    </motion.div>,
    document.body
  );
}
