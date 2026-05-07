import { Rocket, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
  isLoading: boolean;
  onSubmit: () => void;
  onBack: () => void;
}

export function StepComplete({ isLoading, onSubmit, onBack }: Props) {
  return (
    <div className="space-y-6 animate-in slide-in-from-bottom-4 fade-in duration-500 text-center">
      <div className="inline-flex p-6 bg-primary/10 rounded-full mb-4 shadow-[0_0_50px_rgba(6,182,212,0.2)]">
        <Rocket className="w-16 h-16 text-primary" />
      </div>
      
      <div className="space-y-2">
        <h2 className="text-3xl font-bold text-foreground">¡Todo Listo!</h2>
        <p className="text-muted-foreground text-lg max-w-md mx-auto">
          Tu sistema comercial IA está operativo y configurado según tu industria.
        </p>
      </div>

      <div className="pt-8 flex flex-col sm:flex-row items-center justify-center gap-4 max-w-sm mx-auto">
        <Button variant="outline" onClick={onBack} disabled={isLoading} className="w-full">
          Revisar Configuración
        </Button>
        <Button 
          onClick={onSubmit} 
          disabled={isLoading}
          className="w-full bg-primary text-primary-foreground hover:bg-primary-hover shadow-[0_0_20px_rgba(6,182,212,0.3)] text-lg h-12"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              Iniciando...
            </>
          ) : (
            "Ir al Dashboard 🚀"
          )}
        </Button>
      </div>
    </div>
  );
}
