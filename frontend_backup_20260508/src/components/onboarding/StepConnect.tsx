import { QrCode, CheckCircle2, ArrowLeft, MessageCircle, Send } from 'lucide-react';
import { OnboardingData } from '@/hooks/useOnboardingWizard';
import { Button } from '@/components/ui/button';

interface Props {
  data: OnboardingData;
  onChange: (field: keyof OnboardingData, value: any) => void;
  onNext: () => void;
  onBack: () => void;
}

export function StepConnect({ data, onChange, onNext, onBack }: Props) {
  const isWsConnected = data.whatsapp_conectado;
  const isTgConnected = data.telegram_conectado;
  const isAnyConnected = isWsConnected || isTgConnected;

  const handleSimulateConnection = (type: 'ws' | 'tg') => {
    setTimeout(() => {
      if (type === 'ws') onChange('whatsapp_conectado', true);
      else onChange('telegram_conectado', true);
    }, 1500);
  };

  return (
    <div className="relative space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 py-4">
      <div className="text-center space-y-1">
        <h2 className="text-xl md:text-2xl font-bold text-foreground">
          Conectar <span className="text-primary">Canales</span>
        </h2>
        <p className="text-muted-foreground text-xs max-w-sm mx-auto">
          Vincula tus redes para que Yanua empiece a interactuar con tus clientes.
        </p>
      </div>

      <div className="max-w-4xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* WhatsApp Card */}
          <div className={`relative p-6 rounded-2xl border transition-all duration-300 flex flex-col items-center ${
            isWsConnected 
              ? 'border-green-500/30 bg-green-500/10 shadow-lg shadow-green-500/5' 
              : 'border-white/10 bg-white/[0.03] hover:border-white/20'
          }`}>
            <div className={`p-3 rounded-full mb-3 transition-colors ${isWsConnected ? 'bg-green-500/20' : 'bg-green-500/10'}`}>
              <MessageCircle className="w-8 h-8 text-green-500" strokeWidth={1.5} />
            </div>
            <h3 className="text-sm font-bold text-foreground mb-1">WhatsApp</h3>
            <p className="text-[10px] text-muted-foreground/70 uppercase tracking-[0.1em] mb-6">
              {isWsConnected ? 'Canal Vinculado' : 'Escanea para conectar'}
            </p>
            
            {!isWsConnected ? (
              <div 
                className="w-36 h-36 bg-white rounded-xl flex items-center justify-center p-2 mb-2 cursor-pointer hover:scale-[1.02] transition-transform shadow-2xl"
                onClick={() => handleSimulateConnection('ws')}
              >
                <QrCode className="w-28 h-28 text-black" strokeWidth={1} />
              </div>
            ) : (
              <div className="flex flex-col items-center py-10 gap-2">
                <div className="p-2 bg-green-500/20 rounded-full animate-pulse">
                  <CheckCircle2 className="w-6 h-6 text-green-500" strokeWidth={1.5} />
                </div>
                <span className="text-[10px] font-bold text-green-500 uppercase tracking-widest">Línea Activa</span>
              </div>
            )}
          </div>

          {/* Telegram Card */}
          <div className={`relative p-6 rounded-2xl border transition-all duration-300 flex flex-col items-center ${
            isTgConnected 
              ? 'border-blue-500/30 bg-blue-500/10 shadow-lg shadow-blue-500/5' 
              : 'border-white/10 bg-white/[0.03] hover:border-white/20'
          }`}>
            <div className={`p-3 rounded-full mb-3 transition-colors ${isTgConnected ? 'bg-blue-500/20' : 'bg-blue-500/10'}`}>
              <Send className="w-8 h-8 text-blue-500" strokeWidth={1.5} />
            </div>
            <h3 className="text-sm font-bold text-foreground mb-1">Telegram</h3>
            <p className="text-[10px] text-muted-foreground/70 uppercase tracking-[0.1em] mb-6">
              {isTgConnected ? 'Bot Vinculado' : 'Ingresa tu Token'}
            </p>
            
            {!isTgConnected ? (
              <div className="w-full space-y-4 pt-2">
                <div className="relative group">
                  <label className="absolute -top-2 left-3 px-1.5 bg-[#0A0A0B] text-[9px] font-bold text-primary uppercase tracking-widest z-10">
                    Bot Token
                  </label>
                  <input 
                    type="password" 
                    placeholder="728394:AAF_..." 
                    className="w-full bg-white/[0.02] border border-white/10 rounded-xl px-4 py-3 text-xs outline-none focus:border-primary/40 transition-all text-center"
                  />
                </div>
                <Button 
                  onClick={() => handleSimulateConnection('tg')}
                  variant="ghost" 
                  className="w-full h-10 text-[10px] font-bold uppercase tracking-widest text-primary hover:text-primary hover:bg-primary/5 rounded-xl"
                >
                  Vincular Bot
                </Button>
              </div>
            ) : (
              <div className="flex flex-col items-center py-10 gap-2">
                <div className="p-2 bg-blue-500/20 rounded-full animate-pulse">
                  <CheckCircle2 className="w-6 h-6 text-blue-500" strokeWidth={1.5} />
                </div>
                <span className="text-[10px] font-bold text-blue-500 uppercase tracking-widest">Bot Listo</span>
              </div>
            )}
          </div>
        </div>
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
          {isAnyConnected ? "Siguiente Paso ➔" : "Omitir Paso ➔"}
        </Button>
      </div>
    </div>
  );
}
