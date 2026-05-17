"use client";

import { useState, useRef, useEffect } from "react";
import {
  TestTube2, MessageSquare, Send, Bot, User, RefreshCw, CheckCircle, AlertCircle, Zap,
  Play, Pause, RotateCcw, Settings, Target, Clock, Plus, Trash2, Edit2, Copy, Download,
  Lightbulb, Sparkles, ChevronRight, FileText, BarChart3, ArrowRight
} from "lucide-react";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

interface Message {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: Date;
}

interface TestScenario {
  id: string;
  name: string;
  category: string;
  description: string;
  expectedOutcome: string;
}

interface TestResult {
  id: string;
  scenario: string;
  passed: boolean;
  responseTime: number;
  score: number;
  feedback: string;
  timestamp: Date;
}

const INITIAL_DATE = new Date("2024-01-01T00:00:00Z");

const getStatusColor = (status: 'passed' | 'failed') => status === 'passed' ? 'text-emerald-400 bg-emerald-500/10' : 'text-pink-400 bg-pink-500/10';

const getSimulatedResponse = (input: string): string => {
  const lowerInput = input.toLowerCase();
  if (lowerInput.includes('price') || lowerInput.includes('costo') || lowerInput.includes('cuanto')) {
    return '¡Hola! Entiendo que el price es un factor importante. Para darte la mejor cotización, ¿podrías contarme un poco más sobre el volumen que manejas?';
  }
  if (lowerInput.includes('hola') || lowerInput.includes('buenas')) {
    return '¡Hola! Qué gusto saludarte. Soy el asistente virtual de La Bodega. ¿En qué puedo apoyarte con tus compras hoy?';
  }
  return 'Gracias por tu mensaje. Estoy analizando tu consulta en base al catálogo actual. ¿Deseas que te muestre las opciones disponibles?';
};

export default function PruebasPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'chat' | 'scenarios' | 'metrics'>('chat');
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', role: 'agent', content: '¡Hola! Soy tu asistente virtual en modo de pruebas. ¿Qué escenario deseas validar?', timestamp: INITIAL_DATE }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionActive, setSessionActive] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [testScenarios] = useState<TestScenario[]>([
    { id: '1', name: 'Saludo Inicial', category: 'Comportamiento', description: 'El agente debe saludar apropiadamente', expectedOutcome: 'Mensaje de saludo y oferta de ayuda' },
    { id: '2', name: 'Consulta de Inventario', category: 'Conocimiento', description: 'Pregunta sobre stock disponible', expectedOutcome: 'Respuesta con datos reales del catálogo' },
    { id: '3', name: 'Cierre de Venta', category: 'Conversión', description: 'Usuario listo para comprar', expectedOutcome: 'El agente pide datos de contacto o confirma pedido' }
  ]);

  const [testResults] = useState<TestResult[]>([
    { id: '1', scenario: 'Saludo Inicial', passed: true, responseTime: 1.2, score: 95, feedback: 'Excelente tone profesional', timestamp: INITIAL_DATE },
    { id: '2', scenario: 'Consulta de Inventario', passed: true, responseTime: 2.1, score: 88, feedback: 'Datos precisos', timestamp: INITIAL_DATE }
  ]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const sendMessage = () => {
    if (!inputMessage.trim()) return;
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: inputMessage, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInputMessage('');
    setIsTyping(true);
    setTimeout(() => {
      setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), role: 'agent', content: getSimulatedResponse(userMsg.content), timestamp: new Date() }]);
      setIsTyping(false);
    }, 1200);
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-20">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
        <div>
          <h1 className="text-3xl font-black text-white tracking-tight">Centro de Pruebas</h1>
          <p className="text-slate-400 mt-1">Valida el comportamiento y conocimiento de tu IA antes de publicarla.</p>
        </div>
        <Button className="rounded-2xl h-14 px-8 font-black bg-indigo-600 hover:bg-indigo-700 text-white shadow-xl shadow-indigo-500/20">
          <Play className="w-5 h-5 mr-2" /> Iniciar Test Masivo
        </Button>
      </div>

      {/* Tabs Navigation */}
      <div className="flex items-center gap-2 bg-slate-900/50 p-1.5 rounded-2xl border border-white/5 w-fit">
        {[
          { id: 'chat', label: 'Simulador', icon: MessageSquare },
          { id: 'scenarios', label: 'Escenarios', icon: Target },
          { id: 'metrics', label: 'Métricas de QA', icon: BarChart3 }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm transition-all duration-300 ${
              activeTab === tab.id 
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20' 
                : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Panel */}
        <div className="lg:col-span-2 space-y-8">
          {activeTab === 'chat' && (
            <div className="bg-slate-900/40 backdrop-blur-xl border border-white/5 rounded-[32px] overflow-hidden shadow-2xl flex flex-col h-[650px]">
              <div className="p-6 border-b border-white/5 flex items-center justify-between bg-white/5">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-indigo-600 flex items-center justify-center shadow-lg">
                    <Bot className="w-7 h-7 text-white" />
                  </div>
                  <div>
                    <p className="font-black text-white">FluxBot Testing</p>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">En línea (Simulación)</span>
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                   <Button variant="outline" size="icon" className="rounded-xl border-white/5 bg-white/5 text-white" onClick={() => setMessages([])}><RotateCcw size={18}/></Button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-8 space-y-6 bg-black/20">
                {messages.map((m) => (
                  <div key={m.id} className={`flex items-start gap-4 ${m.role === 'user' ? 'justify-end' : ''}`}>
                    {m.role === 'agent' && (
                      <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center flex-shrink-0 shadow-lg mt-1">
                        <Bot className="w-5 h-5 text-white" />
                      </div>
                    )}
                    <div className={`max-w-[80%] ${m.role === 'user' ? 'text-right' : ''}`}>
                      <div className={`rounded-2xl p-4 shadow-xl ${m.role === 'agent' ? 'bg-slate-800 border border-white/5 text-slate-200' : 'bg-indigo-600 text-white'}`}>
                        <p className="text-sm leading-relaxed">{m.content}</p>
                      </div>
                      <p className="text-[10px] text-slate-500 mt-2 font-bold uppercase tracking-widest px-2">{m.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
                    </div>
                  </div>
                ))}
                {isTyping && (
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center flex-shrink-0 shadow-lg mt-1">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    <div className="bg-slate-800 rounded-2xl p-4 border border-white/5 shadow-xl">
                      <div className="flex gap-1.5">
                        <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" />
                        <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce delay-100" />
                        <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce delay-200" />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              <div className="p-6 border-t border-white/5 bg-white/5">
                <div className="flex items-center gap-4 bg-black/40 p-2 rounded-[24px] border border-white/10">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Pon a prueba a tu IA..."
                    className="flex-1 px-6 py-3 bg-transparent text-white outline-none placeholder:text-slate-600 font-medium"
                  />
                  <Button onClick={sendMessage} className="h-12 w-12 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg">
                    <Send className="w-5 h-5" />
                  </Button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'scenarios' && (
            <div className="bg-slate-900/40 backdrop-blur-xl border border-white/5 rounded-[32px] overflow-hidden shadow-2xl">
              <div className="p-8 border-b border-white/5 flex items-center justify-between bg-white/5">
                <h2 className="text-xl font-black text-white flex items-center gap-3">
                  <Target className="text-indigo-500" /> Escenarios de Validación
                </h2>
                <Button variant="outline" className="rounded-xl border-white/10 text-white hover:bg-white/5">
                  <Plus className="w-4 h-4 mr-2" /> Nuevo
                </Button>
              </div>
              <div className="divide-y divide-white/5">
                {testScenarios.map((s) => (
                  <div key={s.id} className="p-8 hover:bg-white/5 transition-all group">
                    <div className="flex justify-between items-start gap-4">
                      <div>
                        <span className="text-[10px] font-black bg-indigo-500/20 text-indigo-400 px-3 py-1 rounded-full uppercase tracking-widest mb-3 inline-block">{s.category}</span>
                        <h3 className="text-lg font-black text-white">{s.name}</h3>
                        <p className="text-sm text-slate-400 mt-2 leading-relaxed">{s.description}</p>
                        <div className="mt-4 p-4 bg-black/40 rounded-2xl border border-white/5">
                          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-2">
                             <CheckCircle size={14} className="text-emerald-500" /> Resultado Esperado
                          </p>
                          <p className="text-sm text-slate-200 font-medium">{s.expectedOutcome}</p>
                        </div>
                      </div>
                      <Button variant="ghost" size="icon" className="text-indigo-400 opacity-0 group-hover:opacity-100 transition-all"><Play size={20} /></Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'metrics' && (
            <div className="bg-slate-900/40 backdrop-blur-xl border border-white/5 rounded-[32px] overflow-hidden shadow-2xl">
              <div className="p-8 border-b border-white/5 bg-white/5">
                <h2 className="text-xl font-black text-white flex items-center gap-3">
                  <BarChart3 className="text-indigo-500" /> Registro de Resultados
                </h2>
              </div>
              <div className="divide-y divide-white/5">
                {testResults.map((r) => (
                  <div key={r.id} className="p-8 hover:bg-white/5 transition-all">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-black text-white">{r.scenario}</h3>
                      <div className={`flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-black uppercase tracking-widest ${getStatusColor(r.passed ? 'passed' : 'failed')}`}>
                         {r.passed ? 'Aprobado' : 'Fallido'}
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4 mb-4">
                      <div className="bg-black/20 p-3 rounded-xl border border-white/5">
                         <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-1">Respuesta</p>
                         <p className="text-white font-black">{r.responseTime}s</p>
                      </div>
                      <div className="bg-black/20 p-3 rounded-xl border border-white/5">
                         <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-1">Puntaje</p>
                         <p className="text-white font-black">{r.score}%</p>
                      </div>
                      <div className="bg-black/20 p-3 rounded-xl border border-white/5">
                         <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-1">Fecha</p>
                         <p className="text-white font-black text-[10px]">12/04/24</p>
                      </div>
                    </div>
                    <p className="text-sm text-slate-400 bg-black/40 p-4 rounded-2xl border border-white/5 leading-relaxed">
                      <b className="text-indigo-400 uppercase text-[10px] tracking-widest block mb-1">Observación QA:</b> {r.feedback}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Side Panel */}
        <div className="space-y-8">
           <div className="bg-gradient-to-br from-indigo-600 to-blue-700 rounded-[32px] p-8 text-white shadow-2xl shadow-indigo-500/20">
              <h3 className="text-xl font-black flex items-center gap-2 mb-6">
                <BarChart3 size={20} /> Score de Calidad
              </h3>
              <div className="space-y-6">
                 <div className="flex justify-between items-end">
                    <span className="text-xs font-bold text-white/70 uppercase tracking-widest">Tasa de Éxito</span>
                    <span className="text-3xl font-black">92%</span>
                 </div>
                 <div className="h-3 bg-white/20 rounded-full overflow-hidden">
                    <div className="h-full w-[92%] bg-white rounded-full shadow-lg" />
                 </div>
                 <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/10">
                    <div>
                       <p className="text-[9px] font-bold text-white/60 uppercase tracking-widest">Escenarios</p>
                       <p className="text-lg font-black">12</p>
                    </div>
                    <div>
                       <p className="text-[9px] font-bold text-white/60 uppercase tracking-widest">Fallas</p>
                       <p className="text-lg font-black text-pink-300">1</p>
                    </div>
                 </div>
              </div>
           </div>

           <div className="bg-slate-900/40 backdrop-blur-xl border border-white/5 rounded-[32px] p-8 space-y-6">
              <h3 className="text-lg font-black text-white flex items-center gap-2">
                <Lightbulb size={20} className="text-amber-400" /> Consejos de QA
              </h3>
              <ul className="space-y-4">
                 {[
                   "Prueba casos con errores ortográficos.",
                   "Verifica respuestas a preguntas sensibles.",
                   "Fuerza el escalamiento a humano.",
                   "Valida datos extraídos de tus PDFs."
                 ].map((tip, i) => (
                   <li key={i} className="flex gap-3 text-sm text-slate-400 leading-relaxed font-medium">
                      <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-2 flex-shrink-0" />
                      {tip}
                   </li>
                 ))}
              </ul>
           </div>

           <Button 
            className="w-full rounded-[28px] h-20 flex items-center justify-between px-8 border border-emerald-500/20 bg-emerald-500/5 hover:bg-emerald-500/10 text-emerald-400 transition-all group shadow-2xl shadow-emerald-500/10"
            onClick={() => {
              toast.success("🚀 ¡Felicidades! Tu FluxBot está ahora totalmente operativo.");
              router.push("/dashboard");
            }}
          >
            <div className="text-left">
              <p className="text-[10px] font-black uppercase tracking-widest text-emerald-500/70 mb-1">Todo validado</p>
              <p className="text-lg font-black">Activar FluxBot</p>
            </div>
            <ArrowRight className="w-6 h-6 group-hover:translate-x-2 transition-transform" />
          </Button>
        </div>
      </div>
    </div>
  );
}
