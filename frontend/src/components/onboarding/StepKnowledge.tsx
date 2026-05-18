import { UploadCloud, CheckCircle2, ArrowLeft, Database } from 'lucide-react';
import { OnboardingData } from '@/hooks/useOnboardingWizard';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';

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
    <motion.div 
      initial={{ opacity: 0, y: 20 }} 
      animate={{ opacity: 1, y: 0 }} 
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="relative space-y-8 py-4"
    >
      <div className="text-center space-y-2 relative z-10">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2, type: 'spring' }}
          className="inline-flex p-3 rounded-full bg-blue-500/10 border border-blue-500/20 mb-4 shadow-[0_0_30px_rgba(59,130,246,0.15)]"
        >
          <Database className="w-8 h-8 text-blue-500" strokeWidth={1.5} />
        </motion.div>
        <h2 className="text-2xl md:text-3xl font-bold text-foreground tracking-tight">
          Ingesta de <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">Conocimiento</span>
        </h2>
        <p className="text-muted-foreground text-xs md:text-sm max-w-sm mx-auto">
          Alimenta al agente con la sabiduría de tu negocio. Arrastra archivos al portal.
        </p>
      </div>

      <div className="max-w-xl mx-auto space-y-8 relative z-10">
        {!isLoaded ? (
          <motion.div 
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="relative group cursor-pointer"
            onClick={handleSimulateUpload}
          >
            {/* Animated Glow Backdrop */}
            <div className="absolute -inset-1 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-[2rem] blur-xl opacity-50 group-hover:opacity-100 transition duration-500" />
            
            <div className="relative border border-dashed border-white/20 rounded-[2rem] p-12 md:p-16 text-center bg-black/40 backdrop-blur-xl hover:border-blue-500/50 transition-all shadow-[inset_0_0_40px_rgba(59,130,246,0.05)] overflow-hidden">
              
              {/* Radar Scan Animation */}
              <motion.div 
                className="absolute inset-0 bg-gradient-to-b from-transparent via-blue-500/5 to-transparent h-32 w-full"
                animate={{ top: ['-50%', '150%'] }}
                transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
              />

              <div className="relative z-10">
                <motion.div 
                  className="inline-flex p-5 bg-white/[0.02] rounded-full mb-6 border border-white/10 group-hover:border-blue-500/40 group-hover:bg-blue-500/10 transition-all shadow-lg"
                  whileHover={{ rotate: 180 }}
                  transition={{ duration: 0.8, type: "spring" }}
                >
                  <UploadCloud className="w-10 h-10 text-white/50 group-hover:text-blue-400 transition-colors" strokeWidth={1} />
                </motion.div>
                <h3 className="text-xl font-bold text-white/90 mb-2">Portal de Ingesta</h3>
                <p className="text-[10px] text-white/40 mb-8 uppercase tracking-[0.2em] font-bold">Admite: PDF, CSV, Excel, TXT</p>
                
                <Button variant="outline" className="relative overflow-hidden h-10 px-8 text-xs font-black uppercase tracking-widest text-blue-400 border-blue-500/30 hover:bg-blue-500/10 hover:text-blue-300 rounded-full transition-all group-hover:shadow-[0_0_20px_rgba(59,130,246,0.2)]">
                  Explorar Archivos
                </Button>
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="border border-blue-500/30 rounded-[2rem] p-12 text-center bg-blue-500/10 relative overflow-hidden group shadow-[0_0_50px_rgba(59,130,246,0.15)] backdrop-blur-xl"
          >
            <div className="absolute -top-20 -right-20 w-48 h-48 bg-blue-500/20 rounded-full blur-3xl animate-pulse" />
            <div className="absolute -bottom-20 -left-20 w-48 h-48 bg-cyan-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
            
            <motion.div 
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", bounce: 0.6 }}
              className="inline-flex p-4 bg-blue-500/20 rounded-full mb-4 border border-blue-400/30 relative z-10"
            >
              <CheckCircle2 className="w-10 h-10 text-blue-400" strokeWidth={1.5} />
            </motion.div>
            <h3 className="text-xl font-bold text-white mb-2 tracking-tight relative z-10">¡Ingesta Completada!</h3>
            <p className="text-xs text-blue-200/70 max-w-xs mx-auto relative z-10">La red neuronal ha indexado 312 nodos de conocimiento sobre tus productos.</p>
            <button 
              onClick={() => onChange('conocimiento_cargado', false)}
              className="mt-8 text-[10px] font-black uppercase tracking-[0.2em] text-blue-400 hover:text-blue-300 transition-colors relative z-10 underline decoration-blue-500/30 underline-offset-4"
            >
              Sobrescribir Memoria
            </button>
          </motion.div>
        )}
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
              isLoaded 
                ? 'border-blue-500/40 bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 shadow-[0_0_20px_rgba(59,130,246,0.2)]' 
                : 'border-white/10 bg-white/5 text-white/50 hover:bg-white/10 hover:text-white'
            }`}
          >
            {isLoaded ? "Siguiente Fase ➔" : "Omitir Ingesta ➔"}
          </Button>
        </motion.div>
      </div>
    </motion.div>
  );
}
