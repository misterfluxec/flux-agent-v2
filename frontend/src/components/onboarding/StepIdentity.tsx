import { Bot, Camera, Sparkles, User, Smile, SmilePlus } from 'lucide-react';
import { OnboardingData } from '@/hooks/useOnboardingWizard';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';

interface Props {
  data: OnboardingData;
  onChange: (field: keyof OnboardingData, value: string) => void;
  onNext: () => void;
}

const PREDEFINED_AVATARS = [
  { 
    id: 'man', 
    label: 'Él', 
    icon: Smile, 
    gradient: 'from-blue-500/20 to-cyan-500/10',
    color: 'text-blue-400',
    glow: 'shadow-[0_0_30px_rgba(59,130,246,0.3)]',
  },
  { 
    id: 'woman', 
    label: 'Ella', 
    icon: SmilePlus, 
    gradient: 'from-pink-500/20 to-purple-500/10',
    color: 'text-pink-400',
    glow: 'shadow-[0_0_30px_rgba(236,72,153,0.3)]',
  },
  { 
    id: 'agent', 
    label: 'Agente', 
    icon: Bot, 
    gradient: 'from-emerald-500/20 to-teal-500/10',
    color: 'text-emerald-400',
    glow: 'shadow-[0_0_30px_rgba(16,185,129,0.3)]',
  },
];

export function StepIdentity({ data, onChange, onNext }: Props) {
  const isValid = data.name.trim().length >= 2;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }} 
      animate={{ opacity: 1, y: 0 }} 
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="relative space-y-8 flex flex-col justify-center py-4"
    >
      <div className="text-center space-y-2 relative z-10">
        <h2 className="text-2xl md:text-3xl font-bold text-foreground tracking-tight">
          Entidad del <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-purple-400">Asistente</span>
        </h2>
        <p className="text-muted-foreground text-xs md:text-sm max-w-sm mx-auto">
          Define la carcasa digital de tu IA. Elige su forma y otórgale un nombre.
        </p>
      </div>

      <div className="max-w-xl mx-auto w-full space-y-12 relative z-10 pt-4">
        {/* Subtle Avatar Selection */}
        <div className="flex flex-wrap justify-center items-center gap-6 md:gap-10">
          {PREDEFINED_AVATARS.map((av, idx) => {
            const Icon = av.icon;
            const isSelected = data.avatar === av.id;
            return (
              <motion.button
                key={av.id}
                onClick={() => onChange('avatar', av.id)}
                className="flex flex-col items-center group outline-none"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * idx, type: 'spring' }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <div className="relative">
                  {/* Glowing background aura */}
                  {isSelected && (
                    <motion.div 
                      layoutId="activeAura"
                      className={`absolute inset-0 rounded-full blur-xl ${av.glow} bg-white/10`} 
                      transition={{ type: "spring", stiffness: 300, damping: 20 }}
                    />
                  )}
                  
                  <div className={`relative w-20 h-20 md:w-24 md:h-24 rounded-full border backdrop-blur-xl flex items-center justify-center transition-all duration-500 ${
                    isSelected 
                      ? `border-white/40 bg-gradient-to-br ${av.gradient} ${av.glow}` 
                      : 'border-white/5 bg-white/[0.02] hover:border-white/20'
                  }`}>
                    <Icon className={`w-10 h-10 md:w-12 md:h-12 transition-all duration-300 ${isSelected ? av.color : 'text-white/20 group-hover:text-white/50'}`} strokeWidth={1.5} />
                  </div>
                  
                  {isSelected && (
                    <motion.div 
                      initial={{ scale: 0 }} 
                      animate={{ scale: 1 }} 
                      className="absolute -top-1 -right-1 bg-white/10 backdrop-blur-md rounded-full p-1.5 shadow-sm z-20 border border-white/20"
                    >
                      <Sparkles className={`w-4 h-4 ${av.color}`} />
                    </motion.div>
                  )}
                </div>
                <span className={`mt-4 text-[10px] font-black uppercase tracking-[0.2em] transition-all duration-300 ${
                  isSelected ? 'text-white drop-shadow-md' : 'text-white/20 group-hover:text-white/40'
                }`}>
                  {av.label}
                </span>
              </motion.button>
            );
          })}
          
          <motion.button 
            className="flex flex-col items-center group outline-none opacity-50 hover:opacity-100"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <div className="w-20 h-20 md:w-24 md:h-24 rounded-full border border-dashed border-white/20 flex items-center justify-center bg-transparent group-hover:bg-white/[0.02] transition-all">
              <Camera className="w-8 h-8 text-white/20 group-hover:text-white/60" strokeWidth={1.5} />
            </div>
            <span className="mt-4 text-[9px] font-black text-white/20 uppercase tracking-[0.2em]">Subir</span>
          </motion.button>
        </div>

        {/* Restored Input Style */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="max-w-sm mx-auto space-y-8"
        >
          <div className="relative group">
            <label className="absolute -top-2 left-4 px-2 bg-[#0A0A0B] text-[9px] font-black text-primary uppercase tracking-[0.2em] z-10 transition-colors group-focus-within:text-purple-400">
              Identidad de Sistema
            </label>
            <input
              type="text"
              value={data.name}
              onChange={(e) => onChange('name', e.target.value)}
              placeholder="Ej: Yanua, Alex, Sofia..."
              className="w-full px-5 py-4 bg-white/[0.02] border border-white/10 rounded-2xl focus:border-primary/50 focus:bg-primary/[0.02] focus:shadow-[0_0_20px_rgba(6,182,212,0.1)] outline-none transition-all text-white text-sm font-medium placeholder:text-white/20 text-center tracking-wide"
            />
          </div>

          <div className="flex justify-center">
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Button 
                onClick={onNext} 
                disabled={!isValid || !data.avatar} 
                variant="outline"
                className="h-12 px-12 border-primary/40 text-primary hover:bg-primary/10 rounded-full text-xs font-black uppercase tracking-[0.2em] backdrop-blur-md transition-all disabled:opacity-20 shadow-[0_0_20px_rgba(6,182,212,0.15)] group relative overflow-hidden"
              >
                <span className="relative z-10">Iniciar Secuencia ➔</span>
                <div className="absolute inset-0 bg-gradient-to-r from-primary/0 via-primary/10 to-primary/0 -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]" />
              </Button>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
