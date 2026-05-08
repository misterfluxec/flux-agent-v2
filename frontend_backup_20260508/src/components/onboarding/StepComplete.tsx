import { Rocket, Loader2, Sparkles, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
  isLoading: boolean;
  onSubmit: () => void;
  onBack: () => void;
}

export function StepComplete({ isLoading, onSubmit, onBack }: Props) {
  return (
    <div className="relative space-y-10 animate-in slide-in-from-bottom-4 fade-in duration-500 text-center py-6">
      <div className="relative inline-flex mb-4">
        <div className="absolute inset-0 bg-primary/20 rounded-full blur-3xl animate-pulse" />
        <div className="relative p-8 bg-primary/10 rounded-full border border-primary/20">
          <Rocket className="w-12 h-12 text-primary" strokeWidth={1.5} />
        </div>
        <div className="absolute -top-2 -right-2 bg-[#0A0A0B] border border-primary/20 rounded-full p-2">
          <Sparkles className="w-4 h-4 text-primary" />
        </div>
      </div>
      
      <div className="space-y-2">
        <h2 className="text-2xl md:text-3xl font-black text-foreground tracking-tight">¡Todo Listo!</h2>
        <p className="text-muted-foreground text-sm max-w-xs mx-auto">
          Tu instancia de <span className="text-primary font-bold">FluxAgent OS</span> está operativa y lista para escalar tu negocio.
        </p>
      </div>

      <div className="pt-6 flex flex-col items-center gap-6 max-w-sm mx-auto w-full">
        <Button 
          onClick={onSubmit} 
          disabled={isLoading}
          className="w-full h-14 bg-primary text-white shadow-xl shadow-primary/20 text-lg font-black rounded-2xl transition-all active:scale-[0.98] disabled:opacity-20 flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Sincronizando...
            </>
          ) : (
            <>
              Obtener Super Poderes 🚀
            </>
          )}
        </Button>

        <button 
          onClick={onBack}
          disabled={isLoading}
          className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground/50 hover:text-primary transition-colors outline-none disabled:opacity-0"
        >
          <ArrowLeft className="w-3 h-3" />
          Revisar Configuración
        </button>
      </div>
    </div>
  );
}
