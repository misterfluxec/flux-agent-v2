"use client";
import { DataHubMetrics } from './components/DataHubMetrics';
import { WizardStepper } from './components/WizardStepper';
import { StepSource } from './components/steps/StepSource';
import { StepConnection } from './components/steps/StepConnection';
import { StepMapping } from './components/steps/StepMapping';
import { StepSyncConfig } from './components/steps/StepSyncConfig';
import { StepProcessing } from './components/steps/StepProcessing';
import { StepValidation } from './components/steps/StepValidation';
import { useIngestionWizard } from './hooks/useIngestionWizard';
import { useEffect, useState } from 'react';
import { AlertCircle } from 'lucide-react';

export default function DataCenterPage() {
  const { state, updateState, nextStep, prevStep, fetchPreview, startSync, pollJobStatus, resetWizard } = useIngestionWizard();
  const [jobProgress, setJobProgress] = useState(0);

  // Polling automático cuando está procesando
  useEffect(() => {
    if (!state.jobId || !state.isProcessing) return;
    const interval = setInterval(async () => {
      const status = await pollJobStatus();
      if (!status) return;
      setJobProgress(status.progress_percent);
      if (status.status === 'success' || status.status === 'failed') {
        updateState({ isProcessing: false });
        if (status.status === 'success') nextStep();
        else updateState({ error: status.error_message || 'Error en procesamiento' });
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [state.jobId, state.isProcessing, pollJobStatus, updateState, nextStep]);

  const renderStep = () => {
    switch (state.step) {
      case 1: return <StepSource onSelect={(s) => { updateState({ sourceType: s }); nextStep(); }} />;
      case 2: return <StepConnection 
        sourceType={state.sourceType!} 
        onDataLoaded={(data) => { 
          updateState({ headers: data.headers, previewRows: data.rows }); 
          nextStep(); 
        }} 
        onBack={prevStep} 
      />;
      case 3: return <StepMapping 
        headers={state.headers} 
        mapping={state.mapping} 
        onMappingChange={(f: string, v: string) => updateState({ mapping: { ...state.mapping, [f]: v } })}
        isReady={['nombre', 'precio'].every(k => state.mapping[k])}
        onConfirm={nextStep} onBack={prevStep} />;
      case 4: return <StepSyncConfig config={state.syncConfig} onUpdate={(c: any) => updateState({ syncConfig: { ...state.syncConfig, ...c } })} onConfirm={startSync} onBack={prevStep} />;
      case 5: return <StepProcessing progress={jobProgress} status={state.isProcessing ? 'syncing' : (state.error ? 'failed' : 'idle')} onBack={prevStep} />;
      case 6: return <StepValidation onActivate={resetWizard} onBack={prevStep} />;
      default: return null;
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] p-6 md:p-8 animate-in fade-in duration-700 relative">
      {/* Premium Background Effects */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-[120px] pointer-events-none -z-10" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-[120px] pointer-events-none -z-10" />

      <div className="max-w-6xl mx-auto">
        <div className="mb-8 relative z-10">
          <h1 className="text-3xl md:text-4xl font-black tracking-tight text-white/90">
            <span className="text-primary">Centro</span> de Datos
          </h1>
          <p className="text-white/50 text-base mt-2 max-w-2xl font-light">
            Conecta, mapea y sincroniza tu inventario. El agente Flux aprenderá automáticamente de la fuente de datos seleccionada.
          </p>
        </div>

        <DataHubMetrics />

        <div className="bg-black/40 backdrop-blur-xl border border-white/5 rounded-[24px] p-6 md:p-10 shadow-xl relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent opacity-50" />
          
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-8">
              <WizardStepper currentStep={state.step} isProcessing={state.isProcessing} />
              {state.step > 1 && state.step < 6 && (
                <button 
                  onClick={resetWizard}
                  className="text-xs font-medium text-gray-500 hover:text-rose-400 transition-colors flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-800 hover:border-rose-500/30 hover:bg-rose-500/5"
                >
                  Reiniciar Proceso
                </button>
              )}
            </div>
            
            <div className="mt-4 min-h-[420px] transition-all duration-500">
              {state.error && (
                <div className="mb-8 p-5 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-rose-400 text-sm flex items-start gap-3 shadow-[0_0_15px_rgba(244,63,94,0.1)]">
                  <AlertCircle className="w-5 h-5 flex-shrink-0" />
                  <div>
                    <span className="font-bold block mb-1">Error de Sincronización:</span>
                    {state.error}
                  </div>
                </div>
              )}
              {renderStep()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
