'use client';

import React from 'react';
import { Check } from 'lucide-react';
import { useIngestionWizard } from './hooks/useIngestionWizard';

// Imports de los pasos (se crearán después)
import StepSourceSelector from './steps/StepSourceSelector';
import StepFileUpload from './steps/StepFileUpload';
import StepColumnMapper from './steps/StepColumnMapper';
import StepSyncConfig from './steps/StepSyncConfig';
import StepProcessing from './steps/StepProcessing';
import StepValidation from './steps/StepValidation';

const STEPS = [
  { id: 1, title: 'Fuente' },
  { id: 2, title: 'Carga' },
  { id: 3, title: 'Mapeo' },
  { id: 4, title: 'Sincronización' },
  { id: 5, title: 'Procesamiento' },
  { id: 6, title: 'Validación' }
];

export default function WizardContainer({ tenantId }: { tenantId: string }) {
  const wizard = useIngestionWizard(tenantId);
  const { currentStep, prevStep, nextStep, startIngestion, progress } = wizard;

  const isProcessing = currentStep === 5;
  const isValidation = currentStep === 6;

  const renderStep = () => {
    switch (currentStep) {
      case 1: return <StepSourceSelector wizard={wizard} />;
      case 2: return <StepFileUpload wizard={wizard} />;
      case 3: return <StepColumnMapper wizard={wizard} />;
      case 4: return <StepSyncConfig wizard={wizard} />;
      case 5: return <StepProcessing wizard={wizard} />;
      case 6: return <StepValidation wizard={wizard} tenantId={tenantId} />;
      default: return null;
    }
  };

  const handleNext = () => {
    if (currentStep === 4) {
      startIngestion();
    } else {
      nextStep();
    }
  };

  return (
    <div className="w-full max-w-[768px] mx-auto bg-surface sm:rounded-[var(--radius-wizard)] p-6 sm:p-8 sm:border border-border shadow-lg">
      
      {/* Header & Step Indicator */}
      <div className="mb-8">
        <h2 className="text-2xl font-semibold text-foreground mb-6 text-center">
          Asistente de Centro de Datos
        </h2>
        
        <div className="flex items-center justify-between relative">
          {/* Línea conectora */}
          <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-border -z-10 -translate-y-1/2" />
          
          {STEPS.map((step, idx) => {
            const isActive = currentStep === step.id;
            const isCompleted = currentStep > step.id;
            
            return (
              <div key={step.id} className="flex flex-col items-center gap-2 bg-surface px-2">
                <div 
                  className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300
                    ${isActive ? 'bg-primary text-primary-foreground scale-110 shadow-md' : 
                      isCompleted ? 'bg-success text-primary-foreground' : 
                      'bg-surface-2 border border-border text-muted-foreground'}`}
                >
                  {isCompleted ? <Check size={20} /> : <span className="font-medium">{step.id}</span>}
                </div>
                {/* Opcional: title for larger screens */}
                <span className={`text-xs hidden sm:block ${isActive ? 'text-foreground font-medium' : 'text-muted-foreground'}`}>
                  {step.title}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="min-h-[400px] flex flex-col transition-all duration-150">
        {renderStep()}
      </div>

      {/* Footer / Navigation */}
      {(!isProcessing && !isValidation) && (
        <div className="mt-8 pt-6 border-t border-border flex justify-between items-center">
          <div className="flex gap-4">
            {currentStep > 1 && (
              <button
                onClick={wizard.resetWizard}
                className="px-4 py-2 rounded-md font-medium text-error hover:bg-error/10 transition-colors"
              >
                Reiniciar
              </button>
            )}
            <button
              onClick={prevStep}
              disabled={currentStep === 1}
              className="px-4 py-2 rounded-md font-medium text-muted-foreground hover:bg-surface-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Atrás
            </button>
          </div>
          
          <button
            onClick={handleNext}
            className="px-6 py-2 rounded-md font-medium bg-primary text-primary-foreground hover:bg-primary-hover shadow-sm transition-colors"
          >
            {currentStep === 4 ? 'Iniciar Ingesta' : 'Siguiente'}
          </button>
        </div>
      )}
      
      {/* Footer Validation Step */}
      {isValidation && (
        <div className="mt-8 pt-6 border-t border-border flex justify-end">
          <button
            onClick={() => {
              localStorage.setItem('flux_phase_3', 'true');
              window.dispatchEvent(new Event('storage'));
              window.location.href = '/dashboard/data-ingestion';
            }}
            className="px-6 py-2 rounded-md font-medium bg-primary text-primary-foreground hover:bg-primary-hover shadow-sm transition-colors"
          >
            Finalizar
          </button>
        </div>
      )}
    </div>
  );
}
