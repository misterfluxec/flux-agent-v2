import { OnboardingData } from '@/hooks/useOnboardingWizard';
import { Button } from '@/components/ui/button';
import { Shield, Utensils, ShoppingCart, Activity, Briefcase, Car, Hammer, Shirt, Laptop, GraduationCap } from 'lucide-react';

interface Props {
  data: OnboardingData;
  onChange: (field: keyof OnboardingData, value: any) => void;
  onNext: () => void;
  onBack: () => void;
}

const INDUSTRIES = [
  { id: 'seguridad', label: 'Seguridad', icon: Shield },
  { id: 'restaurante', label: 'Restaurante', icon: Utensils },
  { id: 'ecommerce', label: 'Ecommerce', icon: ShoppingCart },
  { id: 'clinica', label: 'Clínica', icon: Activity },
  { id: 'inmobiliaria', label: 'Inmobiliaria', icon: Briefcase },
  { id: 'automotriz', label: 'Automotriz', icon: Car },
  { id: 'ferreteria', label: 'Ferretería', icon: Hammer },
  { id: 'retail', label: 'Retail', icon: Shirt },
  { id: 'tecnologia', label: 'Tecnología', icon: Laptop },
  { id: 'educacion', label: 'Educación', icon: GraduationCap },
];

export function StepIndustry({ data, onChange, onNext, onBack }: Props) {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold text-foreground">Selecciona tu Industria</h2>
        <p className="text-muted-foreground">Configuraremos la IA de Yanua automáticamente según tu negocio.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-8">
        {INDUSTRIES.map((ind) => {
          const Icon = ind.icon;
          const isSelected = data.industria === ind.id;
          return (
            <button
              key={ind.id}
              onClick={() => onChange('industria', ind.id)}
              className={`p-4 rounded-xl border flex flex-col items-center justify-center gap-3 transition-all ${
                isSelected
                  ? 'border-primary bg-primary/10 shadow-[0_0_20px_rgba(6,182,212,0.2)]'
                  : 'border-border bg-card hover:border-white/20 hover:bg-white/5'
              }`}
            >
              <Icon className={`w-8 h-8 ${isSelected ? 'text-primary' : 'text-muted-foreground'}`} />
              <span className={`text-sm font-medium ${isSelected ? 'text-primary' : 'text-foreground'}`}>
                {ind.label}
              </span>
            </button>
          );
        })}
      </div>

      <div className="flex justify-between pt-8">
        <Button variant="outline" onClick={onBack}>
          Atrás
        </Button>
        <Button 
          onClick={onNext} 
          disabled={!data.industria}
          className="bg-primary text-primary-foreground hover:bg-primary-hover shadow-[0_0_20px_rgba(6,182,212,0.3)]"
        >
          Siguiente
        </Button>
      </div>
    </div>
  );
}
