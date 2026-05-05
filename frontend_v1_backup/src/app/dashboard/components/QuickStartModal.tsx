'use client';

import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { 
  X, Bot, Sparkles, Rocket, ChevronRight, ChevronLeft, 
  UploadCloud, Link as LinkIcon, MessageSquare, Check, 
  Loader2, User, Building, Send, Globe, MessageCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { createAgent, uploadAgentAvatar, uploadDocument, ingestUrl, sendChat, fetchAgents } from '@/lib/api';
import { useRouter } from 'next/navigation';

interface QuickStartModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (agentId: string) => void;
}

export default function QuickStartModal({ isOpen, onClose, onComplete }: QuickStartModalProps) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [agentId, setAgentId] = useState<string | null>(null);

  // Form States
  const [name, setName] = useState('');
  const [avatar, setAvatar] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [role, setRole] = useState<'orchestrator' | 'specialist'>('orchestrator');
  const [industry, setIndustry] = useState('');
  const [tone, setTone] = useState('amigable');
  
  const [knowledgeType, setKnowledgeType] = useState<'sheets' | 'file' | 'url'>('sheets');
  const [url, setUrl] = useState('');
  const [file, setFile] = useState<File | null>(null);
  
  const [channel, setChannel] = useState<'whatsapp' | 'web' | 'api'>('web');
  
  const [testMessage, setTestMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<{ role: 'user' | 'assistant'; content: string }[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const router = useRouter();

  const [mounted, setMounted] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  useEffect(() => {
    setMounted(true);
    const init = async () => {
      try {
        const agents = await fetchAgents();
        if (agents && agents.length > 0) {
          // El agente "Yanua" (u otro) ya existe
          const firstAgent = agents[0];
          setAgentId(firstAgent.id);
          setName(firstAgent.nombre);
          localStorage.setItem('flux_agent_id', firstAgent.id);
          localStorage.setItem('flux_agent_nombre', firstAgent.nombre);
          
          // Saltamos directamente a la fase de Conocimiento (Paso 3)
          setStep(3);
        }
      } catch (error) {
        console.warn("Error verificando agentes existentes", error);
      } finally {
        setInitialLoading(false);
      }
    };
    init();
  }, []);

  if (!isOpen || !mounted || initialLoading) return null;

  const handleNext = async () => {
    if (step === 1 && !name) {
      toast.error('Por favor, ingresa un nombre para tu agente');
      return;
    }

    if (step === 2) {
      setLoading(true);
      try {
        const payload = {
          nombre: name,
          area: industry || 'ventas',
          tipo_negocio: industry,
          humor: tone,
          tono: tone,
          genero: 'femenino',
          personalidad: `Asistente de ventas ${industry ? `de ${industry}` : 'profesional'}`,
          modelo: 'qwen2.5:3b',
          temperatura: 0.7,
          max_tokens: 512,
          canales: ['web_chat'],
          script_ventas: {
            rol_agente: { tipo: role, area: industry }
          }
        };
        const result = await createAgent(payload);
        setAgentId(result.agente_id);
        
        if (avatar) {
          try {
            await uploadAgentAvatar(result.agente_id, avatar);
          } catch (avatarError) {
            console.warn("Error uploading avatar:", avatarError);
          }
        }
        
        localStorage.setItem('flux_agent_id', result.agente_id);
        localStorage.setItem('flux_agent_nombre', name);
        localStorage.setItem('flux_phase_1', 'true');
        setStep(3);
      } catch (error: any) {
        console.error("Error creating agent:", error);
        const errorMsg = error.response?.data?.detail || error.message || 'Error desconocido';
        toast.error(`Error al crear el agente: ${errorMsg}`);
      } finally {
        setLoading(false);
      }
      return;
    }

    if (step === 3) {
      if (!agentId) {
        toast.error('Error: agente no creado. Por favor, vuelve al paso anterior.');
        setStep(2);
        return;
      }
      
      if (file || url) {
        setLoading(true);
        try {
          if (knowledgeType === 'file' && file) {
            const result = await uploadDocument(file, agentId!);
            toast.success(`Archivo cargado: ${result.job_id}`);
          } else if (knowledgeType === 'url' && url) {
            const result = await ingestUrl(url, agentId!);
            toast.success(`URL procesada: ${result.job_id}`);
          } else if (knowledgeType === 'sheets') {
            // Redirigir al wizard completo de Sheets
            onClose();
            router.push('/dashboard/centro-de-datos');
            return;
          }
          localStorage.setItem('flux_phase_3', 'true');
        } catch (error: any) {
          console.error("Error uploading knowledge:", error);
          const errorMsg = error.response?.data?.detail || error.message || 'Error desconocido';
          toast.error(`Error al cargar conocimiento: ${errorMsg}. Puedes continuar sin conocimiento o intentar de nuevo.`);
        } finally {
          setLoading(false);
        }
      }
      setStep(4);
      return;
    }

    if (step === 4) {
      localStorage.setItem('flux_phase_4', 'true');
      setStep(5);
      return;
    }

    if (step === 5) {
      onComplete(agentId!);
    } else {
      setStep(step + 1);
    }
  };

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      setAvatar(f);
      setAvatarPreview(URL.createObjectURL(f));
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
        session_id: 'test-session',
        mensaje: testMessage,
        agent_id: agentId,
        historial: chatHistory.map(m => ({ rol: m.role === 'user' ? 'user' : 'assistant', contenido: m.content })),
        configuracion: { nombre: name, humor: tone, tipo_negocio: industry }
      });
      
      setChatHistory(prev => [...prev, { role: 'assistant', content: response.respuesta }]);
      localStorage.setItem('flux_phase_5', 'true');
    } catch (error: any) {
      console.error("Error en chat:", error);
      const errorMsg = error.response?.data?.detail || error.message || 'Error desconocido';
      toast.error(`Error al probar el agente: ${errorMsg}`);
      setChatHistory(prev => [...prev, { role: 'assistant', content: 'Lo siento, tuve un problema técnico. Intenta de nuevo.' }]);
    } finally {
      setLoading(false);
    }
  };

  return createPortal(
    <div 
      className="fixed inset-0 w-screen h-screen z-[9999999] flex items-center justify-center p-4 bg-black/90 backdrop-blur-md animate-in fade-in duration-300 cursor-pointer overflow-hidden"
      onClick={onClose}
    >
      <div 
        className="relative w-full max-w-2xl border border-slate-800 rounded-3xl shadow-[0_0_50px_rgba(0,0,0,0.8)] overflow-hidden flex flex-col max-h-[95vh] animate-in zoom-in-95 duration-300 cursor-default"
        style={{ backgroundColor: '#0f172a' }}
        onClick={(e) => e.stopPropagation()}
      >
        
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600/20 flex items-center justify-center text-indigo-500">
              <Sparkles size={20} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight">Entrenamiento Rápido</h2>
              <div className="flex items-center gap-1 mt-0.5">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div 
                    key={i} 
                    className={`h-1 rounded-full transition-all duration-300 ${
                      i === step ? 'w-6 bg-indigo-500' : i < step ? 'w-4 bg-indigo-900' : 'w-2 bg-slate-800'
                    }`} 
                  />
                ))}
                <span className="text-[10px] text-slate-500 ml-2 font-bold uppercase tracking-widest">Paso {step} de 5</span>
              </div>
            </div>
          </div>
          <button 
            onClick={(e) => {
              e.stopPropagation();
              onClose();
            }} 
            className="p-2 hover:bg-slate-800 rounded-full text-slate-300 hover:text-white transition-colors bg-slate-800/50"
            aria-label="Cerrar"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-8">
          
          {/* STEP 1: Identity */}
          {step === 1 && (
            <div className="space-y-8 animate-in slide-in-from-right-4 duration-300">
              <div className="text-center space-y-2">
                <h3 className="text-2xl font-bold text-white">Identidad Visual</h3>
                <p className="text-slate-400 text-sm">Dale un rostro y un nombre a tu asistente.</p>
              </div>
              
              <div className="flex flex-col items-center gap-6">
                <div className="relative group">
                  <div 
                    onClick={() => fileInputRef.current?.click()}
                    className="w-32 h-32 rounded-full bg-slate-800 border-4 border-slate-700 flex items-center justify-center overflow-hidden cursor-pointer group-hover:border-indigo-500 transition-all shadow-xl"
                  >
                    {avatarPreview ? (
                      <img src={avatarPreview} alt="Preview" className="w-full h-full object-cover" />
                    ) : (
                      <div className="flex flex-col items-center text-slate-500 group-hover:text-indigo-400">
                        <UploadCloud size={32} />
                        <span className="text-[10px] font-bold mt-1">SUBIR</span>
                      </div>
                    )}
                  </div>
                  <input type="file" ref={fileInputRef} onChange={handleAvatarChange} className="hidden" accept="image/*" />
                </div>
                
                <div className="w-full max-w-sm space-y-2">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Nombre del Agente</label>
                  <Input 
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Ej: Sofia"
                    className="h-14 rounded-2xl bg-slate-800 border-slate-700 text-white text-lg font-semibold focus:ring-indigo-500/20 placeholder:text-slate-600"
                  />
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: Role & Tone */}
          {step === 2 && (
            <div className="space-y-8 animate-in slide-in-from-right-4 duration-300">
              <div className="text-center space-y-2">
                <h3 className="text-2xl font-bold text-white">Rol y Personalidad</h3>
                <p className="text-slate-400 text-sm">¿Cómo quieres que se comporte tu agente?</p>
              </div>

              <div className="grid gap-6">
                <div className="space-y-3">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Rol Principal</label>
                  <div className="grid grid-cols-2 gap-4">
                    <button 
                      onClick={() => setRole('orchestrator')}
                      className={`p-4 rounded-2xl border-2 flex flex-col items-center gap-2 transition-all ${
                        role === 'orchestrator' ? 'border-indigo-500 bg-indigo-500/5 text-indigo-400' : 'border-slate-800 bg-slate-900 text-slate-500 hover:border-slate-700'
                      }`}
                    >
                      <Sparkles size={24} />
                      <span className="font-bold text-sm">Orquestador</span>
                      <span className="text-[10px] opacity-90 text-center leading-tight">Punto de contacto y derivación</span>
                    </button>
                    <button 
                      onClick={() => setRole('specialist')}
                      className={`p-4 rounded-2xl border-2 flex flex-col items-center gap-2 transition-all ${
                        role === 'specialist' ? 'border-indigo-500 bg-indigo-500/5 text-indigo-400' : 'border-slate-800 bg-slate-900 text-slate-500 hover:border-slate-700'
                      }`}
                    >
                      <Rocket size={24} />
                      <span className="font-bold text-sm">Especialista</span>
                      <span className="text-[10px] opacity-90 text-center leading-tight">Experto en un área puntual</span>
                    </button>
                  </div>
                </div>

                <div className="space-y-3">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Giro del Negocio</label>
                  <select 
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    className="w-full h-12 bg-slate-800 border-slate-700 rounded-2xl px-4 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  >
                    <option value="">Seleccionar...</option>
                    <option value="ecommerce">E-commerce</option>
                    <option value="services">Servicios</option>
                    <option value="realestate">Inmobiliaria</option>
                    <option value="health">Salud</option>
                  </select>
                </div>

                <div className="space-y-3">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Tono de Voz</label>
                  <div className="flex flex-wrap gap-2">
                    {['profesional', 'amigable', 'casual', 'energetico'].map(t => (
                      <button 
                        key={t}
                        onClick={() => setTone(t)}
                        className={`px-4 py-2 rounded-full border text-xs font-bold transition-all ${
                          tone === t ? 'bg-indigo-500 border-indigo-500 text-white' : 'bg-slate-800 border-slate-700 text-slate-400'
                        }`}
                      >
                        {t === 'profesional' ? '👔 Profesional' : t === 'amigable' ? '😊 Amigable' : t === 'casual' ? '☕ Casual' : '⚡ Energético'}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: Knowledge */}
          {step === 3 && (
            <div className="space-y-8 animate-in slide-in-from-right-4 duration-300">
              <div className="text-center space-y-2">
                <div className="inline-flex items-center justify-center p-3 bg-indigo-500/10 rounded-full mb-2">
                  <Bot size={32} className="text-indigo-400" />
                </div>
                <h3 className="text-2xl font-bold text-white">¡Bienvenido! He creado a {name} para ti</h3>
                <p className="text-slate-400 text-sm">¿De dónde quieres que aprenda hoy?</p>
              </div>

              <div className="space-y-6">
                <div className="flex bg-slate-800/50 p-1 rounded-2xl border border-slate-700">
                  <button 
                    onClick={() => setKnowledgeType('sheets')}
                    className={`flex-1 py-2 rounded-xl text-xs font-bold transition-all ${knowledgeType === 'sheets' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-500 hover:text-slate-300'}`}
                  >
                    Google Sheets
                  </button>
                  <button 
                    onClick={() => setKnowledgeType('file')}
                    className={`flex-1 py-2 rounded-xl text-xs font-bold transition-all ${knowledgeType === 'file' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-500 hover:text-slate-300'}`}
                  >
                    Archivo Local
                  </button>
                  <button 
                    onClick={() => setKnowledgeType('url')}
                    className={`flex-1 py-2 rounded-xl text-xs font-bold transition-all ${knowledgeType === 'url' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-500 hover:text-slate-300'}`}
                  >
                    Sitio Web
                  </button>
                </div>

                {knowledgeType === 'sheets' && (
                  <div className="p-8 border-2 border-indigo-500/30 rounded-3xl bg-indigo-500/5 text-center">
                    <Building size={48} className="mx-auto text-indigo-400 mb-4" />
                    <h4 className="text-white font-bold text-lg mb-2">Sincronización en Tiempo Real</h4>
                    <p className="text-sm text-slate-400 mb-6">Conecta tu inventario o base de datos de Google Sheets. Tu agente aprenderá automáticamente de cualquier cambio que hagas.</p>
                    <Button onClick={() => { onClose(); router.push('/dashboard/centro-de-datos'); }} className="bg-[#0F9D58] hover:bg-[#0b8043] text-white rounded-xl px-8">
                      Conectar Google Sheets
                    </Button>
                  </div>
                )}

                {knowledgeType === 'file' && (
                  <div 
                    onClick={() => fileInputRef.current?.click()}
                    className="p-12 border-2 border-dashed border-slate-700 rounded-3xl bg-slate-800/20 hover:border-indigo-500/50 hover:bg-slate-800/40 transition-all text-center cursor-pointer group"
                  >
                    <UploadCloud size={48} className="mx-auto text-slate-600 group-hover:text-indigo-400 mb-4" />
                    <p className="text-slate-300 font-bold">{file ? file.name : 'Selecciona un archivo'}</p>
                    <p className="text-xs text-slate-500 mt-2">PDF, XLSX o CSV hasta 50MB</p>
                    <input type="file" ref={fileInputRef} onChange={(e) => setFile(e.target.files?.[0] || null)} className="hidden" />
                  </div>
                )}
                
                {knowledgeType === 'url' && (
                  <div className="space-y-4">
                    <div className="relative">
                      <Globe size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                      <Input 
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder="https://tu-sitio.com"
                        className="h-14 pl-12 rounded-2xl bg-slate-800 border-slate-700"
                      />
                    </div>
                    <p className="text-xs text-slate-500 text-center">La IA navegará por tu sitio para extraer información.</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* STEP 4: Channels */}
          {step === 4 && (
            <div className="space-y-8 animate-in slide-in-from-right-4 duration-300">
              <div className="text-center space-y-2">
                <h3 className="text-2xl font-bold text-white">Canales de Atención</h3>
                <p className="text-slate-400 text-sm">¿Dónde quieres que atienda tu agente?</p>
              </div>

              <div className="grid gap-4">
                {[
                  { id: 'web', title: 'Widget Web', desc: 'Embebe el chat en tu sitio web', icon: Globe, color: 'text-blue-400' },
                  { id: 'whatsapp', title: 'WhatsApp Business', desc: 'Conecta vía Evolution API', icon: MessageCircle, color: 'text-emerald-400' },
                  { id: 'api', title: 'API REST', desc: 'Conexión personalizada para devs', icon: Rocket, color: 'text-purple-400' },
                ].map(item => (
                  <button 
                    key={item.id}
                    onClick={() => setChannel(item.id as any)}
                    className={`p-5 rounded-2xl border-2 flex items-center gap-4 transition-all text-left ${
                      channel === item.id ? 'border-indigo-500 bg-indigo-500/5' : 'border-slate-800 bg-slate-900 hover:border-slate-700'
                    }`}
                  >
                    <div className={`p-3 rounded-xl bg-slate-800 ${item.color}`}>
                      <item.icon size={24} />
                    </div>
                    <div>
                      <h4 className="font-bold text-white">{item.title}</h4>
                      <p className="text-xs text-slate-500">{item.desc}</p>
                    </div>
                    {channel === item.id && <Check className="ml-auto text-indigo-500" />}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* STEP 5: Test Chat */}
          {step === 5 && (
            <div className="flex flex-col h-full space-y-4 animate-in slide-in-from-right-4 duration-300">
              <div className="text-center space-y-1">
                <h3 className="text-xl font-bold text-white">Prueba de Fuego 🔥</h3>
                <p className="text-slate-400 text-xs">Habla con {name} para validar su entrenamiento.</p>
              </div>

              <div className="flex-1 bg-slate-950/50 rounded-2xl border border-slate-800 flex flex-col p-4 min-h-[300px]">
                <div className="flex-1 overflow-y-auto space-y-3 mb-4 pr-2 custom-scrollbar">
                  {chatHistory.length === 0 && (
                    <div className="h-full flex items-center justify-center text-slate-600 italic text-sm">
                      Escribe algo para comenzar...
                    </div>
                  )}
                  {chatHistory.map((m, i) => (
                    <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[80%] p-3 rounded-2xl text-sm ${
                        m.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-sm' : 'bg-slate-800 text-slate-200 rounded-tl-sm'
                      }`}>
                        {m.content}
                      </div>
                    </div>
                  ))}
                  {loading && (
                    <div className="flex justify-start">
                      <div className="bg-slate-800 p-3 rounded-2xl rounded-tl-sm">
                        <Loader2 size={16} className="animate-spin text-slate-400" />
                      </div>
                    </div>
                  )}
                </div>
                
                <div className="relative">
                  <Input 
                    value={testMessage}
                    onChange={(e) => setTestMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Escribe un mensaje..."
                    className="h-12 pr-12 rounded-xl bg-slate-800 border-slate-700"
                  />
                  <button 
                    onClick={handleSendMessage}
                    disabled={loading || !testMessage}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-indigo-500 hover:text-indigo-400 disabled:opacity-30"
                  >
                    <Send size={20} />
                  </button>
                </div>
              </div>
            </div>
          )}

        </div>

        {/* Footer */}
        <div className="p-6 border-t border-slate-800 flex items-center justify-between bg-slate-900/50">
          <Button 
            variant="ghost" 
            onClick={() => setStep(step - 1)}
            disabled={step === 1 || loading}
            className="text-slate-300 hover:text-white hover:bg-slate-800 px-4"
          >
            <ChevronLeft size={16} className="mr-1" /> Atrás
          </Button>
          
          <div className="flex gap-3">
            {step === 3 && (
              <Button variant="ghost" onClick={() => setStep(4)} className="text-slate-300 hover:text-white hover:bg-slate-800">
                Saltar
              </Button>
            )}
            <Button 
              onClick={handleNext}
              disabled={loading}
              className="px-8 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold"
            >
              {loading ? (
                <><Loader2 size={16} className="mr-2 animate-spin" /> Procesando...</>
              ) : step === 5 ? (
                <>Finalizar <Rocket size={16} className="ml-2" /></>
              ) : (
                <>Continuar <ChevronRight size={16} className="ml-1" /></>
              )}
            </Button>
          </div>
        </div>
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
      `}</style>
    </div>,
    document.body
  );
}
