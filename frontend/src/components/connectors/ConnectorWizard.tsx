import React, { useState, useEffect } from 'react';
import { X, Check, Database, Loader2, Wand2, ArrowRight, Server, Table } from 'lucide-react';

interface ConnectorWizardProps {
  onClose: () => void;
}

type WizardStep = 'provider' | 'credentials' | 'discovery' | 'mapping';

export function ConnectorWizard({ onClose }: ConnectorWizardProps) {
  const [step, setStep] = useState<WizardStep>('provider');
  const [provider, setProvider] = useState<string>('');
  const [sessionId, setSessionId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [schema, setSchema] = useState<any>(null);

  // Formularios de credenciales (mock para el demo)
  const [host, setHost] = useState('db.empresa.local');
  const [user, setUser] = useState('admin');
  const [pass, setPass] = useState('********');

  const handleProviderSelect = async (selected: string) => {
    setProvider(selected);
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/integrations/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: selected, tenant_id: 'demo-tenant' })
      });
      if (!res.ok) throw new Error('Error al iniciar sesión');
      const data = await res.json();
      setSessionId(data.session_id);
      setStep('credentials');
    } catch (err: any) {
      setError(err.message);
      // Fallback para UI
      setSessionId('mock-session-id');
      setStep('credentials');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestConnection = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/integrations/sessions/${sessionId}/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credentials: { host, user, pass }, tenant_id: 'demo-tenant' })
      });
      if (!res.ok) throw new Error('Fallo en conexión');
      
      // Iniciar discovery directamente si la conexión es exitosa
      handleStartDiscovery();
    } catch (err: any) {
      setError(err.message);
      handleStartDiscovery(); // Fallback
    }
  };

  const handleStartDiscovery = async () => {
    setStep('discovery');
    setIsLoading(true);
    try {
      await fetch(`/api/v1/integrations/sessions/${sessionId}/discover`, {
        method: 'POST'
      });
      pollDiscoveryStatus();
    } catch (err) {
      pollDiscoveryStatus(); // Fallback loop
    }
  };

  const pollDiscoveryStatus = () => {
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      try {
        const res = await fetch(`/api/v1/integrations/sessions/${sessionId}`);
        if (res.ok) {
          const data = await res.json();
          if (data.status === 'mapping') {
            clearInterval(interval);
            setSchema(data.discovered_schema);
            setStep('mapping');
            setIsLoading(false);
          }
        }
      } catch (err) {
        console.error("Polling error", err);
      }

      // Fallback seguro después de 3 segundos para el Demo UI si falla el backend
      if (attempts >= 3) {
        clearInterval(interval);
        setSchema({
            tables: [{
                name: "dbo.Products",
                columns: [
                    {name: "ProductId"}, {name: "ProductName"}, {name: "FinalPrice"}
                ]
            }]
        });
        setStep('mapping');
        setIsLoading(false);
      }
    }, 1500);
  };

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-[90%] max-w-3xl bg-slate-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/5 bg-slate-900">
          <div>
            <h2 className="text-xl font-bold text-slate-100">Nueva Integración</h2>
            <p className="text-sm text-slate-400 mt-1">Conecta tu sistema para mantener los datos sincronizados.</p>
          </div>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-white/5 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 bg-slate-900">
          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-lg">
              {error}
            </div>
          )}

          {step === 'provider' && (
            <div className="grid grid-cols-2 gap-4">
              <button onClick={() => handleProviderSelect('sqlserver')} className="flex flex-col items-center justify-center p-6 border border-white/10 rounded-xl bg-slate-800/50 hover:bg-indigo-500/10 hover:border-indigo-500/50 transition-all text-slate-300 hover:text-white group">
                <Database className="w-12 h-12 mb-3 text-slate-500 group-hover:text-indigo-400 transition-colors" />
                <span className="font-semibold">SQL Server</span>
                <span className="text-xs text-slate-500 mt-1">Conexión Directa DB</span>
              </button>
              
              <button onClick={() => handleProviderSelect('sap_b1')} className="flex flex-col items-center justify-center p-6 border border-white/10 rounded-xl bg-slate-800/50 hover:bg-blue-500/10 hover:border-blue-500/50 transition-all text-slate-300 hover:text-white group">
                <Server className="w-12 h-12 mb-3 text-slate-500 group-hover:text-blue-400 transition-colors" />
                <span className="font-semibold">SAP Business One</span>
                <span className="text-xs text-slate-500 mt-1">HANA / SQL API</span>
              </button>

              <button onClick={() => handleProviderSelect('csv')} className="flex flex-col items-center justify-center p-6 border border-white/10 rounded-xl bg-slate-800/50 hover:bg-emerald-500/10 hover:border-emerald-500/50 transition-all text-slate-300 hover:text-white group">
                <Table className="w-12 h-12 mb-3 text-slate-500 group-hover:text-emerald-400 transition-colors" />
                <span className="font-semibold">Archivo Excel / CSV</span>
                <span className="text-xs text-slate-500 mt-1">Subida estática</span>
              </button>
            </div>
          )}

          {step === 'credentials' && (
            <div className="space-y-4 max-w-lg mx-auto">
              <div className="p-4 bg-indigo-500/10 border border-indigo-500/20 rounded-xl mb-6">
                <p className="text-sm text-indigo-300 flex items-center gap-2">
                  <Database className="w-4 h-4" /> Configurando <strong>{provider.toUpperCase()}</strong>
                </p>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Host / URL</label>
                <input value={host} onChange={e => setHost(e.target.value)} type="text" className="w-full bg-slate-950 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Usuario</label>
                  <input value={user} onChange={e => setUser(e.target.value)} type="text" className="w-full bg-slate-950 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Contraseña</label>
                  <input value={pass} onChange={e => setPass(e.target.value)} type="password" className="w-full bg-slate-950 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500" />
                </div>
              </div>
            </div>
          )}

          {step === 'discovery' && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Loader2 className="w-12 h-12 text-indigo-500 animate-spin mb-4" />
              <h3 className="text-lg font-medium text-slate-200">Leyendo esquema de datos...</h3>
              <p className="text-sm text-slate-400 mt-2 max-w-sm">
                Estamos conectándonos a <strong>{provider.toUpperCase()}</strong> para extraer la lista de tablas y columnas disponibles.
              </p>
            </div>
          )}

          {step === 'mapping' && (
            <div className="space-y-6">
              <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-xl p-4 flex items-start gap-4">
                <Wand2 className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-semibold text-indigo-300">Esquema Descubierto (Auto Mapped)</h4>
                  <p className="text-xs text-indigo-200/70 mt-1">
                    Detectamos la tabla <strong>{schema?.tables[0]?.name || 'Productos'}</strong>. Hemos sugerido el siguiente mapeo hacia el Catálogo Canónico.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-[1fr_auto_1fr] gap-4 items-center">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider text-center">Columna Origen ({provider})</div>
                <div className="w-6"></div>
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider text-center">Campo FluxAgent</div>
                
                {/* Mapping Row 1 */}
                <div className="p-3 rounded bg-slate-800 border border-white/5 text-sm font-medium text-slate-300 text-center">ProductId</div>
                <ArrowRight className="w-4 h-4 text-slate-500" />
                <div className="p-3 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium text-center">sku</div>

                {/* Mapping Row 2 */}
                <div className="p-3 rounded bg-slate-800 border border-white/5 text-sm font-medium text-slate-300 text-center">ProductName</div>
                <ArrowRight className="w-4 h-4 text-slate-500" />
                <div className="p-3 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium text-center">name</div>

                {/* Mapping Row 3 */}
                <div className="p-3 rounded bg-slate-800 border border-white/5 text-sm font-medium text-slate-300 text-center">FinalPrice</div>
                <ArrowRight className="w-4 h-4 text-slate-500" />
                <div className="p-3 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium text-center">price</div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-white/5 bg-slate-900/50 flex justify-end gap-3">
          {step !== 'discovery' && (
            <button onClick={onClose} disabled={isLoading} className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors">
              Cancelar
            </button>
          )}
          
          {step === 'credentials' && (
            <button onClick={handleTestConnection} disabled={isLoading} className="flex items-center gap-2 bg-indigo-500 hover:bg-indigo-400 text-white px-5 py-2 rounded-lg font-medium transition-colors">
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Probar Conexión & Continuar'}
            </button>
          )}

          {step === 'mapping' && (
            <button onClick={onClose} className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white px-5 py-2 rounded-lg font-medium transition-colors">
              <Check className="w-4 h-4" />
              Confirmar & Activar Sync
            </button>
          )}
        </div>

      </div>
    </div>
  );
}
