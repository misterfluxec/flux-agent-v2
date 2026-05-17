import { Bot, Camera, Sparkles, User, UserCircle2, Smile, SmilePlus } from 'lucide-react';
import { OnboardingData } from '@/hooks/useOnboardingWizard';
import { Button } from '@/components/ui/button';

interface Props {
  data: OnboardingData;
  onChange: (field: keyof OnboardingData, value: string) => void;
  onNext: () => void;
}

const PREDEFINED_AVATARS = [
  { 
    id: 'man', 
    label: 'Él', 
    icon: Smile, 
    gradient: 'from-blue-500/10 to-blue-500/5',
    color: 'text-blue-500',
  },
  { 
    id: 'woman', 
    label: 'Ella', 
    icon: SmilePlus, 
    gradient: 'from-pink-500/10 to-pink-500/5',
    color: 'text-pink-500',
  },
  { 
    id: 'agent', 
    label: 'Agente', 
    icon: Bot, 
    gradient: 'from-cyan-500/10 to-cyan-500/5',
    color: 'text-cyan-500',
  },
];

export function StepIdentity({ data, onChange, onNext }: Props) {
  const isValid = data.name.trim().length >= 2;

  return (
    <div className="relative space-y-8 animate-in slide-in-from-bottom-4 fade-in duration-500 flex flex-col justify-center py-4">
      <div className="text-center space-y-1 relative z-10">
        <h2 className="text-xl md:text-2xl font-bold text-foreground">
          Identidad del <span className="text-primary">Asistente</span>
        </h2>
        <p className="text-muted-foreground text-xs">
          Personaliza la esencia de tu nuevo colaborador digital.
        </p>
      </div>

      <div className="max-w-xl mx-auto w-full space-y-10 relative z-10">
        {/* Subtle Avatar Selection */}
        <div className="flex flex-wrap justify-center items-center gap-8 md:gap-12">
          {PREDEFINED_AVATARS.map((av) => {
            const Icon = av.icon;
            const isSelected = data.avatar === av.id;
            return (
              <button
                key={av.id}
                onClick={() => onChange('avatar', av.id)}
                className="flex flex-col items-center group outline-none"
              >
                <div className={`relative transition-all duration-500 ${
                  isSelected ? 'scale-110' : 'opacity-40 hover:opacity-100'
                }`}>
                  <div className={`w-16 h-16 md:w-20 md:h-20 rounded-full border flex items-center justify-center transition-all duration-300 ${
                    isSelected 
                      ? `border-primary/50 bg-gradient-to-br ${av.gradient} shadow-lg shadow-primary/5` 
                      : 'border-border bg-white/2 hover:border-white/20'
                  }`}>
                    <Icon className={`w-8 h-8 md:w-10 md:h-10 transition-all ${isSelected ? av.color : 'text-muted-foreground'}`} strokeWidth={1.5} />
                  </div>
                  {isSelected && (
                    <div className="absolute -top-1 -right-1 bg-primary rounded-full p-1 shadow-sm z-20">
                      <Sparkles className="w-3 h-3 text-white" />
                    </div>
                  )}
                </div>
                <span className={`mt-3 text-[10px] font-bold uppercase tracking-widest transition-all ${
                  isSelected ? 'text-primary' : 'text-muted-foreground/70'
                }`}>
                  {av.label}
                </span>
              </button>
            );
          })}
          
          <button className="flex flex-col items-center group outline-none">
            <div className="w-16 h-16 md:w-20 md:h-20 rounded-full border border-dashed border-white/20 flex items-center justify-center text-muted-foreground/50 hover:border-primary/50 hover:text-primary transition-all">
              <Camera className="w-6 h-6" strokeWidth={1.5} />
            </div>
            <span className="mt-3 text-[9px] font-bold text-muted-foreground/50 uppercase tracking-widest">Subir</span>
          </button>
        </div>

        {/* Restored Input Style */}
        <div className="max-w-sm mx-auto space-y-6 pt-4">
          <div className="relative group">
            <label className="absolute -top-2 left-4 px-2 bg-[#0A0A0B] text-[10px] font-bold text-primary uppercase tracking-widest z-10">
              Nombre de Identidad
            </label>
            <input
              type="text"
              value={data.name}
              onChange={(e) => onChange('name', e.target.value)}
              placeholder="Ej: Yanua, Alex, Sofia..."
              className="w-full px-5 py-3.5 bg-white/[0.03] border border-white/10 rounded-xl focus:border-primary/50 outline-none transition-all text-foreground text-sm font-medium placeholder:text-muted-foreground/40"
            />
          </div>

          <div className="flex justify-center">
            <Button 
              onClick={onNext} 
              disabled={!isValid || !data.avatar} 
              variant="outline"
              className="h-11 px-10 border-primary/40 text-primary hover:bg-primary/10 rounded-full text-xs font-black uppercase tracking-[0.2em] transition-all active:scale-[0.98] disabled:opacity-20 shadow-[0_0_20px_rgba(6,182,212,0.1)]"
            >
              Continuar ➔
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
