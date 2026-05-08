import { OnboardingData } from '@/hooks/useOnboardingWizard';
import { Button } from '@/components/ui/button';
import { Shield, Utensils, ShoppingCart, Activity, Briefcase, Car, Hammer, Shirt, Laptop, GraduationCap, ArrowLeft, Sparkles, ShoppingBag } from 'lucide-react';

interface Props {
  data: OnboardingData;
  onChange: (field: keyof OnboardingData, value: any) => void;
  onNext: () => void;
  onBack: () => void;
}

const INDUSTRIES = [
  { id: 'seguridad', label: 'Seguridad', icon: Shield },
  { id: 'restaurante', label: 'Restaurante', icon: Utensils },
  { id: 'ecommerce', label: 'Ecommerce', icon: ShoppingBag },
  { id: 'clinica', label: 'Clínica', icon: Activity },
  { id: 'servicios', label: 'Servicios', icon: Briefcase },
  { id: 'automotriz', label: 'Automotriz', icon: Car },
  { id: 'ferreteria', label: 'Ferretería', icon: Hammer },
  { id: 'retail', label: 'Retail', icon: Shirt },
  { id: 'tecnologia', label: 'Tecnología', icon: Laptop },
  { id: 'custom', label: 'Custom', icon: GraduationCap },
];

export function StepIndustry({ data, onChange, onNext, onBack }: Props) {
  return (
    <div className="relative space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 py-4">
      <div className="text-center space-y-1">
        <h2 className="text-xl md:text-2xl font-bold text-foreground">
          Selecciona tu <span className="text-primary">Industria</span>
        </h2>
        <p className="text-muted-foreground text-xs max-w-sm mx-auto">
          Configuraremos la IA de Yanua automáticamente según tu modelo de negocio.
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 mt-8">
        {INDUSTRIES.map((ind) => {
          const Icon = ind.icon;
          const isSelected = data.industria === ind.id;
          return (
            <button
              key={ind.id}
              onClick={() => onChange('industria', ind.id)}
              className={`group relative p-5 rounded-2xl border transition-all duration-300 flex flex-col items-center justify-center gap-3 ${
                isSelected
                  ? 'border-primary/40 bg-primary/5 shadow-lg shadow-primary/5'
                  : 'border-white/5 bg-white/[0.02] hover:border-white/20 hover:bg-white/5'
              }`}
            >
              <div className={`p-2 rounded-full transition-colors ${isSelected ? 'bg-primary/20' : 'bg-transparent'}`}>
                <Icon className={`w-6 h-6 transition-all duration-300 ${isSelected ? 'text-primary scale-110' : 'text-muted-foreground/80 group-hover:text-muted-foreground'}`} strokeWidth={1.5} />
              </div>
              <span className={`text-[11px] font-bold uppercase tracking-wider transition-colors ${isSelected ? 'text-primary' : 'text-muted-foreground/70'}`}>
                {ind.label}
              </span>

              {isSelected && (
                <div className="absolute top-2 right-2 animate-in zoom-in duration-300">
                  <Sparkles className="w-3 h-3 text-primary/70" />
                </div>
              )}
            </button>
          );
        })}
      </div>

      <div className="flex justify-between items-center pt-8">
        <button 
          onClick={onBack}
          className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground/70 hover:text-primary transition-colors outline-none"
        >
          <ArrowLeft className="w-3 h-3" />
          Volver
        </button>
        
        <Button 
          onClick={onNext} 
          disabled={!data.industria}
          variant="outline"
          className="h-11 px-10 border-primary/40 text-primary hover:bg-primary/10 rounded-full text-xs font-black uppercase tracking-[0.2em] transition-all active:scale-[0.98] disabled:opacity-20 shadow-[0_0_20px_rgba(6,182,212,0.1)]"
        >
          Siguiente Paso ➔
        </Button>
      </div>
    </div>
  );
}
