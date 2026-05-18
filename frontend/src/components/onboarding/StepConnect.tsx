import { QrCode, CheckCircle2, ArrowLeft, MessageCircle, Send } from 'lucide-react';
import { OnboardingData } from '@/hooks/useOnboardingWizard';
import { Button } from '@/components/ui/button';
import { motion, AnimatePresence } from 'framer-motion';

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
    <motion.div 
      initial={{ opacity: 0, y: 20 }} 
      animate={{ opacity: 1, y: 0 }} 
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="relative space-y-8 py-4"
    >
      <div className="text-center space-y-2 relative z-10">
        <h2 className="text-2xl md:text-3xl font-bold text-foreground tracking-tight">
          Nodos de <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-400">Transmisión</span>
        </h2>
        <p className="text-muted-foreground text-xs md:text-sm max-w-sm mx-auto">
          Vincula los canales de comunicación. Yanua operará de forma autónoma en ellos.
        </p>
      </div>

      <div className="max-w-4xl mx-auto relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* WhatsApp Card */}
          <motion.div 
            whileHover={{ scale: 1.02 }}
            className={`relative p-8 rounded-[2rem] border transition-all duration-500 flex flex-col items-center justify-between min-h-[320px] backdrop-blur-xl ${
            isWsConnected 
              ? 'border-green-500/40 bg-green-500/10 shadow-[0_0_40px_rgba(34,197,94,0.15)]' 
              : 'border-white/10 bg-black/40 hover:border-white/20'
          }`}>
            <div className="flex flex-col items-center w-full">
              <div className={`p-4 rounded-full mb-4 transition-colors duration-500 ${isWsConnected ? 'bg-green-500/20 shadow-[0_0_20px_rgba(34,197,94,0.3)]' : 'bg-green-500/10 border border-green-500/20'}`}>
                <MessageCircle className="w-8 h-8 text-green-400" strokeWidth={1.5} />
              </div>
              <h3 className="text-lg font-bold text-white mb-1 tracking-wide">WhatsApp Business</h3>
              <p className="text-[10px] font-black text-green-400/70 uppercase tracking-[0.2em] mb-8">
                {isWsConnected ? 'Canal Establecido' : 'Esperando Sincronización'}
              </p>
            </div>
            
            <AnimatePresence mode="wait">
              {!isWsConnected ? (
                <motion.div 
                  key="ws-qr"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="w-40 h-40 bg-white rounded-2xl flex items-center justify-center p-3 cursor-pointer hover:scale-[1.05] transition-transform shadow-[0_0_30px_rgba(255,255,255,0.1)] group relative"
                  onClick={() => handleSimulateConnection('ws')}
                >
                  <div className="absolute inset-0 bg-green-500/20 opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl" />
                  <QrCode className="w-32 h-32 text-black relative z-10" strokeWidth={1} />
                </motion.div>
              ) : (
                <motion.div 
                  key="ws-connected"
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex flex-col items-center py-6 gap-4"
                >
                  <div className="relative">
                    <div className="absolute inset-0 bg-green-500 rounded-full blur-xl opacity-40 animate-pulse" />
                    <div className="p-4 bg-green-500/20 rounded-full relative z-10 border border-green-500/40">
                      <CheckCircle2 className="w-8 h-8 text-green-400" strokeWidth={1.5} />
                    </div>
                  </div>
                  <span className="text-[11px] font-black text-green-400 uppercase tracking-[0.2em]">Enlace Activo</span>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>

          {/* Telegram Card */}
          <motion.div 
            whileHover={{ scale: 1.02 }}
            className={`relative p-8 rounded-[2rem] border transition-all duration-500 flex flex-col items-center justify-between min-h-[320px] backdrop-blur-xl ${
            isTgConnected 
              ? 'border-blue-500/40 bg-blue-500/10 shadow-[0_0_40px_rgba(59,130,246,0.15)]' 
              : 'border-white/10 bg-black/40 hover:border-white/20'
          }`}>
            <div className="flex flex-col items-center w-full">
              <div className={`p-4 rounded-full mb-4 transition-colors duration-500 ${isTgConnected ? 'bg-blue-500/20 shadow-[0_0_20px_rgba(59,130,246,0.3)]' : 'bg-blue-500/10 border border-blue-500/20'}`}>
                <Send className="w-8 h-8 text-blue-400" strokeWidth={1.5} />
              </div>
              <h3 className="text-lg font-bold text-white mb-1 tracking-wide">Telegram Bot</h3>
              <p className="text-[10px] font-black text-blue-400/70 uppercase tracking-[0.2em] mb-8">
                {isTgConnected ? 'Canal Establecido' : 'Requiere Autenticación'}
              </p>
            </div>
            
            <AnimatePresence mode="wait">
              {!isTgConnected ? (
                <motion.div 
                  key="tg-form"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="w-full space-y-5 px-4"
                >
                  <div className="relative group">
                    <label className="absolute -top-2 left-3 px-2 bg-[#0A0A0B] text-[9px] font-black text-blue-400 uppercase tracking-[0.2em] z-10">
                      Token de Acceso
                    </label>
                    <input 
                      type="password" 
                      placeholder="728394:AAF_..." 
                      className="w-full bg-white/[0.02] border border-white/10 rounded-2xl px-5 py-4 text-xs font-mono text-center outline-none focus:border-blue-500/50 focus:bg-blue-500/[0.02] transition-all text-white"
                    />
                  </div>
                  <Button 
                    onClick={() => handleSimulateConnection('tg')}
                    variant="outline" 
                    className="w-full h-12 text-[10px] font-black uppercase tracking-[0.2em] text-blue-400 border-blue-500/30 hover:bg-blue-500/10 hover:border-blue-500/50 rounded-2xl transition-all"
                  >
                    Vincular Red
                  </Button>
                </motion.div>
              ) : (
                <motion.div 
                  key="tg-connected"
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex flex-col items-center py-6 gap-4"
                >
                  <div className="relative">
                    <div className="absolute inset-0 bg-blue-500 rounded-full blur-xl opacity-40 animate-pulse" />
                    <div className="p-4 bg-blue-500/20 rounded-full relative z-10 border border-blue-500/40">
                      <CheckCircle2 className="w-8 h-8 text-blue-400" strokeWidth={1.5} />
                    </div>
                  </div>
                  <span className="text-[11px] font-black text-blue-400 uppercase tracking-[0.2em]">Enlace Activo</span>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </div>

      <div className="flex justify-between items-center pt-10">
        <button 
          onClick={onBack}
          className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground/70 hover:text-white transition-colors outline-none"
        >
          <ArrowLeft className="w-4 h-4" />
          Volver
        </button>
        
        <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
          <Button 
            onClick={onNext} 
            variant="outline"
            className={`h-12 px-10 rounded-full text-xs font-black uppercase tracking-[0.2em] backdrop-blur-md transition-all shadow-2xl ${
              isAnyConnected 
                ? 'border-primary/40 bg-primary/10 text-primary hover:bg-primary/20 shadow-[0_0_20px_rgba(6,182,212,0.2)]' 
                : 'border-white/10 bg-white/5 text-white/50 hover:bg-white/10 hover:text-white'
            }`}
          >
            {isAnyConnected ? "Siguiente Fase ➔" : "Omitir Conexión ➔"}
          </Button>
        </motion.div>
      </div>
    </motion.div>
  );
}
