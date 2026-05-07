import { QrCode, Smartphone, CheckCircle2 } from 'lucide-react';
import { OnboardingData } from '@/hooks/useOnboardingWizard';
import { Button } from '@/components/ui/button';

interface Props {
  data: OnboardingData;
  onChange: (field: keyof OnboardingData, value: any) => void;
  onNext: () => void;
  onBack: () => void;
}

export function StepConnect({ data, onChange, onNext, onBack }: Props) {
  const isConnected = data.whatsapp_conectado;

  const handleSimulateConnection = () => {
    setTimeout(() => {
      onChange('whatsapp_conectado', true);
    }, 2000);
  };

  return (
    <div className="space-y-6 animate-in slide-in-from-bottom-4 fade-in duration-500">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold text-foreground">Conectar WhatsApp</h2>
        <p className="text-muted-foreground">Escanea el código QR para dar vida a tu agente en WhatsApp.</p>
      </div>

      <div className="max-w-md mx-auto mt-8">
        {!isConnected ? (
          <div className="border border-border bg-card rounded-2xl p-8 text-center shadow-lg relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-primary animate-pulse" />
            <div 
              className="w-48 h-48 mx-auto bg-white rounded-xl flex items-center justify-center p-2 mb-6 cursor-pointer shadow-inner"
              onClick={handleSimulateConnection}
            >
              <QrCode className="w-40 h-40 text-black" strokeWidth={1} />
            </div>
            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground mb-2">
              <Smartphone className="w-4 h-4" />
              <span>Abre WhatsApp en tu teléfono</span>
            </div>
            <p className="text-xs text-muted-foreground">Ve a Configuración {'>'} Dispositivos Vinculados {'>'} Vincular dispositivo</p>
          </div>
        ) : (
          <div className="border border-border rounded-2xl p-8 text-center bg-card shadow-[0_0_30px_rgba(6,182,212,0.1)]">
            <div className="inline-flex p-4 bg-primary/10 rounded-full mb-4">
              <CheckCircle2 className="w-10 h-10 text-primary" />
            </div>
            <h3 className="text-xl font-bold text-foreground mb-2">¡WhatsApp Conectado!</h3>
            <p className="text-muted-foreground">Tu agente ya está listo para responder mensajes.</p>
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
          {isConnected ? "Siguiente" : "Omitir por ahora"}
        </Button>
      </div>
    </div>
  );
}
