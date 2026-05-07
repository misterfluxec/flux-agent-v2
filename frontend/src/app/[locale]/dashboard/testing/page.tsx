"use client";

import { useState, useRef, useEffect } from "react";
import {
  TestTube2, MessageSquare, Send, Bot, User, RefreshCw, CheckCircle, AlertCircle, Zap,
  Play, Pause, RotateCcw, Settings, Target, Clock, Plus, Trash2, Edit2, Copy, Download,
  Lightbulb, Sparkles, ChevronRight, FileText, BarChart3
} from "lucide-react";
import { toast } from "sonner";
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

const getStatusColor = (status: 'passed' | 'failed') => status === 'passed' ? 'text-green-600 bg-green-500/10' : 'text-red-600 bg-red-500/10';

const getSimulatedResponse = (input: string): string => {
  const lowerInput = input.toLowerCase();
  if (lowerInput.includes('precio') || lowerInput.includes('costo') || lowerInput.includes('cuanto')) {
    return '¡Hola! Antes de darte información sobre precios, me gustaría saber más sobre tus necesidades. ¿Podrías contarme qué tipo de producto buscas?';
  }
  if (lowerInput.includes('hola') || lowerInput.includes('buenas')) {
    return '¡Hola! Qué gusto saludarte. Soy tu asesor virtual. Estoy aquí para ayudarte a encontrar exactamente lo que necesitas. ¿En qué te ayudo hoy?';
  }
  if (lowerInput.includes('gracias')) {
    return '¡De nada! Es un placer poder ayudarte. ¿Hay algo más en lo que pueda asistirte?';
  }
  return 'Gracias por tu mensaje. Como tu asesor virtual, mi objetivo es darte la mejor información. ¿Podrías darme más detalles para poder ayudarte mejor?';
};

export default function PruebasPage() {
  const [activeTab, setActiveTab] = useState<'chat' | 'scenarios' | 'metrics' | 'training'>('chat');
  
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', role: 'agent', content: '¡Hola! Soy tu asistente virtual. ¿En qué puedo ayudarte hoy?', timestamp: INITIAL_DATE }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionActive, setSessionActive] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [testScenarios] = useState<TestScenario[]>([
    { id: '1', name: 'Saludo Inicial', category: 'Comportamiento', description: 'El agente debe saludar apropiadamente', expectedOutcome: 'Mensaje de saludo con nombre del agente y oferta de ayuda' },
    { id: '2', name: 'Consulta de Precio', category: 'Ventas', description: 'Cuando el usuario pregunta por el precio', expectedOutcome: 'El agente pregunta por necesidades antes de dar precio' },
    { id: '3', name: 'Manejo de Objeciones', category: 'Ventas', description: 'El usuario expresa preocupación sobre el precio', expectedOutcome: 'El agente ofrece valor adicional o alternativas' },
    { id: '4', name: 'Cierre de Venta', category: 'Conversión', description: 'El usuario muestra interés en comprar', expectedOutcome: 'El agente cierra con pregunta de seguimiento' },
    { id: '5', name: 'Escalamiento a Humano', category: 'Comportamiento', description: 'El usuario pide hablar con una persona', expectedOutcome: 'El agente escala apropiadamente' },
    { id: '6', name: 'Preguntas Frecuentes', category: 'Conocimiento', description: 'El usuario pregunta sobre políticas de envío', expectedOutcome: 'Respuesta precisa basada en datos cargados' }
  ]);

  const [testResults] = useState<TestResult[]>([
    { id: '1', scenario: 'Saludo Inicial', passed: true, responseTime: 1.2, score: 95, feedback: 'Excelente saludo', timestamp: INITIAL_DATE },
    { id: '2', scenario: 'Consulta de Precio', passed: true, responseTime: 2.1, score: 88, feedback: 'Buen manejo, preguntó por necesidades', timestamp: INITIAL_DATE },
    { id: '3', scenario: 'Manejo de Objeciones', passed: false, responseTime: 3.5, score: 62, feedback: 'Necesita mejorar la empatía', timestamp: INITIAL_DATE }
  ]);

  const [trainingProgress] = useState({ identity: 100, script: 85, behavior: 70, data: 60, connectors: 100 });

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
      const agentResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'agent',
        content: getSimulatedResponse(userMsg.content),
        timestamp: new Date()
      };
      setMessages(prev => [...prev, agentResponse]);
      setIsTyping(false);
    }, 1500 + Math.random() * 1000);
  };

  const resetChat = () => {
    setMessages([{ id: '1', role: 'agent', content: '¡Hola! Soy tu asistente virtual. ¿En qué puedo ayudarte hoy?', timestamp: new Date() }]);
    setSessionActive(true);
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-7xl mx-auto pb-20">
      {/* Page Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">
            <span className="text-indigo-500">Centro</span> de Pruebas
          </h1>
          <p className="text-muted-foreground mt-1 text-sm">Prueba y valida la configuración de tu Centro de Datos en un entorno seguro</p>
        </div>
        <Button className="rounded-xl h-11 bg-indigo-600 hover:bg-indigo-700 text-white shadow-[0_0_20px_rgba(99,102,241,0.3)] transition-all">
          <TestTube2 className="w-5 h-5 mr-2" /> Ejecutar Test Completo
        </Button>
      </div>

      {/* Tab Navigation */}
      <div className="flex items-center gap-2 bg-card rounded-xl p-2 border border-border overflow-x-auto shadow-sm">
        {[
          { id: 'chat', label: 'Simulador', icon: MessageSquare },
          { id: 'scenarios', label: 'Escenarios', icon: Target },
          { id: 'metrics', label: 'Métricas', icon: BarChart3 },
          { id: 'training', label: 'Centro de Datos', icon: Sparkles }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as 'chat' | 'scenarios' | 'metrics' | 'training')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium text-sm whitespace-nowrap transition-all ${activeTab === tab.id ? 'bg-indigo-600 text-white shadow-md' : 'hover:bg-muted text-muted-foreground'}`}
          >
            <tab.icon className="w-4 h-4" /> {tab.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Chat Simulator */}
          {activeTab === 'chat' && (
            <div className="bg-card rounded-2xl border border-border overflow-hidden shadow-sm flex flex-col h-[600px]">
              <div className="p-4 border-b border-border flex items-center justify-between bg-muted/20">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center shadow-sm">
                    <Bot className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="font-semibold text-sm">Asistente AI - Modo Pruebas</p>
                    <div className="flex items-center gap-1.5">
                      <div className={`w-2 h-2 rounded-full ${sessionActive ? 'bg-green-500 animate-pulse' : 'bg-muted-foreground'}`} />
                      <span className="text-xs text-muted-foreground">{sessionActive ? 'Sesión activa' : 'Sesión pausada'}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="icon" onClick={() => setSessionActive(!sessionActive)} className={sessionActive ? 'text-amber-500 hover:bg-amber-500/10' : 'text-green-500 hover:bg-green-500/10'} title={sessionActive ? 'Pausar' : 'Reanudar'}>
                    {sessionActive ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </Button>
                  <Button variant="ghost" size="icon" onClick={resetChat} title="Reiniciar chat"><RotateCcw className="w-4 h-4" /></Button>
                  <Button variant="ghost" size="icon" title="Ajustes"><Settings className="w-4 h-4" /></Button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin bg-card/50">
                {messages.map((message) => (
                  <div key={message.id} className={`flex items-start gap-3 ${message.role === 'user' ? 'justify-end' : ''}`}>
                    {message.role === 'agent' && (
                      <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-indigo-600 flex items-center justify-center flex-shrink-0 shadow-sm mt-1">
                        <Bot className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                      </div>
                    )}
                    <div className={`max-w-[80%] sm:max-w-[70%] ${message.role === 'user' ? 'text-right' : ''}`}>
                      <div className={`rounded-2xl p-3 sm:p-4 shadow-sm ${message.role === 'agent' ? 'bg-muted rounded-tl-sm border border-border' : 'bg-indigo-600 text-white rounded-tr-sm'}`}>
                        <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
                      </div>
                      <p className="text-[10px] sm:text-xs text-muted-foreground mt-1.5 px-1">{message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
                    </div>
                    {message.role === 'user' && (
                      <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-indigo-100 flex items-center justify-center flex-shrink-0 shadow-sm mt-1">
                        <User className="w-4 h-4 sm:w-5 sm:h-5 text-indigo-600" />
                      </div>
                    )}
                  </div>
                ))}
                {isTyping && (
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-indigo-600 flex items-center justify-center flex-shrink-0 shadow-sm mt-1">
                      <Bot className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                    </div>
                    <div className="bg-muted rounded-2xl rounded-tl-sm p-4 border border-border shadow-sm">
                      <div className="flex items-center gap-1.5">
                        <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              <div className="p-4 border-t border-border bg-card">
                <div className="flex items-center gap-3">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Escribe un mensaje de prueba..."
                    disabled={!sessionActive || isTyping}
                    className="flex-1 px-4 py-3 bg-muted/50 rounded-xl border border-border outline-none focus:border-indigo-500 disabled:opacity-50 transition-colors"
                  />
                  <Button onClick={sendMessage} disabled={!sessionActive || !inputMessage.trim() || isTyping} className="h-12 w-12 sm:w-auto sm:px-6 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm disabled:opacity-50 flex-shrink-0">
                    <Send className="w-5 h-5 sm:mr-2" />
                    <span className="hidden sm:inline">Enviar</span>
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Test Scenarios */}
          {activeTab === 'scenarios' && (
            <div className="bg-card rounded-2xl border border-border overflow-hidden shadow-sm">
              <div className="p-5 border-b border-border flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <h2 className="font-semibold flex items-center gap-2 text-lg">
                  <Target className="w-5 h-5 text-indigo-500" /> Escenarios de Prueba
                </h2>
                <Button className="rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white">
                  <Plus className="w-4 h-4 mr-2" /> Nuevo Escenario
                </Button>
              </div>
              <div className="divide-y divide-border">
                {testScenarios.map((scenario) => (
                  <div key={scenario.id} className="p-5 hover:bg-secondary/30 transition-colors group">
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                      <div className="flex-1">
                        <span className="inline-block px-2.5 py-1 bg-indigo-500/10 text-indigo-600 rounded-full text-xs font-medium mb-2">{scenario.category}</span>
                        <h3 className="font-semibold text-base">{scenario.name}</h3>
                        <p className="text-sm text-muted-foreground mt-1">{scenario.description}</p>
                        <div className="mt-3 p-3 bg-muted/50 rounded-xl border border-border/50">
                          <p className="text-xs font-medium text-muted-foreground mb-1 flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5" /> Resultado Esperado:</p>
                          <p className="text-sm text-foreground/90">{scenario.expectedOutcome}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-1 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
                        <Button variant="ghost" size="icon" className="text-indigo-500 hover:bg-indigo-500/10"><Play className="w-4 h-4" /></Button>
                        <Button variant="ghost" size="icon"><Edit2 className="w-4 h-4" /></Button>
                        <Button variant="ghost" size="icon"><Copy className="w-4 h-4" /></Button>
                        <Button variant="ghost" size="icon" className="text-red-500 hover:bg-red-500/10"><Trash2 className="w-4 h-4" /></Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Metrics */}
          {activeTab === 'metrics' && (
            <div className="bg-card rounded-2xl border border-border overflow-hidden shadow-sm">
              <div className="p-5 border-b border-border">
                <h2 className="font-semibold flex items-center gap-2 text-lg">
                  <BarChart3 className="w-5 h-5 text-indigo-500" /> Resultados de Testing
                </h2>
              </div>
              <div className="divide-y divide-border">
                {testResults.map((result) => (
                  <div key={result.id} className="p-5 hover:bg-secondary/30 transition-colors">
                    <div className="flex flex-col gap-3">
                      <div className="flex items-center gap-3">
                        <h3 className="font-semibold text-base">{result.scenario}</h3>
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium flex items-center gap-1.5 ${getStatusColor(result.passed ? 'passed' : 'failed')}`}>
                          {result.passed ? <CheckCircle className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
                          {result.passed ? 'Aprobado' : 'Fallido'}
                        </span>
                      </div>
                      <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1.5 bg-muted px-2.5 py-1 rounded-md"><Clock className="w-4 h-4 text-indigo-500" /> {result.responseTime}s</span>
                        <span className="flex items-center gap-1.5 bg-muted px-2.5 py-1 rounded-md"><Target className="w-4 h-4 text-amber-500" /> Score: {result.score}%</span>
                        <span className="text-xs">{result.timestamp.toLocaleString()}</span>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1 p-3 bg-muted/50 rounded-xl border border-border/50"><strong>Feedback:</strong> {result.feedback}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Training */}
          {activeTab === 'training' && (
            <div className="bg-card rounded-2xl border border-border overflow-hidden shadow-sm">
              <div className="p-5 border-b border-border">
                <h2 className="font-semibold flex items-center gap-2 text-lg">
                  <Sparkles className="w-5 h-5 text-amber-500" /> Flujo de Centro de Datos Completo
                </h2>
                <p className="text-sm text-muted-foreground mt-1">Sigue los pasos para validar el conocimiento de tu agente</p>
              </div>
              <div className="p-6 space-y-8">
                {[
                  { step: 1, name: 'Identidad', progress: trainingProgress.identity, desc: 'Nombre, tono, personalidad' },
                  { step: 2, name: 'Scripts', progress: trainingProgress.script, desc: 'Fases, reglas de oro' },
                  { step: 3, name: 'Comportamiento', progress: trainingProgress.behavior, desc: 'Saludos, keywords' },
                  { step: 4, name: 'Conocimiento', progress: trainingProgress.data, desc: 'Archivos, web, bases de datos' },
                  { step: 5, name: 'Conectores', progress: trainingProgress.connectors, desc: 'WhatsApp, Web chat' },
                ].map((item) => (
                  <div key={item.step} className="flex items-start gap-5 group">
                    <div className="relative">
                      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-bold text-lg shadow-sm transition-colors ${item.progress === 100 ? 'bg-green-500 text-white' : 'bg-muted border border-border text-muted-foreground group-hover:border-indigo-500'}`}>
                        {item.progress === 100 ? <CheckCircle className="w-6 h-6" /> : item.step}
                      </div>
                      {item.step < 5 && <div className="absolute top-[52px] left-1/2 w-0.5 h-7 -translate-x-1/2 bg-border group-hover:bg-indigo-500/30 transition-colors" />}
                    </div>
                    <div className="flex-1 pt-1">
                      <div className="flex items-center justify-between mb-1">
                        <h3 className="font-semibold text-base">{item.name}</h3>
                        <span className={`text-sm font-medium ${item.progress === 100 ? 'text-green-600' : 'text-indigo-600'}`}>{item.progress}%</span>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">{item.desc}</p>
                      <div className="h-2.5 bg-muted rounded-full overflow-hidden border border-border/50">
                        <div className={`h-full rounded-full transition-all duration-1000 ${item.progress === 100 ? 'bg-green-500' : 'bg-indigo-600'}`} style={{ width: `${item.progress}%` }} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Quick Stats */}
          <div className="rounded-2xl p-6 text-white shadow-sm" style={{ background: "linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)", boxShadow: "0 10px 30px rgba(99,102,241,0.2)" }}>
            <h3 className="font-semibold mb-5 flex items-center gap-2">
              <BarChart3 className="w-5 h-5" /> Resumen de Pruebas
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center pb-3 border-b border-white/20">
                <span className="text-white/90 text-sm">Escenarios</span>
                <span className="font-bold text-xl">{testScenarios.length}</span>
              </div>
              <div className="flex justify-between items-center pb-3 border-b border-white/20">
                <span className="text-white/90 text-sm">Aprobados</span>
                <span className="font-bold text-xl text-green-300">{testResults.filter(r => r.passed).length}</span>
              </div>
              <div className="flex justify-between items-center pb-3 border-b border-white/20">
                <span className="text-white/90 text-sm">Fallidos</span>
                <span className="font-bold text-xl text-pink-300">{testResults.filter(r => !r.passed).length}</span>
              </div>
              <div className="flex justify-between items-center pt-1">
                <span className="text-white/90 text-sm font-medium">Tasa de éxito</span>
                <span className="font-bold text-2xl">{testResults.length > 0 ? Math.round((testResults.filter(r => r.passed).length / testResults.length) * 100) : 0}%</span>
              </div>
            </div>
          </div>

          {/* Testing Tips */}
          <div className="bg-amber-500/10 rounded-2xl p-5 border border-amber-500/20 shadow-sm">
            <h3 className="font-semibold text-amber-600 flex items-center gap-2 mb-4">
              <Lightbulb className="w-5 h-5" /> Consejos de Pruebas
            </h3>
            <ul className="space-y-3">
              {[
                "Prueba casos de rechazo o quejas",
                "Fuerza preguntas fuera de contexto",
                "Verifica los tiempos de respuesta",
                "Prueba modismos y errores ortográficos"
              ].map((tip, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                  <ChevronRight className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" /> <span>{tip}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Quick Actions */}
          <div className="bg-card rounded-2xl border border-border p-5 shadow-sm">
            <h3 className="font-semibold flex items-center gap-2 mb-4">
              <Zap className="w-5 h-5 text-indigo-500" /> Acciones
            </h3>
            <div className="space-y-2">
              <Button variant="outline" className="w-full justify-start rounded-xl h-12 border-border hover:bg-muted"><Play className="w-4 h-4 mr-3 text-green-500" /> Test Automático</Button>
              <Button variant="outline" className="w-full justify-start rounded-xl h-12 border-border hover:bg-muted"><Download className="w-4 h-4 mr-3 text-blue-500" /> Exportar Logs</Button>
              <Button variant="outline" className="w-full justify-start rounded-xl h-12 border-border hover:bg-muted"><FileText className="w-4 h-4 mr-3 text-amber-500" /> Reporte QA (PDF)</Button>
              <Button variant="outline" className="w-full justify-start rounded-xl h-12 border-border hover:bg-muted"><RefreshCw className="w-4 h-4 mr-3 text-purple-500" /> Resetear Métricas</Button>
            </div>
          </div>

          {/* Final Activation Step */}
          <Button 
            className="w-full rounded-2xl h-14 flex items-center justify-between px-6 border-2 border-green-500/20 bg-green-500/5 hover:bg-green-500/10 text-green-600 dark:text-green-400 transition-all group shadow-lg shadow-green-500/10"
            onClick={() => {
              localStorage.setItem('flux_phase_5', 'true');
              window.dispatchEvent(new Event('storage'));
              toast.success("🚀 ¡Felicidades! Tu FluxBot está ahora totalmente operativo.");
              window.location.href = "/dashboard";
            }}
          >
            <span className="font-semibold flex items-center gap-2">
              <Zap className="w-5 h-5" /> Activar FluxBot Completo
            </span>
            <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Button>
        </div>
      </div>
    </div>
  );
}
