import React, { useState } from 'react';
import { X, Check, FileSpreadsheet, ArrowRight, Wand2 } from 'lucide-react';

interface MappingWizardPreviewProps {
  onClose: () => void;
}

export function MappingWizardPreview({ onClose }: MappingWizardPreviewProps) {
  const [step, setStep] = useState(1);
  const [isAutoMapping, setIsAutoMapping] = useState(false);

  const handleAutoMap = () => {
    setIsAutoMapping(true);
    setTimeout(() => {
      setIsAutoMapping(false);
      setStep(2);
    }, 1500);
  };

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      
      <div className="w-[90%] max-w-3xl bg-slate-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/5">
          <div>
            <h2 className="text-xl font-bold text-slate-100">Configurar Conector</h2>
            <p className="text-sm text-slate-400 mt-1">Conecta y mapea los datos de tu Google Sheet.</p>
          </div>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-white/5 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          
          {step === 1 && (
            <div className="space-y-6">
              <div className="p-4 rounded-xl border border-dashed border-white/20 bg-slate-950/50 flex flex-col items-center justify-center text-center h-48">
                <FileSpreadsheet className="w-10 h-10 text-emerald-500 mb-3" />
                <h3 className="font-medium text-slate-200">https://docs.google.com/spreadsheets/...</h3>
                <p className="text-xs text-slate-500 mt-2">Hoja "Inventario" cargada exitosamente.</p>
              </div>

              <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-xl p-4 flex items-start gap-4">
                <Wand2 className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-semibold text-indigo-300">Auto Mapping Inteligente</h4>
                  <p className="text-xs text-indigo-200/70 mt-1">
                    Detectamos 8 columnas en tu archivo. FluxAgent puede intentar emparejarlas automáticamente con nuestro model canónico.
                  </p>
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-slate-300 mb-4">Revisa el mapeo de columnas</h3>
              
              <div className="grid grid-cols-[1fr_auto_1fr] gap-4 items-center">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider text-center">Columna Original (Excel)</div>
                <div className="w-6"></div>
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider text-center">Campo FluxAgent</div>
                
                {/* Mapping Row 1 */}
                <div className="p-3 rounded bg-slate-800 border border-white/5 text-sm font-medium text-slate-300 text-center">Codigo</div>
                <ArrowRight className="w-4 h-4 text-slate-500" />
                <div className="p-3 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium text-center">sku</div>

                {/* Mapping Row 2 */}
                <div className="p-3 rounded bg-slate-800 border border-white/5 text-sm font-medium text-slate-300 text-center">Nombre_Prod</div>
                <ArrowRight className="w-4 h-4 text-slate-500" />
                <div className="p-3 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium text-center">name</div>

                {/* Mapping Row 3 */}
                <div className="p-3 rounded bg-slate-800 border border-white/5 text-sm font-medium text-slate-300 text-center">Precio_Final</div>
                <ArrowRight className="w-4 h-4 text-slate-500" />
                <div className="p-3 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium text-center">price</div>

              </div>
              
              <div className="mt-8 p-4 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <p className="text-xs text-amber-400 font-medium flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                  La columna "Notas_Internas" fue ignorada.
                </p>
              </div>

            </div>
          )}
          
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-white/5 bg-slate-900/50 flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors">
            Cancelar
          </button>
          
          {step === 1 ? (
            <button 
              onClick={handleAutoMap}
              disabled={isAutoMapping}
              className="flex items-center gap-2 bg-indigo-500 hover:bg-indigo-400 text-white px-5 py-2 rounded-lg font-medium transition-colors"
            >
              {isAutoMapping ? 'Mapeando...' : 'Auto-Mapear Columnas'}
            </button>
          ) : (
            <button 
              onClick={onClose}
              className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white px-5 py-2 rounded-lg font-medium transition-colors"
            >
              <Check className="w-4 h-4" />
              Confirmar & Iniciar Sync
            </button>
          )}
        </div>

      </div>
    </div>
  );
}
