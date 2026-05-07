import { useState } from 'react';
import { ExternalLink, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

export function StepRemoteConnection({ sourceType, onDataLoaded, onBack }: any) {
  const [status, setStatus] = useState<'idle' | 'connecting' | 'success' | 'error'>('idle');
  const [preview, setPreview] = useState<any>(null);
  const [error, setError] = useState('');

  const handleConnect = async () => {
    setStatus('connecting');
    setError('');
    try {
      // En producción real: window.location.href = `/api/v1/oauth/authorize/${sourceType}`;
      // Aquí simulamos el proceso de autorización y obtención de preview
      await new Promise(r => setTimeout(r, 1500));
      
      // Simulamos una respuesta exitosa del backend tras la conexión OAuth
      const mockData = {
        headers: ['ID', 'Producto', 'Precio', 'Categoría', 'Stock'],
        preview_rows: [
          { ID: 'S-001', Producto: 'Suscripción Premium', Precio: '49.99', Categoría: 'Servicios', Stock: '∞' },
          { ID: 'S-002', Producto: 'Pack de Créditos', Precio: '19.99', Categoría: 'Consumibles', Stock: '1000' },
          { ID: 'S-003', Producto: 'Consultoría IA', Precio: '150.00', Categoría: 'Servicios', Stock: '5' }
        ]
      };
      
      setPreview(mockData);
      setStatus('success');
    } catch (err: any) {
      setStatus('error');
      setError(err.message || 'Error de conexión');
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className={`relative overflow-hidden border-2 border-dashed rounded-[2rem] p-10 text-center transition-all duration-500 ${
        status === 'success' 
          ? 'border-emerald-500/50 bg-emerald-500/5 shadow-[0_0_40px_-10px_rgba(16,185,129,0.2)]' 
          : 'border-gray-800 bg-gray-900/20 hover:border-indigo-500/40'
      }`}>
        {/* Decorative Background */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 blur-3xl rounded-full" />
        
        {status === 'idle' && (
          <button onClick={handleConnect} className="flex flex-col items-center gap-4 group mx-auto">
            <div className="p-5 bg-indigo-500/10 rounded-2xl group-hover:bg-indigo-500/20 group-hover:scale-110 transition-all duration-500 border border-indigo-500/20 shadow-xl">
              <ExternalLink className="w-8 h-8 text-indigo-400" />
            </div>
            <div className="space-y-1">
              <p className="text-lg font-bold text-white">Conectar con {sourceType === 'sheets' ? 'Google Sheets' : 'Microsoft Excel'}</p>
              <p className="text-sm text-gray-500">Te redirigiremos para autorizar el acceso de lectura a Yanua.</p>
            </div>
            <div className="mt-2 px-6 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-sm font-bold transition-all shadow-lg shadow-indigo-600/20">
              Autorizar Acceso
            </div>
          </button>
        )}

        {status === 'connecting' && (
          <div className="flex flex-col items-center gap-4 py-4">
            <div className="relative">
              <div className="absolute inset-0 bg-indigo-500/20 rounded-full blur-xl animate-pulse" />
              <Loader2 className="w-10 h-10 animate-spin text-indigo-400 relative z-10" />
            </div>
            <p className="text-sm font-medium text-gray-300">Estableciendo túnel de datos seguro...</p>
          </div>
        )}

        {status === 'success' && preview && (
          <div className="space-y-4 py-2">
            <div className="w-12 h-12 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto border border-emerald-500/30">
              <CheckCircle className="w-6 h-6 text-emerald-400" />
            </div>
            <div className="space-y-1">
              <p className="text-lg font-bold text-emerald-400">¡Conexión Exitosa!</p>
              <p className="text-xs text-gray-500">Se han detectado {preview.preview_rows?.length || 0} columnas listas para mapear.</p>
            </div>
          </div>
        )}

        {status === 'error' && (
          <div className="flex flex-col items-center gap-4 py-4">
            <div className="p-4 bg-rose-500/10 rounded-2xl border border-rose-500/20">
              <AlertCircle className="w-8 h-8 text-rose-400" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-bold text-rose-400">Error de Conexión</p>
              <p className="text-xs text-gray-500">{error}</p>
            </div>
            <button onClick={handleConnect} className="text-xs font-bold text-indigo-400 hover:underline">Reintentar</button>
          </div>
        )}
      </div>

      {status === 'success' && preview && (
        <div className="bg-black/40 backdrop-blur-xl rounded-2xl border border-gray-800/80 overflow-hidden shadow-2xl animate-in fade-in slide-in-from-top-2 duration-700">
          <div className="px-5 py-3 bg-gray-800/30 border-b border-gray-800/50 flex items-center justify-between">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-widest">Vista previa remota</p>
            <span className="text-[10px] bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/20">LIVE DATA</span>
          </div>
          <div className="p-4 overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-gray-800/50">
                  {preview.headers.map((h: string) => (
                    <th key={h} className="px-3 py-2 text-gray-400 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.preview_rows.slice(0, 3).map((row: any, i: number) => (
                  <tr key={i} className="border-b border-gray-800/30 last:border-0">
                    {preview.headers.map((h: string) => (
                      <td key={h} className="px-3 py-2 text-gray-300 font-mono truncate max-w-[150px]">{row[h]}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="flex justify-between items-center pt-6 border-t border-gray-800/50">
        <button onClick={onBack} className="px-6 py-2.5 text-sm font-medium text-gray-500 hover:text-white transition-colors">
          Atrás
        </button>
        <button 
          onClick={() => preview && onDataLoaded({ headers: preview.headers, rows: preview.preview_rows })} 
          disabled={status !== 'success'} 
          className="px-8 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-800/50 disabled:text-gray-600 disabled:cursor-not-allowed rounded-xl text-sm font-bold transition-all shadow-lg shadow-indigo-600/20"
        >
          Continuar al Mapeo
        </button>
      </div>
    </div>
  );
}
