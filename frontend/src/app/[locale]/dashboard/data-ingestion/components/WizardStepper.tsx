import { Check, Loader2 } from 'lucide-react';

const STEPS = [
  { id: 1, label: 'Fuente' },
  { id: 2, label: 'Carga' },
  { id: 3, label: 'Mapeo' },
  { id: 4, label: 'Sincronización' },
  { id: 5, label: 'Procesamiento' },
  { id: 6, label: 'Validación' }
];

export function WizardStepper({ currentStep, isProcessing }: { currentStep: number; isProcessing: boolean }) {
  return (
    <div className="flex items-center justify-between mb-10 relative px-4">
      {/* Background Line */}
      <div className="absolute top-1/2 left-4 right-4 h-[2px] bg-gray-800/60 -z-10 transform -translate-y-1/2 rounded-full" />
      
      {/* Progress Line */}
      <div 
        className="absolute top-1/2 left-4 h-[2px] bg-gradient-to-r from-indigo-500 to-purple-500 -z-10 transform -translate-y-1/2 transition-all duration-700 ease-in-out shadow-[0_0_10px_rgba(99,102,241,0.5)]"
        style={{ width: `calc(${((currentStep - 1) / (STEPS.length - 1)) * 100}% - 2rem)` }}
      />
      
      {STEPS.map((step) => {
        const isActive = step.id === currentStep;
        const isCompleted = step.id < currentStep;
        
        return (
          <div key={step.id} className="flex flex-col items-center gap-3 bg-transparent relative">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center border-[3px] transition-all duration-500 backdrop-blur-md ${
              isCompleted 
                ? 'border-emerald-500 bg-emerald-500/20 text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.3)]' 
                : isActive 
                  ? 'border-indigo-500 bg-indigo-500/20 text-indigo-400 scale-110 shadow-[0_0_20px_rgba(99,102,241,0.4)]' 
                  : 'border-gray-800 bg-gray-900/80 text-gray-500'
            }`}>
              {isCompleted ? <Check className="w-5 h-5 stroke-[3]" /> :
               isActive && isProcessing ? <Loader2 className="w-5 h-5 animate-spin" /> :
               <span className="text-sm font-bold">{step.id}</span>}
            </div>
            <span className={`absolute -bottom-6 text-[10px] font-bold uppercase tracking-wider whitespace-nowrap transition-colors duration-300 ${
              isActive ? 'text-indigo-400' : isCompleted ? 'text-emerald-500' : 'text-gray-600'
            }`}>
              {step.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
