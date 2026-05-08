// @ts-nocheck
import { Check, AlertCircle } from 'lucide-react';

export function StepMapping({ headers, mapping, onMappingChange, onConfirm, onBack, isReady }: any) {
  const REQUIRED = ['nombre', 'precio'];
  const OPTIONAL = ['sku', 'stock', 'descripcion', 'categoria'];

  const autoDetect = (field: string) => {
    const lower = field.toLowerCase();
    if (['nombre', 'producto', 'item', 'name'].some(k => lower.includes(k))) return 'nombre';
    if (['precio', 'costo', 'valor', 'price'].some(k => lower.includes(k))) return 'precio';
    if (['stock', 'cantidad', 'disponible', 'qty'].some(k => lower.includes(k))) return 'stock';
    if (['sku', 'codigo', 'code'].some(k => lower.includes(k))) return 'sku';
    if (['desc', 'detalle', 'descripcion'].some(k => lower.includes(k))) return 'descripcion';
    if (['cat', 'categoria', 'category'].some(k => lower.includes(k))) return 'categoria';
    return null;
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">Mapeo de Columnas</h2>
          <p className="text-gray-400 text-sm mt-1">Asocia las columnas de tu fuente con los campos que el agente requiere aprender.</p>
        </div>
        {isReady && (
          <span className="flex items-center gap-1.5 text-emerald-400 text-sm font-semibold bg-emerald-500/10 border border-emerald-500/20 px-4 py-1.5 rounded-full shadow-[0_0_15px_rgba(16,185,129,0.15)]">
            <Check className="w-4 h-4" /> Listo para continuar
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {[...REQUIRED, ...OPTIONAL].map(field => {
          const detected = headers?.find((h: string) => autoDetect(h) === field);
          const isRequired = REQUIRED.includes(field);
          return (
            <div key={field} className="bg-black/40 backdrop-blur-md p-5 rounded-2xl border border-gray-800/60 hover:border-gray-600 transition-colors">
              <div className="flex items-center justify-between mb-3">
                <label className="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center gap-1.5">
                  {field} {isRequired && <AlertCircle className="w-3.5 h-3.5 text-rose-400" title="Campo Requerido" />}
                </label>
                {detected && !mapping[field] && (
                  <span className="text-[10px] uppercase font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 px-2 py-0.5 rounded-md">Sugerido</span>
                )}
              </div>
              <div className="relative group">
                <select
                  value={mapping[field] || ''}
                  onChange={(e) => onMappingChange(field, e.target.value)}
                  className="w-full bg-gray-900/50 border border-gray-700 rounded-xl p-3 text-sm text-gray-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all appearance-none cursor-pointer hover:bg-gray-800/50"
                >
                  <option value="" className="text-gray-500">Seleccionar columna...</option>
                  {headers?.map((h: string) => <option key={h} value={h}>{h}</option>)}
                </select>
                <div className="absolute inset-y-0 right-0 flex items-center px-3 pointer-events-none text-gray-500 group-hover:text-gray-300">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex justify-end gap-4 pt-6 border-t border-gray-800/50">
        <button 
          onClick={onBack} 
          className="px-6 py-2.5 text-sm font-medium text-gray-400 hover:text-white bg-transparent hover:bg-gray-800/50 rounded-xl transition-all"
        >
          Atrás
        </button>
        <button 
          onClick={onConfirm} 
          disabled={!isReady}
          className="px-8 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:from-gray-800 disabled:to-gray-800 disabled:text-gray-500 disabled:cursor-not-allowed rounded-xl text-sm font-bold text-white shadow-[0_0_15px_rgba(99,102,241,0.4)] hover:shadow-[0_0_25px_rgba(99,102,241,0.6)] disabled:shadow-none transition-all duration-300"
        >
          Confirmar y Continuar
        </button>
      </div>
    </div>
  );
}
