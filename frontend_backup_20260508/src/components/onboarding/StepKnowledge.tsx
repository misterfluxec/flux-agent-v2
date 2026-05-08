import { UploadCloud, CheckCircle2, ArrowLeft, Sparkles, FolderSync, Cloud, Database } from 'lucide-react';
import { OnboardingData } from '@/hooks/useOnboardingWizard';
import { Button } from '@/components/ui/button';

interface Props {
  data: OnboardingData;
  onChange: (field: keyof OnboardingData, value: any) => void;
  onNext: () => void;
  onBack: () => void;
}

export function StepKnowledge({ data, onChange, onNext, onBack }: Props) {
  const isLoaded = data.conocimiento_cargado;

  const handleSimulateUpload = () => {
    setTimeout(() => {
      onChange('conocimiento_cargado', true);
    }, 1500);
  };

  return (
    <div className="relative space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 py-4">
      <div className="text-center space-y-1">
        <h2 className="text-xl md:text-2xl font-bold text-foreground">
          Conocimiento del <span className="text-primary">Agente</span>
        </h2>
        <p className="text-muted-foreground text-xs max-w-sm mx-auto">
          Sube tus archivos o conecta tus nubes para que Yanua aprenda sobre tu negocio.
        </p>
      </div>

      <div className="max-w-xl mx-auto space-y-8">
        {!isLoaded ? (
          <>
            <div 
              className="border border-dashed border-white/20 rounded-2xl p-10 text-center hover:bg-white/[0.04] hover:border-primary/30 transition-all cursor-pointer group"
              onClick={handleSimulateUpload}
            >
              <div className="inline-flex p-3 bg-white/[0.03] rounded-full mb-3 border border-white/10 group-hover:border-primary/20 transition-all">
                <UploadCloud className="w-6 h-6 text-muted-foreground/60 group-hover:text-primary transition-all" strokeWidth={1.5} />
              </div>
              <h3 className="text-sm font-bold text-foreground/90 mb-1">Arrastra tus archivos aquí</h3>
              <p className="text-[10px] text-muted-foreground/60 mb-4 uppercase tracking-widest">PDF, CSV, XLS, DOCS</p>
              <Button variant="ghost" className="h-8 px-4 text-[10px] font-bold uppercase tracking-widest text-primary hover:text-primary hover:bg-primary/5">Explorar archivos</Button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {[
                { name: 'Google Drive', icon: FolderSync, color: 'text-green-400', bg: 'bg-green-400/10' },
                { name: 'OneDrive', icon: Cloud, color: 'text-blue-400', bg: 'bg-blue-400/10' },
                { name: 'MEGA', icon: Database, color: 'text-red-500', bg: 'bg-red-500/10' },
              ].map((cloud) => (
                <button 
                  key={cloud.name}
                  className="h-14 flex items-center justify-center gap-3 rounded-xl border border-white/10 bg-white/[0.03] hover:border-white/20 hover:bg-white/5 transition-all outline-none group"
                  onClick={handleSimulateUpload}
                >
                  <div className={`w-8 h-8 flex items-center justify-center rounded-md shrink-0 transition-colors ${cloud.bg}`}>
                    <cloud.icon className={`w-5 h-5 ${cloud.color}`} strokeWidth={1.5} />
                  </div>
                  <span className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground/70 group-hover:text-primary transition-colors">{cloud.name}</span>
                </button>
              ))}
            </div>
          </>
        ) : (
          <div className="border border-white/10 rounded-2xl p-10 text-center bg-primary/10 relative overflow-hidden group">
            <div className="absolute -top-10 -right-10 w-32 h-32 bg-primary/20 rounded-full blur-3xl" />
            <div className="inline-flex p-3 bg-primary/20 rounded-full mb-3">
              <CheckCircle2 className="w-8 h-8 text-primary" strokeWidth={1.5} />
            </div>
            <h3 className="text-lg font-bold text-foreground mb-1 tracking-tight">¡Conocimiento Procesado!</h3>
            <p className="text-xs text-muted-foreground/80 max-w-xs mx-auto">Yanua ha aprendido 312 productos y servicios de tus documentos.</p>
            <button 
              onClick={() => onChange('conocimiento_cargado', false)}
              className="mt-6 text-[10px] font-bold uppercase tracking-widest text-primary hover:text-primary transition-colors"
            >
              Cambiar documentos
            </button>
          </div>
        )}
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
          variant="outline"
          className="h-11 px-10 border-primary/40 text-primary hover:bg-primary/10 rounded-full text-xs font-black uppercase tracking-[0.2em] transition-all active:scale-[0.98] disabled:opacity-20 shadow-[0_0_20px_rgba(6,182,212,0.1)]"
        >
          {isLoaded ? "Siguiente Paso ➔" : "Omitir Paso ➔"}
        </Button>
      </div>
    </div>
  );
}
