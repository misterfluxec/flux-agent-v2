import { useState, useEffect } from 'react';
import { Clock, Bot, ArrowRight, AlertTriangle, ShieldCheck, Zap } from 'lucide-react';
import { api } from '@/lib/api';

export function StepSyncConfig({ config, onUpdate, onConfirm, onBack }: any) {
  const [localConfig, setLocalConfig] = useState(config || { frequency: 'daily', agentId: '', conflictResolution: 'overwrite' });
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const res = await api.get('/api/v1/agents/');
        setAgents(res.data);
        // Si hay un agente llamado Yanua, seleccionarlo por defecto
        const yanua = res.data.find((a: any) => a.nombre.toLowerCase().includes('yanua'));
        if (yanua && !localConfig.agentId) {
          handleChange('agentId', yanua.id);
        } else if (res.data.length > 0 && !localConfig.agentId) {
          handleChange('agentId', res.data[0].id);
        }
      } catch (error) {
        console.error("Error fetching agents:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchAgents();
  }, []);

  const handleChange = (key: string, value: string) => setLocalConfig((prev: any) => ({ ...prev, [key]: value }));

  const frequencies = [
    { id: 'manual', label: 'Solo Manual', desc: 'Sincroniza cuando tú lo decidas', icon: Clock },
    { id: 'hourly', label: 'Cada Hora', desc: 'Mantiene datos frescos (60 min)', icon: Zap },
    { id: 'daily', label: 'Diario', desc: 'Actualización cada 24 horas', icon: Clock },
    { id: 'realtime', label: 'Tiempo Real', desc: 'Vía Webhooks (Solo APIs)', icon: Zap },
  ];

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Frecuencia */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="p-2 bg-indigo-500/10 rounded-lg border border-indigo-500/20">
              <Clock className="w-4 h-4 text-indigo-400" />
            </div>
            <h3 className="font-bold text-white uppercase text-xs tracking-widest">Frecuencia de Sincronización</h3>
          </div>
          
          <div className="grid grid-cols-1 gap-3">
            {frequencies.map(f => (
              <label 
                key={f.id} 
                className={`group relative flex items-center gap-4 p-4 rounded-2xl border-2 cursor-pointer transition-all duration-300 ${
                  localConfig.frequency === f.id 
                    ? 'border-indigo-500 bg-indigo-500/10 shadow-[0_0_20px_-5px_rgba(99,102,241,0.2)]' 
                    : 'border-gray-800 bg-gray-900/40 hover:border-gray-700'
                }`}
              >
                <input type="radio" name="freq" checked={localConfig.frequency === f.id} onChange={() => handleChange('frequency', f.id)} className="hidden" />
                <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${localConfig.frequency === f.id ? 'border-indigo-500' : 'border-gray-600'}`}>
                  {localConfig.frequency === f.id && <div className="w-2.5 h-2.5 bg-indigo-500 rounded-full animate-in zoom-in-50" />}
                </div>
                <div>
                  <p className="text-sm font-bold text-white">{f.label}</p>
                  <p className="text-[10px] text-gray-500">{f.desc}</p>
                </div>
                {f.id === 'realtime' && (
                  <span className="absolute top-2 right-2 text-[8px] font-bold bg-amber-500/20 text-amber-500 px-2 py-0.5 rounded-full border border-amber-500/20">BETA</span>
                )}
              </label>
            ))}
          </div>
        </div>

        {/* Agente y Conflicto */}
        <div className="space-y-6">
          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="p-2 bg-purple-500/10 rounded-lg border border-purple-500/20">
                <Bot className="w-4 h-4 text-purple-400" />
              </div>
              <h3 className="font-bold text-white uppercase text-xs tracking-widest">Cerebro Destino</h3>
            </div>
            
            <div className="relative">
              <select 
                value={localConfig.agentId} 
                onChange={(e) => handleChange('agentId', e.target.value)} 
                disabled={loading}
                className="w-full bg-black/60 border-2 border-gray-800 rounded-2xl p-4 text-sm font-medium text-white focus:border-indigo-500 outline-none appearance-none transition-all cursor-pointer shadow-xl"
              >
                {loading ? (
                  <option>Cargando agentes...</option>
                ) : (
                  <>
                    <option value="" disabled>Selecciona un agente...</option>
                    {agents.map(a => (
                      <option key={a.id} value={a.id}>{a.nombre} (V{a.version || '1.0'})</option>
                    ))}
                  </>
                )}
              </select>
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-gray-500">
                <ArrowRight className="w-4 h-4 rotate-90" />
              </div>
            </div>

            <div className="flex items-start gap-3 bg-indigo-500/5 border border-indigo-500/10 rounded-2xl p-4">
              <ShieldCheck className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p className="text-xs font-bold text-indigo-300">Seguridad de Datos</p>
                <p className="text-[10px] text-gray-500 leading-relaxed">
                  Los datos vectorizados se cifrarán y almacenarán en un espacio privado aislado para este agente. Solo accesible bajo permisos del Tenant.
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-bold text-gray-500 uppercase text-[10px] tracking-widest">Resolución de Conflictos</h3>
            </div>
            <div className="flex gap-2">
              {['overwrite', 'skip'].map(mode => (
                <button
                  key={mode}
                  onClick={() => handleChange('conflictResolution', mode)}
                  className={`flex-1 py-3 px-4 rounded-xl border text-[10px] font-bold transition-all ${
                    localConfig.conflictResolution === mode 
                      ? 'border-indigo-500/50 bg-indigo-500/10 text-indigo-400' 
                      : 'border-gray-800 bg-black/20 text-gray-500 hover:border-gray-700'
                  }`}
                >
                  {mode === 'overwrite' ? 'SOBREESCRIBIR EXISTENTE' : 'OMITIR DUPLICADOS'}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-between items-center pt-8 border-t border-gray-800/50">
        <button onClick={onBack} className="px-6 py-2.5 text-sm font-medium text-gray-500 hover:text-white transition-colors">
          Atrás
        </button>
        <button 
          onClick={() => { onUpdate(localConfig); onConfirm(); }} 
          disabled={!localConfig.agentId} 
          className="px-10 py-3 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 disabled:from-gray-800 disabled:to-gray-900 disabled:text-gray-600 disabled:cursor-not-allowed rounded-2xl text-sm font-extrabold flex items-center gap-3 transition-all shadow-xl shadow-indigo-600/20 active:scale-95"
        >
          Iniciar Entrenamiento <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
