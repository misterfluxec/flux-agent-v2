import { Bot, PauseCircle, Send, CheckCircle2, DollarSign, BrainCircuit, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface Props {
  conversation: any;
  onTakeover: () => void;
}

export function LeadIntelligence({ conversation, onTakeover }: Props) {
  if (!conversation) {
    return (
      <div className="w-80 border-l border-border bg-background p-6 flex flex-col items-center justify-center text-center">
        <BrainCircuit className="w-12 h-12 text-muted-foreground mb-4 opacity-50" />
        <h3 className="font-medium text-muted-foreground">Selecciona un lead para ver la inteligencia de Yanua</h3>
      </div>
    );
  }

  // Simular resumen de IA
  const isHumanNeeded = conversation.status === 'waiting' || conversation.status === 'new';

  return (
    <div className="w-80 border-l border-border bg-background flex flex-col h-full overflow-y-auto">
      <div className="p-4 border-b border-border bg-card">
        <h2 className="font-bold text-foreground flex items-center gap-2">
          <BrainCircuit className="w-4 h-4 text-primary" />
          Lead Intelligence
        </h2>
      </div>

      <div className="p-5 space-y-6">
        {/* Perfil del Lead */}
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center border border-primary/20">
            <User className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h3 className="font-bold text-foreground">{conversation.contactName || conversation.contactPhone}</h3>
            <p className="text-xs text-muted-foreground">WhatsApp Lead</p>
          </div>
        </div>

        {/* Resumen Yanua */}
        <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-2 opacity-20"><Bot className="w-16 h-16 text-primary" /></div>
          <div className="relative z-10">
            <h4 className="text-xs font-bold text-primary uppercase tracking-widest mb-2 flex items-center gap-1">
              <SparklesIcon /> Resumen Yanua
            </h4>
            <p className="text-sm text-foreground mb-3 leading-relaxed">
              El cliente está interesado en comprar {conversation.pipelineStage === 'negotiation' ? 'el plan premium' : 'productos generales'}. Ha hecho varias preguntas de soporte.
            </p>
            <div className="flex gap-2">
              <Badge variant="outline" className="bg-background/50 border-primary/20 text-primary">Interesado</Badge>
              {isHumanNeeded && <Badge variant="destructive" className="bg-destructive/10 text-destructive border-none">Requiere Humano</Badge>}
            </div>
          </div>
        </div>

        {/* Info CRM */}
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Datos CRM</h4>
          
          <div className="space-y-2">
            <div className="flex justify-between items-center text-sm">
              <span className="text-muted-foreground">Etapa Pipeline</span>
              <span className="font-medium text-foreground capitalize">{conversation.pipelineStage || 'Nuevo'}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-muted-foreground">Score</span>
              <span className="font-medium text-green-500">Alto (85%)</span>
            </div>
          </div>
        </div>

        {/* Acciones */}
        <div className="pt-4 border-t border-border space-y-3">
          <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-2">Acciones de IA</h4>
          
          <Button 
            onClick={onTakeover}
            variant="default"
            className="w-full bg-primary text-primary-foreground hover:bg-primary-hover shadow-[0_0_15px_rgba(6,182,212,0.3)] gap-2"
          >
            <PauseCircle className="w-4 h-4" />
            Tomar Control de la IA
          </Button>

          <Button variant="outline" className="w-full border-border hover:bg-white/5 gap-2">
            <DollarSign className="w-4 h-4" />
            Enviar Link de Pago
          </Button>
          
          <Button variant="outline" className="w-full border-border hover:bg-white/5 gap-2">
            <CheckCircle2 className="w-4 h-4" />
            Marcar Resuelto
          </Button>
        </div>
      </div>
    </div>
  );
}

function SparklesIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
    </svg>
  );
}
