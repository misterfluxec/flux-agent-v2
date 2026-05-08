import { Check } from 'lucide-react';

export function WizardStepper({ currentStep }: { currentStep: number }) {
  const steps = [
    { num: 1, label: 'Identidad' },
    { num: 2, label: 'Industria' },
    { num: 3, label: 'Conocimiento' },
    { num: 4, label: 'Canales' },
    { num: 5, label: 'Activación' },
  ];

  return (
    <div className="mb-12 px-4">
      <div className="flex items-center justify-between relative max-w-2xl mx-auto">
        {/* Track Line */}
        <div className="absolute top-1/2 left-0 w-full h-[1px] bg-white/10 -translate-y-1/2" />
        
        {/* Progress Line */}
        <div
          className="absolute top-1/2 left-0 h-[1px] bg-primary -translate-y-1/2 transition-all duration-700 ease-in-out shadow-[0_0_8px_rgba(6,182,212,0.5)]"
          style={{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }}
        />

        {steps.map((s) => (
          <div key={s.num} className="relative z-10 flex flex-col items-center">
            {/* Subtle pulsing aura for the active step */}
            {s.num === currentStep && (
              <div className="absolute inset-0 m-auto w-7 h-7 sm:w-8 sm:h-8 rounded-full border border-primary/40 bg-primary/20 scale-[1.3] animate-pulse blur-[1px]" />
            )}
            
            <div
              className={`relative z-10 w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center border transition-all duration-500 ${
                s.num < currentStep
                  ? 'bg-primary border-primary text-white'
                  : s.num === currentStep
                  ? 'bg-[#0A0A0B] border-primary text-primary scale-110 shadow-[0_0_15px_rgba(6,182,212,0.2)]'
                  : 'bg-[#0A0A0B] border-white/10 text-white/20'
              }`}
            >
              {s.num < currentStep ? (
                <Check className="w-3.5 h-3.5 sm:w-4 sm:h-4" strokeWidth={3} />
              ) : (
                <span className="text-[10px] sm:text-xs font-black">{s.num}</span>
              )}
            </div>
            
            <div className="absolute -bottom-6 w-max">
              <span className={`text-[9px] font-bold uppercase tracking-widest transition-all duration-300 ${
                s.num === currentStep ? 'text-primary opacity-100 translate-y-0' : 'text-white/20 opacity-40 translate-y-1'
              }`}>
                {s.label}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
