import { User, Image as ImageIcon } from 'lucide-react';
import { OnboardingData } from '@/hooks/useOnboardingWizard';
import { Button } from '@/components/ui/button';

interface Props {
  data: OnboardingData;
  onChange: (field: keyof OnboardingData, value: string) => void;
  onNext: () => void;
}

export function StepIdentity({ data, onChange, onNext }: Props) {
  const isValid = data.nombre.trim().length >= 2;

  return (
    <div className="space-y-6 animate-in slide-in-from-bottom-4 fade-in duration-500">
      <div className="text-center space-y-2">
        <div className="inline-flex p-3 bg-primary/10 rounded-full mb-2 border border-primary/20 shadow-[0_0_15px_rgba(6,182,212,0.2)]">
          <User className="w-6 h-6 text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-foreground">Identidad del Asistente</h2>
        <p className="text-muted-foreground">Dale un nombre y un rostro a tu nuevo compañero de equipo.</p>
      </div>
      <div className="space-y-6 max-w-md mx-auto mt-8">
        <div>
          <label className="block text-sm font-medium mb-2 text-foreground">Nombre del Asistente</label>
          <input
            type="text"
            value={data.nombre}
            onChange={(e) => onChange('nombre', e.target.value)}
            placeholder="Ej: Yanua, Alex, Sofia..."
            className="w-full px-4 py-3 bg-background border border-border rounded-lg focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none transition text-foreground"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-3 text-foreground">Avatar (Opcional)</label>
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-card border border-border flex items-center justify-center overflow-hidden">
              {data.avatar ? (
                <img src={data.avatar} alt="Avatar" className="w-full h-full object-cover" />
              ) : (
                <User className="w-8 h-8 text-muted-foreground" />
              )}
            </div>
            <Button variant="outline" className="border-border hover:bg-white/5 gap-2">
              <ImageIcon className="w-4 h-4" />
              Subir Foto
            </Button>
          </div>
        </div>
      </div>
      <div className="flex justify-end pt-8 max-w-md mx-auto">
        <Button 
          onClick={onNext} 
          disabled={!isValid} 
          className="bg-primary text-primary-foreground hover:bg-primary-hover shadow-[0_0_20px_rgba(6,182,212,0.3)] w-full"
        >
          Siguiente
        </Button>
      </div>
    </div>
  );
}
