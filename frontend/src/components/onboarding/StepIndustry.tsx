import { OnboardingData } from '@/hooks/useOnboardingWizard';
import { Button } from '@/components/ui/button';
import { Shield, Utensils, ShoppingCart, Activity, Briefcase, Car, Hammer, Shirt, Laptop, GraduationCap, ArrowLeft, Sparkles, ShoppingBag, Network } from 'lucide-react';
import { motion } from 'framer-motion';

interface Props {
  data: OnboardingData;
  onChange: (field: keyof OnboardingData, value: any) => void;
  onNext: () => void;
  onBack: () => void;
}

const INDUSTRIES = [
  { id: 'seguridad', label: 'Seguridad', icon: Shield, color: 'text-indigo-400', glow: 'shadow-[0_0_20px_rgba(129,140,248,0.2)]' },
  { id: 'restaurante', label: 'Restaurante', icon: Utensils, color: 'text-orange-400', glow: 'shadow-[0_0_20px_rgba(251,146,60,0.2)]' },
  { id: 'ecommerce', label: 'Ecommerce', icon: ShoppingBag, color: 'text-pink-400', glow: 'shadow-[0_0_20px_rgba(244,114,182,0.2)]' },
  { id: 'clinica', label: 'Clínica', icon: Activity, color: 'text-emerald-400', glow: 'shadow-[0_0_20px_rgba(52,211,153,0.2)]' },
  { id: 'servicios', label: 'Servicios', icon: Briefcase, color: 'text-blue-400', glow: 'shadow-[0_0_20px_rgba(96,165,250,0.2)]' },
  { id: 'automotriz', label: 'Automotriz', icon: Car, color: 'text-red-400', glow: 'shadow-[0_0_20px_rgba(248,113,113,0.2)]' },
  { id: 'ferreteria', label: 'Ferretería', icon: Hammer, color: 'text-yellow-400', glow: 'shadow-[0_0_20px_rgba(250,204,21,0.2)]' },
  { id: 'retail', label: 'Retail', icon: Shirt, color: 'text-purple-400', glow: 'shadow-[0_0_20px_rgba(192,132,252,0.2)]' },
  { id: 'tecnologia', label: 'Tecnología', icon: Laptop, color: 'text-cyan-400', glow: 'shadow-[0_0_20px_rgba(34,211,238,0.2)]' },
  { id: 'custom', label: 'Otro', icon: Network, color: 'text-white/50', glow: 'shadow-[0_0_20px_rgba(255,255,255,0.1)]' },
];

export function StepIndustry({ data, onChange, onNext, onBack }: Props) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }} 
      animate={{ opacity: 1, y: 0 }} 
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="relative space-y-8 py-4"
    >
      <div className="text-center space-y-2 relative z-10">
        <h2 className="text-2xl md:text-3xl font-bold text-foreground tracking-tight">
          Sector <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-purple-400">Operativo</span>
        </h2>
        <p className="text-muted-foreground text-xs md:text-sm max-w-sm mx-auto">
          Selecciona el dominio de conocimiento base. Yanua pre-cargará los protocolos de esta industria.
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4 md:gap-5 mt-10 relative z-10">
        {INDUSTRIES.map((ind, idx) => {
          const Icon = ind.icon;
          const isSelected = data.industria === ind.id;
          return (
            <motion.button
              key={ind.id}
              onClick={() => onChange('industria', ind.id)}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.05 * idx, type: 'spring' }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className={`group relative p-6 rounded-3xl border transition-all duration-500 flex flex-col items-center justify-center gap-4 outline-none ${
                isSelected
                  ? `border-white/30 bg-white/10 ${ind.glow} backdrop-blur-xl`
                  : 'border-white/5 bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04] backdrop-blur-sm'
              }`}
            >
              {isSelected && (
                <motion.div 
                  layoutId="industryGlow"
                  className="absolute inset-0 rounded-3xl bg-gradient-to-b from-white/10 to-transparent opacity-50"
                  transition={{ type: "spring", stiffness: 300, damping: 20 }}
                />
              )}

              <div className="relative">
                <Icon className={`w-8 h-8 transition-all duration-500 ${isSelected ? ind.color + ' scale-125' : 'text-white/20 group-hover:text-white/50'}`} strokeWidth={1.5} />
                
                {isSelected && (
                  <motion.div 
                    initial={{ scale: 0 }} 
                    animate={{ scale: 1 }} 
                    className="absolute -top-2 -right-2"
                  >
                    <Sparkles className={`w-4 h-4 ${ind.color}`} />
                  </motion.div>
                )}
              </div>
              
              <span className={`text-[10px] font-black uppercase tracking-[0.15em] transition-colors duration-300 relative z-10 ${isSelected ? 'text-white' : 'text-white/30 group-hover:text-white/60'}`}>
                {ind.label}
              </span>
            </motion.button>
          );
        })}
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
            disabled={!data.industria}
            variant="outline"
            className="h-12 px-10 border-primary/40 text-primary hover:bg-primary/10 rounded-full text-xs font-black uppercase tracking-[0.2em] backdrop-blur-md transition-all disabled:opacity-20 shadow-[0_0_20px_rgba(6,182,212,0.15)] group relative overflow-hidden"
          >
            <span className="relative z-10">Siguiente Fase ➔</span>
            <div className="absolute inset-0 bg-gradient-to-r from-primary/0 via-primary/10 to-primary/0 -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]" />
          </Button>
        </motion.div>
      </div>
    </motion.div>
  );
}
