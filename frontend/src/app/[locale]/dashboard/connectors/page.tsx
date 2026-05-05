"use client";

import { useState } from "react";
import {
  Plug, CheckCircle, AlertCircle, RefreshCw, Plus, Trash2, Settings, MessageSquare, Send,
  Users, Zap, Globe, MessageCircle, Camera, SendHorizontal, Clock
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import WhatsAppCloudWizard from "./components/WhatsAppCloudWizard";
import QuotaLowBanner from "./components/QuotaLowBanner";
import QuotaManager from "./components/QuotaManager";

interface Connector {
  id: string;
  name: string;
  platform: 'telegram' | 'whatsapp' | 'instagram' | 'messenger' | 'webchat';
  status: 'connected' | 'disconnected' | 'error' | 'syncing';
  lastActivity: string;
  messages: number;
  conversations: number;
  enabled: boolean;
  config: {
    apiKey?: string;
    botToken?: string;
    phoneNumber?: string;
    webhook?: string;
  };
}

const platforms = [
  { value: 'telegram', label: 'Telegram', icon: SendHorizontal, color: 'bg-blue-500', description: 'Conecta tu bot de Telegram' },
  { value: 'whatsapp_evolution', label: 'WhatsApp (Evo)', icon: MessageCircle, color: 'bg-green-500', description: 'Integración rápida con Evolution API' },
  { value: 'whatsapp_cloud', label: 'WhatsApp Cloud API', icon: MessageCircle, color: 'bg-emerald-600', description: 'Integración oficial de Meta (Recomendado)' },
  { value: 'instagram', label: 'Instagram', icon: Camera, color: 'bg-gradient-to-br from-purple-500 via-pink-500 to-yellow-500', description: 'Mensajes directos de Instagram' },
  { value: 'messenger', label: 'Messenger', icon: MessageSquare, color: 'bg-blue-600', description: 'Facebook Messenger' },
  { value: 'webchat', label: 'Web Chat', icon: Globe, color: 'bg-indigo-500', description: 'Widget de chat para tu web' }
];

export default function ConectoresPage() {
  const [connectors, setConnectors] = useState<Connector[]>([
    { id: '1', name: 'Bot Principal Telegram', platform: 'telegram', status: 'connected', lastActivity: 'Hace 2 min', messages: 12450, conversations: 892, enabled: true, config: { botToken: '123456:ABC-DefGHIjklMNOpqrSTUvwxYZ' } },
    { id: '2', name: 'WhatsApp Business', platform: 'whatsapp', status: 'connected', lastActivity: 'Hace 5 min', messages: 8934, conversations: 567, enabled: true, config: { phoneNumber: '+52 55 1234 5678' } },
    { id: '3', name: 'IG DM - @mitienda', platform: 'instagram', status: 'connected', lastActivity: 'Hace 15 min', messages: 3456, conversations: 234, enabled: true, config: { apiKey: 'IGQVJV...' } },
    { id: '4', name: 'Messenger FB', platform: 'messenger', status: 'disconnected', lastActivity: 'Hace 1 día', messages: 1234, conversations: 89, enabled: false, config: {} },
    { id: '5', name: 'Chat Web Mi Sitio', platform: 'webchat', status: 'connected', lastActivity: 'Hace 1 min', messages: 5678, conversations: 456, enabled: true, config: { webhook: 'https://misitio.com/webhook' } }
  ]);

  const [showNewConnector, setShowNewConnector] = useState(false);
  const [showCloudWizard, setShowCloudWizard] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<string>('');
  const [newConnector, setNewConnector] = useState({ name: '', botToken: '', phoneNumber: '', apiKey: '', webhook: '' });
  const [acceptedToS, setAcceptedToS] = useState(false);

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      connected: 'bg-green-500/10 text-green-600',
      disconnected: 'bg-muted text-muted-foreground',
      error: 'bg-red-500/10 text-red-600',
      syncing: 'bg-orange-500/10 text-orange-600'
    };
    return styles[status] || '';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected': return <CheckCircle className="w-3 h-3" />;
      case 'disconnected': return <AlertCircle className="w-3 h-3" />;
      case 'error': return <AlertCircle className="w-3 h-3" />;
      case 'syncing': return <RefreshCw className="w-3 h-3 animate-spin" />;
      default: return null;
    }
  };

  const toggleConnector = (id: string) => {
    setConnectors(connectors => connectors.map(c => c.id === id ? { ...c, enabled: !c.enabled } : c));
  };

  const deleteConnector = (id: string) => {
    if (confirm("¿Estás seguro de eliminar este conector?")) {
      setConnectors(connectors => connectors.filter(c => c.id !== id));
      toast.success("Conector eliminado");
    }
  };

  const handleAddConnector = () => {
    if (selectedPlatform === 'whatsapp_cloud') {
      setShowCloudWizard(true);
      setShowNewConnector(false);
      return;
    }

    if (!newConnector.name) { toast.error("El nombre es requerido"); return; }
    const newC: Connector = {
      id: Date.now().toString(),
      name: newConnector.name,
      platform: selectedPlatform as any,
      status: 'connected',
      lastActivity: 'Ahora',
      messages: 0,
      conversations: 0,
      enabled: true,
      config: { ...newConnector }
    };
    setConnectors([newC, ...connectors]);
    localStorage.setItem("flux_phase_4", "true");
    toast.success("Conector agregado correctamente");
    window.dispatchEvent(new Event('storage'));
    setShowNewConnector(false);
    setSelectedPlatform('');
    setNewConnector({ name: '', botToken: '', phoneNumber: '', apiKey: '', webhook: '' });
  };

  const totalStats = {
    activeConnectors: connectors.filter(c => c.enabled && c.status === 'connected').length,
    totalMessages: connectors.reduce((acc, c) => acc + c.messages, 0),
    totalConversations: connectors.reduce((acc, c) => acc + c.conversations, 0),
    activePlatforms: new Set(connectors.filter(c => c.status === 'connected').map(c => c.platform)).size
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-7xl mx-auto pb-20">

      {/* Banner de cuota baja — se auto-oculta si no aplica */}
      <QuotaLowBanner />

      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 animate-entry">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Plug className="w-4 h-4 text-indigo-500" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-indigo-500/80">Omnicanalidad</span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-purple-600">Conectores</span> Multicanal
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Integra tu agente de ventas con diferentes plataformas de mensajería.
          </p>
        </div>
        <Button onClick={() => setShowNewConnector(true)} className="rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white h-11 px-6 shadow-[0_0_20px_rgba(99,102,241,0.3)] transition-all">
          <Plus className="w-5 h-5 mr-2" /> Agregar Conector
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-card rounded-xl p-4 border border-border shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-green-500/10 flex items-center justify-center">
              <Zap className="w-5 h-5 text-green-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{totalStats.activeConnectors}</p>
              <p className="text-xs text-muted-foreground">Conectores activos</p>
            </div>
          </div>
        </div>
        <div className="bg-card rounded-xl p-4 border border-border shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-indigo-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{totalStats.totalMessages.toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">Mensajes totales</p>
            </div>
          </div>
        </div>
        <div className="bg-card rounded-xl p-4 border border-border shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-orange-500/10 flex items-center justify-center">
              <Users className="w-5 h-5 text-orange-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{totalStats.totalConversations}</p>
              <p className="text-xs text-muted-foreground">Conversaciones</p>
            </div>
          </div>
        </div>
        <div className="bg-card rounded-xl p-4 border border-border shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
              <Plug className="w-5 h-5 text-purple-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{totalStats.activePlatforms}</p>
              <p className="text-xs text-muted-foreground">Plataformas activas</p>
            </div>
          </div>
        </div>
      </div>

      {/* Panel de Gestión de Cuotas Híbridas */}
      <QuotaManager />

      {/* Connectors List */}
      <div className="bg-card rounded-2xl border border-border overflow-hidden shadow-sm">
        <div className="p-5 border-b border-border">
          <h2 className="font-semibold flex items-center gap-2">
            <Plug className="w-5 h-5 text-indigo-500" /> Conectores Configurados
          </h2>
        </div>

        <div className="divide-y divide-border">
          {connectors.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">No tienes conectores agregados.</div>
          ) : connectors.map((connector) => {
            const platform = platforms.find(p => p.value === connector.platform);
            const Icon = platform?.icon || Plug;
            return (
              <div key={connector.id} className={`p-5 hover:bg-secondary/50 transition-colors ${!connector.enabled && 'opacity-60 grayscale'}`}>
                <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                  <div className={`w-14 h-14 rounded-xl ${platform?.color || 'bg-muted'} flex items-center justify-center flex-shrink-0 hidden sm:flex`}>
                    <Icon className="w-7 h-7 text-white" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 flex-wrap">
                      <h3 className="font-semibold text-base sm:text-lg truncate">{connector.name}</h3>
                      <span className={`px-2 py-1 rounded-full text-[10px] sm:text-xs font-medium ${getStatusBadge(connector.status)} flex items-center gap-1`}>
                        {getStatusIcon(connector.status)}
                        {connector.status === 'connected' && 'Conectado'}
                        {connector.status === 'disconnected' && 'Desconectado'}
                        {connector.status === 'error' && 'Error'}
                        {connector.status === 'syncing' && 'Sincronizando'}
                      </span>
                      <span className="px-2 py-1 bg-secondary text-muted-foreground rounded-full text-[10px] sm:text-xs">
                        {platform?.label}
                      </span>
                    </div>

                    <div className="flex items-center gap-4 mt-3 text-xs sm:text-sm text-muted-foreground flex-wrap">
                      <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {connector.lastActivity}</span>
                      <span className="flex items-center gap-1"><MessageSquare className="w-3 h-3" /> {connector.messages.toLocaleString()} msg</span>
                      <span className="flex items-center gap-1"><Users className="w-3 h-3" /> {connector.conversations} conv.</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 justify-end sm:justify-start">
                    <Button variant="ghost" size="icon" className="hover:bg-muted" title="Configurar"><Settings className="w-4 h-4" /></Button>
                    <Button variant="ghost" size="icon" className="text-indigo-500 hover:bg-indigo-500/10" title="Probar"><Send className="w-4 h-4" /></Button>
                    <button onClick={() => toggleConnector(connector.id)} className={`w-10 h-6 rounded-full transition-colors relative flex-shrink-0 ${connector.enabled ? 'bg-green-500' : 'bg-muted'}`} title={connector.enabled ? 'Desactivar' : 'Activar'}>
                      <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${connector.enabled ? 'left-5' : 'left-1'}`} />
                    </button>
                    <Button variant="ghost" size="icon" onClick={() => deleteConnector(connector.id)} className="text-red-500 hover:bg-red-500/10" title="Eliminar"><Trash2 className="w-4 h-4" /></Button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Supported Platforms */}
      <div className="rounded-2xl p-6 text-white" style={{ background: "linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)", boxShadow: "0 10px 30px rgba(99,102,241,0.3)" }}>
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Plug className="w-5 h-5" /> Plataformas Soportadas
        </h3>
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          {platforms.map((platform) => {
            const Icon = platform.icon;
            return (
              <div key={platform.value} className="flex flex-col items-center text-center p-4 bg-white/10 rounded-xl hover:bg-white/20 transition-colors cursor-pointer" onClick={() => { setShowNewConnector(true); setSelectedPlatform(platform.value); }}>
                <Icon className="w-8 h-8 mb-2 text-white" />
                <p className="text-sm font-medium">{platform.label}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Platform Selection Modal */}
      {showNewConnector && !selectedPlatform && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border shadow-lg rounded-2xl w-full max-w-2xl animate-in zoom-in-95 duration-200">
            <div className="p-6 border-b border-border flex items-center justify-between">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Plug className="w-6 h-6 text-indigo-500" /> Selecciona una Plataforma
              </h2>
              <Button variant="ghost" size="icon" onClick={() => { setShowNewConnector(false); setAcceptedToS(false); }}>✕</Button>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {platforms.map((platform) => {
                  const Icon = platform.icon;
                  return (
                    <button key={platform.value} onClick={() => setSelectedPlatform(platform.value)} className="p-6 rounded-xl border-2 border-border hover:border-indigo-500/50 transition-all text-center group bg-background">
                      <div className={`w-16 h-16 rounded-2xl ${platform.color} flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform shadow-sm`}>
                        <Icon className="w-8 h-8 text-white" />
                      </div>
                      <p className="font-semibold text-base">{platform.label}</p>
                      <p className="text-xs text-muted-foreground mt-1">{platform.description}</p>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Configuration Modal */}
      {showNewConnector && selectedPlatform && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border shadow-lg rounded-2xl w-full max-w-xl animate-in zoom-in-95 duration-200">
            <div className="p-6 border-b border-border flex items-center justify-between">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Plug className="w-6 h-6 text-indigo-500" /> Configurar {platforms.find(p => p.value === selectedPlatform)?.label}
              </h2>
              <Button variant="ghost" size="icon" onClick={() => { setShowNewConnector(false); setSelectedPlatform(''); }}>✕</Button>
            </div>

            <div className="p-6 space-y-5">
              <div>
                <label className="block text-sm font-medium mb-2">Nombre del Conector</label>
                <input type="text" value={newConnector.name} onChange={(e) => setNewConnector({ ...newConnector, name: e.target.value })} placeholder="Ej: Mi Bot Principal" className="w-full px-4 py-3 bg-background rounded-xl border border-border outline-none focus:border-indigo-500" />
              </div>

              {selectedPlatform === 'telegram' && (
                <div>
                  <label className="block text-sm font-medium mb-2">Bot Token</label>
                  <input type="text" value={newConnector.botToken} onChange={(e) => setNewConnector({ ...newConnector, botToken: e.target.value })} placeholder="123456789:ABCdefGHIjklMNOpqrSTUvwxYZ" className="w-full px-4 py-3 bg-background rounded-xl border border-border outline-none focus:border-indigo-500" />
                  <p className="text-xs text-muted-foreground mt-2">Obtén el token de tu bot desde @BotFather en Telegram</p>
                </div>
              )}

              {(selectedPlatform === 'whatsapp_evolution' || selectedPlatform === 'whatsapp_cloud') && (
                <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4 mb-4">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-yellow-500 shrink-0 mt-0.5" />
                    <div className="space-y-2">
                      <h4 className="font-semibold text-yellow-600">Términos de Servicio - WhatsApp</h4>
                      <div className="text-sm text-yellow-600/80 space-y-1">
                        <p>Al conectar WhatsApp, aceptas que:</p>
                        <ul className="list-disc pl-4 space-y-1">
                          <li>Cumplirás con las Políticas Comerciales de WhatsApp.</li>
                          <li>Obtendrás consentimiento explícito antes de enviar mensajes.</li>
                          <li>FluxAgent no almacenará el contenido más de 72 horas.</li>
                        </ul>
                      </div>
                      <label className="flex items-center gap-2 mt-3 cursor-pointer">
                        <input type="checkbox" checked={acceptedToS} onChange={(e) => setAcceptedToS(e.target.checked)} className="rounded border-yellow-500/30 text-yellow-600 focus:ring-yellow-500" />
                        <span className="text-sm font-medium text-yellow-600">Acepto los términos y condiciones (Cláusula 8)</span>
                      </label>
                    </div>
                  </div>
                </div>
              )}

              {selectedPlatform === 'whatsapp_evolution' && (
                <div>
                  <label className="block text-sm font-medium mb-2">Número de WhatsApp</label>
                  <input type="text" value={newConnector.phoneNumber} onChange={(e) => setNewConnector({ ...newConnector, phoneNumber: e.target.value })} placeholder="+52 55 1234 5678" className="w-full px-4 py-3 bg-background rounded-xl border border-border outline-none focus:border-indigo-500" />
                </div>
              )}

              {selectedPlatform === 'whatsapp_cloud' && (
                <div className="text-center py-4">
                  <Plug className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
                  <h3 className="font-semibold text-lg">Configuración de Cloud API</h3>
                  <p className="text-sm text-muted-foreground mt-2">Serás redirigido al asistente paso a paso para vincular tu cuenta de Meta Business y configurar el Webhook oficial.</p>
                </div>
              )}

              {selectedPlatform === 'instagram' && (
                <div>
                  <label className="block text-sm font-medium mb-2">API Key de Instagram</label>
                  <input type="text" value={newConnector.apiKey} onChange={(e) => setNewConnector({ ...newConnector, apiKey: e.target.value })} placeholder="IGQVJV..." className="w-full px-4 py-3 bg-background rounded-xl border border-border outline-none focus:border-indigo-500" />
                </div>
              )}

              {selectedPlatform === 'webchat' && (
                <div>
                  <label className="block text-sm font-medium mb-2">Webhook URL</label>
                  <input type="url" value={newConnector.webhook} onChange={(e) => setNewConnector({ ...newConnector, webhook: e.target.value })} placeholder="https://tudominio.com/webhook" className="w-full px-4 py-3 bg-background rounded-xl border border-border outline-none focus:border-indigo-500" />
                </div>
              )}
            </div>

            <div className="p-6 border-t border-border flex items-center justify-end gap-3 bg-secondary/30 rounded-b-2xl">
              <Button variant="ghost" onClick={() => { setSelectedPlatform(''); setAcceptedToS(false); }} className="rounded-xl">Volver</Button>
              <Button 
                onClick={handleAddConnector} 
                className="rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white"
                disabled={(selectedPlatform.includes('whatsapp') && !acceptedToS)}
              >
                <Zap className="w-4 h-4 mr-2" /> {selectedPlatform === 'whatsapp_cloud' ? 'Iniciar Asistente' : 'Conectar'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Cloud API Wizard */}
      {showCloudWizard && (
        <WhatsAppCloudWizard 
          onClose={() => setShowCloudWizard(false)} 
          onSuccess={(config) => {
            const newC: Connector = {
              id: Date.now().toString(),
              name: 'WhatsApp Cloud API',
              platform: 'whatsapp',
              status: 'connected',
              lastActivity: 'Ahora',
              messages: 0,
              conversations: 0,
              enabled: true,
              config: config
            };
            setConnectors([newC, ...connectors]);
            setShowCloudWizard(false);
            setAcceptedToS(false);
            setSelectedPlatform('');
            toast.success("WhatsApp Cloud API integrado correctamente");
          }} 
        />
      )}
    </div>
  );
}
