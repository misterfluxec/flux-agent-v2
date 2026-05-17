'use client';

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  MessageCircle, 
  Send, 
  Code2, 
  Smartphone, 
  Globe, 
  CheckCircle2, 
  Activity, 
  PlayCircle,
  MessageSquare,
  Clock,
  Loader2
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api-client';
import { ChannelConfig, ChannelStatus } from '@/types/channels';
import { PermissionGate } from '@/components/system/PermissionGate';
import { SystemStatus } from '@/constants/status';

// Mapeo seguro a la arquitectura de status estandar
const normalizeStatus = (rawStatus?: string) => {
  if (!rawStatus) return SystemStatus.DISCONNECTED;
  if (rawStatus === 'connected') return SystemStatus.CONNECTED;
  if (rawStatus === 'error') return SystemStatus.DEGRADED;
  return SystemStatus.PENDING;
};
// In a real app this would subscribe to the EventBus
function useRealtimeEvents(events: string[], callback: (event: any) => void) {
  useEffect(() => {
    // Implement standard WS listener here
  }, []);
}

// ============================================================================
// SHARED COMPONENTS
// ============================================================================

const HealthMetric = ({ label, value, status }: { label: string, value: string, status: 'good' | 'warning' | 'error' | 'neutral' }) => {
  const colors = {
    good: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    warning: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    error: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
    neutral: 'text-slate-400 bg-slate-500/10 border-slate-500/20'
  };

  return (
    <div className="flex items-center justify-between p-2.5 bg-white/[0.02] border border-white/5 rounded-lg">
      <span className="text-xs text-slate-400">{label}</span>
      <span className={cn("text-[10px] font-bold px-2 py-0.5 rounded border", colors[status])}>
        {value}
      </span>
    </div>
  );
};

const AuditTimeline = ({ events }: { events: { time: string, message: string }[] }) => (
  <div className="mt-6 pt-6 border-t border-white/5">
    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Lifecycle Timeline</h4>
    <div className="space-y-3">
      {events.map((e, i) => (
        <div key={i} className="flex gap-3">
          <div className="text-[10px] font-mono text-slate-500 mt-0.5">{e.time}</div>
          <div className="text-xs text-slate-300">{e.message}</div>
        </div>
      ))}
    </div>
  </div>
);

// ============================================================================
// CHANNEL PANELS
// ============================================================================

const WhatsAppPanel = ({ channel }: { channel?: ChannelConfig }) => {
  const queryClient = useQueryClient();
  const [phone, setPhone] = useState('');
  
  const status = channel?.status || 'disconnected';

  const requestQr = useMutation({
    mutationFn: (phoneNumber: string) => apiClient.post('/channels/whatsapp/qr', { phone_number: phoneNumber }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['channels'] }),
    onError: () => toast.error("Error solicitando QR")
  });

  const connectMock = useMutation({
    mutationFn: () => apiClient.post('/channels/connect', { type: 'whatsapp', config: { qr_scanned: true } }),
    onSuccess: () => {
      toast.success("Dispositivo conectado!");
      queryClient.invalidateQueries({ queryKey: ['channels'] });
    }
  });

  const testConnection = useMutation({
    mutationFn: () => apiClient.post('/channels/test-connection', { channel: 'whatsapp' }),
    onSuccess: (res) => toast.success(`Round-trip RTT: ${res.data.latency_ms}ms`)
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex gap-6">
        {/* Left Column: Connection Journey */}
        <div className="w-1/2 space-y-4">
          <h3 className="text-sm font-bold text-white mb-4">Connection Journey</h3>
          
          {status === 'disconnected' && (
            <div className="p-4 bg-white/[0.02] border border-white/10 rounded-xl">
              <label className="text-xs font-bold text-slate-400 mb-2 block">Número (con código país)</label>
              <input 
                value={phone}
                onChange={e => setPhone(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-white mb-4" 
                placeholder="+593999999999"
              />
              <PermissionGate feature="channels.manage">
                <Button 
                  onClick={() => requestQr.mutate(phone)} 
                  disabled={requestQr.isPending || !phone}
                  className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold"
                >
                  {requestQr.isPending ? <Loader2 className="animate-spin w-4 h-4 mr-2" /> : null}
                  Generar QR Code
                </Button>
              </PermissionGate>
            </div>
          )}

          {status === 'awaiting_qr_scan' && (
            <div className="p-4 bg-white/[0.02] border border-emerald-500/20 rounded-xl relative overflow-hidden group text-center">
              <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500" />
              <p className="text-sm font-bold text-white mb-4">Escanea el QR</p>
              <div className="w-48 h-48 bg-white mx-auto rounded-lg mb-4 flex items-center justify-center">
                {/* Mock Image display */}
                <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==" className="w-full h-full object-cover p-2 border-2 border-black border-dashed" alt="QR" />
              </div>
              <PermissionGate feature="channels.manage">
                <Button 
                  onClick={() => connectMock.mutate()} 
                  className="w-full bg-white/10 hover:bg-white/20 text-white font-bold"
                >
                  ✅ Simular Escaneo Exitoso
                </Button>
              </PermissionGate>
            </div>
          )}

          {status === 'connected' && (
            <>
              <div className="p-4 bg-white/[0.02] border border-emerald-500/20 rounded-xl relative overflow-hidden group">
                <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500" />
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-emerald-400 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4" /> Paso 1: Scan QR
                  </span>
                  <span className="text-[10px] text-slate-500">Completado</span>
                </div>
                <p className="text-xs text-slate-400">Dispositivo vinculado correctamente</p>
              </div>

              <div className="p-4 bg-white/[0.02] border border-cyan-500/30 rounded-xl relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-cyan-500" />
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-cyan-400 flex items-center gap-2">
                    <Activity className="w-4 h-4" /> Operational Test
                  </span>
                </div>
                <p className="text-xs text-slate-400 mb-3">Verifica latencia Round-Trip (Websockets & EventBus).</p>
                <PermissionGate feature="channels.test_connection">
                  <Button 
                    onClick={() => testConnection.mutate()} 
                    disabled={testConnection.isPending}
                    size="sm" 
                    className="bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 w-full font-bold"
                  >
                    {testConnection.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <PlayCircle className="w-4 h-4 mr-2" />}
                    Test Connection
                  </Button>
                </PermissionGate>
              </div>
            </>
          )}
        </div>

        {/* Right Column: Health & Operations */}
        <div className="w-1/2 space-y-6">
          <div>
            <h3 className="text-sm font-bold text-white mb-4">Technical Health Layer</h3>
            <div className="grid grid-cols-2 gap-2">
              <HealthMetric 
                label="Session Status" 
                value={status === 'connected' ? "AUTHENTICATED" : status.toUpperCase()} 
                status={status === 'connected' ? 'good' : (status === 'error' ? 'error' : 'warning')} 
              />
              <HealthMetric 
                label="Health Score" 
                value={channel?.health_score ? `${channel.health_score}%` : "N/A"} 
                status={channel?.health_score === 100 ? 'good' : 'warning'} 
              />
              <HealthMetric label="Webhook" value={status === 'connected' ? "HEALTHY" : "PENDING"} status={status === 'connected' ? 'good' : 'neutral'} />
              <HealthMetric label="Rate Limit" value="NORMAL" status="neutral" />
            </div>
          </div>

          {status === 'connected' && (
            <div>
              <h3 className="text-sm font-bold text-white mb-4">Operational Status</h3>
              <div className="grid grid-cols-2 gap-2">
                <div className="p-4 bg-white/[0.02] border border-white/5 rounded-xl text-center">
                  <div className="text-2xl font-black text-white">0</div>
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider mt-1">Messages Today</div>
                </div>
                <div className="p-4 bg-white/[0.02] border border-white/5 rounded-xl text-center">
                  <div className="text-2xl font-black text-amber-400">0</div>
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider mt-1">Human Handoffs</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {status === 'connected' && (
        <AuditTimeline events={[
          { time: channel?.updated_at || "N/A", message: "Channel State transitioned to CONNECTED." },
          { time: channel?.created_at || "N/A", message: "QR Code successfully scanned and session linked." },
        ]} />
      )}
    </div>
  );
};

const TelegramPanel = ({ channel }: { channel?: ChannelConfig }) => {
  const queryClient = useQueryClient();
  const [token, setToken] = useState('');
  const status = channel?.status || 'disconnected';

  const connect = useMutation({
    mutationFn: () => apiClient.post('/channels/connect', { type: 'telegram', config: { bot_token: token } }),
    onSuccess: () => {
      toast.success("Telegram Bot Connected!");
      queryClient.invalidateQueries({ queryKey: ['channels'] });
    }
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex gap-6">
        <div className="w-1/2 space-y-4">
          <h3 className="text-sm font-bold text-white mb-4">Connection Journey</h3>
          
          <div className="space-y-4">
            <div>
              <label className="text-xs font-bold text-slate-400 mb-2 block">Bot Token (from @BotFather)</label>
              <input 
                type="password" 
                value={token}
                onChange={e => setToken(e.target.value)}
                placeholder="123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                disabled={status === 'connected'}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/50 disabled:opacity-50" 
              />
            </div>
            {status !== 'connected' && (
              <PermissionGate feature="channels.manage">
                <Button 
                  onClick={() => connect.mutate()} 
                  disabled={!token || connect.isPending}
                  className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-bold"
                >
                  Verify Token & Connect
                </Button>
              </PermissionGate>
            )}
          </div>
        </div>

        <div className="w-1/2 space-y-6">
          <div>
            <h3 className="text-sm font-bold text-white mb-4">Technical Health Layer</h3>
            <div className="grid grid-cols-2 gap-2">
              <HealthMetric label="Bot Connected" value={status === 'connected' ? 'YES' : 'NO'} status={status === 'connected' ? 'good' : 'warning'} />
              <HealthMetric label="Webhook" value={status === 'connected' ? 'VALID' : 'PENDING'} status={status === 'connected' ? 'good' : 'neutral'} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const WebWidgetPanel = ({ channel }: { channel?: ChannelConfig }) => {
  const queryClient = useQueryClient();
  const [color, setColor] = useState("#2563eb");
  const [position, setPosition] = useState("right");
  const [agentName, setAgentName] = useState("Sales Bot");

  const status = channel?.status || 'disconnected';

  const connect = useMutation({
    mutationFn: () => apiClient.post('/channels/connect', { type: 'webchat', config: { enabled: true } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['channels'] })
  });

  const snippet = `<script
  src="https://cdn.fluxagent.com/widget.js"
  data-agent="${agentName}"
  data-color="${color}"
  data-position="${position}"
  defer
></script>`;

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex gap-6">
        <div className="w-1/2 space-y-4">
          <h3 className="text-sm font-bold text-white mb-4">Widget Configuration</h3>
          
          <div className="space-y-4">
            <div>
              <label className="text-xs font-bold text-slate-400 mb-2 block">Brand Color</label>
              <div className="flex gap-2">
                <input 
                  type="color" 
                  value={color}
                  onChange={e => setColor(e.target.value)}
                  className="w-10 h-10 rounded cursor-pointer bg-transparent border-0 p-0" 
                />
                <input 
                  type="text" 
                  value={color}
                  onChange={e => setColor(e.target.value)}
                  className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/50" 
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-400 mb-2 block">Agent Name</label>
              <input 
                type="text" 
                value={agentName}
                onChange={e => setAgentName(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/50" 
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-400 mb-2 block">Position</label>
              <select 
                value={position}
                onChange={e => setPosition(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/50"
              >
                <option value="right">Bottom Right</option>
                <option value="left">Bottom Left</option>
              </select>
            </div>

            {status !== 'connected' && (
              <PermissionGate feature="channels.manage">
                <Button 
                  onClick={() => connect.mutate()} 
                  className="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold mt-4"
                >
                  Activar Webhook Endpoint
                </Button>
              </PermissionGate>
            )}
          </div>
        </div>

        <div className="w-1/2 space-y-4">
          <h3 className="text-sm font-bold text-white mb-4">Embed Snippet</h3>
          <div className="p-4 bg-black/60 border border-white/10 rounded-xl">
            <pre className="text-xs font-mono text-emerald-400 overflow-x-auto whitespace-pre-wrap">
              {snippet}
            </pre>
          </div>
          <Button onClick={() => navigator.clipboard.writeText(snippet).then(() => toast.success("Snippet copied!"))} className="w-full bg-white/10 hover:bg-white/20 text-white font-bold">
            Copy Snippet
          </Button>

          <HealthMetric label="Webhook Status" value={status === 'connected' ? 'ACTIVE' : 'INACTIVE'} status={status === 'connected' ? 'good' : 'neutral'} />
        </div>
      </div>
    </div>
  );
};

const ComingSoonPanel = ({ name }: { name: string }) => (
  <div className="flex flex-col items-center justify-center py-20 animate-in fade-in duration-500">
    <div className="h-16 w-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mb-6">
      <Clock className="w-8 h-8 text-white/20" />
    </div>
    <h3 className="text-xl font-bold text-white mb-2">{name} Integration</h3>
    <p className="text-sm text-slate-400 mb-6 text-center max-w-sm">
      Planned for Beta Phase 2. This will allow seamless bidirectional messaging with {name} users.
    </p>
    <div className="px-4 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-bold uppercase tracking-wider">
      Coming Soon
    </div>
  </div>
);

const CustomAPIPanel = ({ channel }: { channel?: ChannelConfig }) => {
  const queryClient = useQueryClient();
  const [provider, setProvider] = useState('evolution');
  const [apiUrl, setApiUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [instanceName, setInstanceName] = useState('');

  const status = channel?.status || 'disconnected';

  const connect = useMutation({
    mutationFn: () => apiClient.post('/channels/connect', { 
      type: 'custom_api', 
      config: { provider, apiUrl, apiKey, instanceName } 
    }),
    onSuccess: () => {
      toast.success("API Custom/Evolution conectada correctamente.");
      queryClient.invalidateQueries({ queryKey: ['channels'] });
    }
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex gap-6">
        <div className="w-1/2 space-y-4">
          <h3 className="text-sm font-bold text-white mb-4">Enterprise Gateway Connection</h3>
          <p className="text-xs text-slate-400 mb-4">
            Connect your own WhatsApp API infrastructure (e.g., Evolution API, WhaTicket) to maintain ownership of your instances.
          </p>
          
          <div className="space-y-4">
            <div>
              <label className="text-xs font-bold text-slate-400 mb-2 block">Proveedor API</label>
              <select 
                value={provider}
                onChange={e => setProvider(e.target.value)}
                disabled={status === 'connected'}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/50"
              >
                <option value="evolution">Evolution API</option>
                <option value="whaticket">WhaTicket API</option>
                <option value="generic">Generic Webhook</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-400 mb-2 block">URL de la API</label>
              <input 
                type="text" 
                value={apiUrl}
                onChange={e => setApiUrl(e.target.value)}
                placeholder="https://api.tuempresa.com"
                disabled={status === 'connected'}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/50 disabled:opacity-50" 
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-400 mb-2 block">Global API Key / Bearer Token</label>
              <input 
                type="password" 
                value={apiKey}
                onChange={e => setApiKey(e.target.value)}
                placeholder="••••••••••••••••"
                disabled={status === 'connected'}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/50 disabled:opacity-50" 
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-400 mb-2 block">Instance Name / ID</label>
              <input 
                type="text" 
                value={instanceName}
                onChange={e => setInstanceName(e.target.value)}
                placeholder="flux-main-instance"
                disabled={status === 'connected'}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/50 disabled:opacity-50" 
              />
            </div>

            {status !== 'connected' && (
              <PermissionGate feature="channels.manage">
                <Button 
                  onClick={() => connect.mutate()} 
                  disabled={!apiUrl || !apiKey || connect.isPending}
                  className="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold"
                >
                  Verify & Connect API
                </Button>
              </PermissionGate>
            )}
          </div>
        </div>

        <div className="w-1/2 space-y-6">
          <div>
            <h3 className="text-sm font-bold text-white mb-4">Technical Health Layer</h3>
            <div className="grid grid-cols-2 gap-2">
              <HealthMetric label="Gateway Status" value={status === 'connected' ? 'ACTIVE' : 'DISCONNECTED'} status={status === 'connected' ? 'good' : 'warning'} />
              <HealthMetric label="Auth Validate" value={status === 'connected' ? 'VALID' : 'PENDING'} status={status === 'connected' ? 'good' : 'neutral'} />
              <HealthMetric label="Webhook Link" value={status === 'connected' ? 'BOUND' : 'UNBOUND'} status={status === 'connected' ? 'good' : 'neutral'} />
              <HealthMetric label="Latency" value={status === 'connected' ? '45ms' : 'N/A'} status={status === 'connected' ? 'good' : 'neutral'} />
            </div>
            
            {status === 'connected' && (
              <div className="mt-6 p-4 bg-white/[0.02] border border-cyan-500/30 rounded-xl relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-cyan-500" />
                <h4 className="text-xs font-bold text-cyan-400 mb-2">Endpoint de Retorno (Webhook URL)</h4>
                <p className="text-[10px] text-slate-400 mb-3 leading-relaxed">
                  Configura esta URL en tu instancia de Evolution API (Set Webhook) para que FluxAgent reciba los mensajes.
                </p>
                <div className="bg-black/60 p-2 rounded text-xs font-mono text-emerald-400 overflow-x-auto whitespace-pre-wrap select-all">
                  https://api.fluxagent.com/v1/webhooks/evolution/{instanceName || 'instance-id'}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// MAIN PAGE COMPONENT
// ============================================================================

const CHANNELS_MAP = [
  { id: 'whatsapp', label: 'WhatsApp', icon: MessageCircle, component: WhatsAppPanel },
  { id: 'telegram', label: 'Telegram', icon: Send, component: TelegramPanel },
  { id: 'webchat', label: 'Web Widget', icon: Globe, component: WebWidgetPanel },
  { id: 'instagram', label: 'Instagram', icon: Smartphone, component: () => <ComingSoonPanel name="Instagram Direct" /> },
  { id: 'messenger', label: 'Messenger', icon: MessageSquare, component: () => <ComingSoonPanel name="Facebook Messenger" /> },
  { id: 'custom_api', label: 'BYO API (Evolution)', icon: Code2, component: CustomAPIPanel },
];

export default function ChannelsDashboard() {
  const queryClient = useQueryClient();
  const [activeChannel, setActiveChannel] = useState(CHANNELS_MAP[0].id);

  // 1. Fetch channel states from backend
  const { data: response, isLoading } = useQuery({
    queryKey: ['channels'],
    queryFn: () => apiClient.get<ChannelConfig[]>('/channels')
  });

  const channelsData = response?.data || [];

  // 2. Realtime Updates via Websocket events
  useRealtimeEvents(['channel.status_changed', 'channel.test_ack'], (event) => {
    // Invalidate react-query cache to re-fetch when WS pushes an event
    if (event.event_type === 'channel.status_changed') {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
      toast.info(`Channel ${event.channel} is now ${event.payload.status}`);
    } else if (event.event_type === 'channel.test_ack') {
      toast.success(`[WS] ${event.channel} test ACK received in ${event.payload.latency_ms}ms!`);
    }
  });

  const activeChannelData = channelsData.find((c) => c.channel_type === activeChannel);
  const ActiveComponent = CHANNELS_MAP.find(c => c.id === activeChannel)?.component || WhatsAppPanel;

  const disconnectChannel = useMutation({
    mutationFn: (id: string) => apiClient.post(`/channels/${id}/disconnect`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['channels'] })
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-700 pb-12 px-4 md:px-8 max-w-6xl mx-auto pt-8">
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white/90">
            Canales de <span className="text-cyan-400">Comunicación</span>
          </h1>
          <p className="text-white/40 text-sm mt-1">
            Supervisa el status técnico y operacional de tus integraciones conversacionales.
          </p>
        </div>
        {activeChannelData && activeChannelData.status === 'connected' && (
          <PermissionGate feature="channels.disconnect">
            <Button 
              variant="destructive" 
              className="bg-rose-900/30 text-rose-400 border border-rose-900/50 hover:bg-rose-900/50"
              onClick={() => disconnectChannel.mutate(activeChannelData.id)}
              disabled={disconnectChannel.isPending}
            >
              Desconectar Canal
            </Button>
          </PermissionGate>
        )}
      </div>

      <div className="flex gap-8">
        {/* Sidebar Navigation */}
        <div className="w-64 flex-shrink-0">
          <nav className="space-y-1">
            {CHANNELS_MAP.map(channel => {
              const Icon = channel.icon;
              const isActive = activeChannel === channel.id;
              const isConnected = channelsData.some(c => c.channel_type === channel.id && c.status === 'connected');
              
              return (
                <button
                  key={channel.id}
                  onClick={() => setActiveChannel(channel.id)}
                  className={cn(
                    "w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-bold transition-all text-left",
                    isActive 
                      ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20" 
                      : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.02] border border-transparent"
                  )}
                >
                  <span className="flex items-center gap-3">
                    <Icon className="w-4 h-4" />
                    {channel.label}
                  </span>
                  {isConnected && (
                    <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Active Panel Content */}
        <div className="flex-1 min-w-0 bg-black/40 backdrop-blur-xl border border-white/5 rounded-2xl p-8 min-h-[600px]">
          {isLoading ? (
            <div className="w-full h-full flex items-center justify-center">
              <Loader2 className="w-8 h-8 text-cyan-500 animate-spin" />
            </div>
          ) : (
            <ActiveComponent channel={activeChannelData} />
          )}
        </div>
      </div>
    </div>
  );
}
