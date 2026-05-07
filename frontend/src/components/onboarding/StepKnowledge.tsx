import { UploadCloud, CheckCircle2 } from 'lucide-react';
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
    // Simulamos la carga visual para UX
    setTimeout(() => {
      onChange('conocimiento_cargado', true);
    }, 1500);
  };

  return (
    <div className="space-y-6 animate-in slide-in-from-bottom-4 fade-in duration-500">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold text-foreground">Conocimiento del Agente</h2>
        <p className="text-muted-foreground">Sube documentos para que Yanua aprenda todo sobre tu negocio.</p>
      </div>

      <div className="max-w-xl mx-auto mt-8">
        {!isLoaded ? (
          <div 
            className="border-2 border-dashed border-border rounded-2xl p-12 text-center hover:bg-white/5 hover:border-primary/50 transition cursor-pointer"
            onClick={handleSimulateUpload}
          >
            <div className="inline-flex p-4 bg-background rounded-full mb-4 shadow-sm border border-border">
              <UploadCloud className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">Arrastra tus archivos aquí</h3>
            <p className="text-sm text-muted-foreground mb-6">Soporta PDF, TXT, CSV, XLS y Docs</p>
            <Button variant="secondary" className="pointer-events-none">Explorar archivos</Button>
          </div>
        ) : (
          <div className="border border-border rounded-2xl p-8 text-center bg-card shadow-[0_0_30px_rgba(6,182,212,0.1)]">
            <div className="inline-flex p-4 bg-primary/10 rounded-full mb-4">
              <CheckCircle2 className="w-10 h-10 text-primary" />
            </div>
            <h3 className="text-xl font-bold text-foreground mb-2">¡Conocimiento Procesado!</h3>
            <p className="text-muted-foreground">Yanua ha aprendido 312 productos y servicios de tus documentos.</p>
            <Button 
              variant="outline" 
              onClick={() => onChange('conocimiento_cargado', false)}
              className="mt-6 border-border text-xs"
            >
              Subir más archivos
            </Button>
          </div>
        )}
      </div>

      <div className="flex justify-between pt-8">
        <Button variant="outline" onClick={onBack}>
          Atrás
        </Button>
        <Button 
          onClick={onNext} 
          className="bg-primary text-primary-foreground hover:bg-primary-hover shadow-[0_0_20px_rgba(6,182,212,0.3)]"
        >
          {isLoaded ? "Siguiente" : "Omitir por ahora"}
        </Button>
      </div>
    </div>
  );
}
