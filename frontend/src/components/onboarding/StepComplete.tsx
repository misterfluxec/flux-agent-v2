import { Rocket, Loader2, Sparkles, ArrowLeft, Power } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';

interface Props {
  isLoading: boolean;
  onSubmit: () => void;
  onBack: () => void;
}

export function StepComplete({ isLoading, onSubmit, onBack }: Props) {
  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }} 
      animate={{ opacity: 1, scale: 1 }} 
      transition={{ duration: 0.7, ease: "easeOut" }}
      className="relative space-y-10 text-center py-8"
    >
      <div className="relative inline-flex mb-4 group">
        <motion.div 
          className="absolute inset-0 bg-primary/30 rounded-full blur-[40px]"
          animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0.8, 0.5] }}
          transition={{ repeat: Infinity, duration: 2.5, ease: "easeInOut" }}
        />
        <div className="relative p-8 bg-black/40 backdrop-blur-xl rounded-full border border-primary/40 shadow-[inset_0_0_30px_rgba(6,182,212,0.1)]">
          <Power className="w-16 h-16 text-primary group-hover:drop-shadow-[0_0_15px_rgba(6,182,212,0.8)] transition-all duration-500" strokeWidth={1} />
        </div>
        <motion.div 
          className="absolute -top-4 -right-4 bg-[#0A0A0B] border border-primary/30 rounded-full p-3 shadow-xl"
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 8, ease: "linear" }}
        >
          <Sparkles className="w-5 h-5 text-purple-400" />
        </motion.div>
      </div>
      
      <div className="space-y-3 relative z-10">
        <h2 className="text-3xl md:text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-primary via-purple-400 to-pink-500 tracking-tight drop-shadow-sm">
          Secuencia Completada
        </h2>
        <p className="text-muted-foreground text-sm max-w-sm mx-auto leading-relaxed">
          La arquitectura cognitiva ha sido ensamblada. Tu instancia de <span className="text-white font-black tracking-wide drop-shadow-[0_0_5px_rgba(255,255,255,0.5)]">FluxAgent OS</span> está lista para despertar.
        </p>
      </div>

      <div className="pt-8 flex flex-col items-center gap-8 max-w-sm mx-auto w-full relative z-10">
        <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} className="w-full">
          <Button 
            onClick={onSubmit} 
            disabled={isLoading}
            className="w-full h-16 relative overflow-hidden bg-gradient-to-r from-primary to-purple-600 text-white shadow-[0_0_40px_rgba(168,85,247,0.4)] text-[13px] uppercase tracking-[0.2em] font-black rounded-[2rem] transition-all disabled:opacity-50 border border-white/20 group"
          >
            {/* Shimmer Effect */}
            <motion.div 
              className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/40 to-transparent skew-x-12"
              animate={{ translateX: ['100%', '-100%'] }}
              transition={{ repeat: Infinity, duration: 2.5, ease: "easeInOut" }}
            />

            {isLoading ? (
              <span className="flex items-center gap-3 relative z-10">
                <Loader2 className="w-5 h-5 animate-spin text-white" />
                Inicializando Core...
              </span>
            ) : (
              <span className="flex items-center gap-3 relative z-10">
                <Rocket className="w-5 h-5 group-hover:-translate-y-1 group-hover:translate-x-1 transition-transform" />
                Activar Agente 
              </span>
            )}
          </Button>
        </motion.div>

        <button 
          onClick={onBack}
          disabled={isLoading}
          className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-white/30 hover:text-white transition-colors outline-none disabled:opacity-0 group"
        >
          <ArrowLeft className="w-3 h-3 group-hover:-translate-x-1 transition-transform" />
          Revisar Parámetros
        </button>
      </div>
    </motion.div>
  );
}
