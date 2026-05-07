import { Check } from 'lucide-react';
import { useTranslations } from 'next-intl';

export function WizardStepper({ currentStep }: { currentStep: number }) {
  const steps = [
    { num: 1, label: 'Identidad' },
    { num: 2, label: 'Industria' },
    { num: 3, label: 'Conocimiento' },
    { num: 4, label: 'Canales' },
    { num: 5, label: 'Activación' },
  ];

  return (
    <div className="mb-8 px-2">
      <div className="flex items-center justify-between relative">
        <div className="absolute top-1/2 left-0 w-full h-1 bg-muted -translate-y-1/2 rounded-full" />
        <div
          className="absolute top-1/2 left-0 h-1 bg-primary -translate-y-1/2 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }}
        />
        {steps.map((s) => (
          <div key={s.num} className="relative z-10 flex flex-col items-center">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${
                s.num < currentStep
                  ? 'bg-primary border-primary text-primary-foreground shadow-lg shadow-primary/20'
                  : s.num === currentStep
                  ? 'bg-background border-primary text-primary scale-110 shadow-md'
                  : 'bg-background border-muted text-muted-foreground'
              }`}
            >
              {s.num < currentStep ? <Check className="w-5 h-5" /> : <span className="text-sm font-bold">{s.num}</span>}
            </div>
            <span className={`mt-2 text-[10px] sm:text-xs font-medium hidden sm:block transition-colors ${
              s.num <= currentStep ? 'text-foreground' : 'text-muted-foreground'
            }`}>
              {s.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
