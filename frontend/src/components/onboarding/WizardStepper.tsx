import { Check } from 'lucide-react';
import { motion } from 'framer-motion';

export function WizardStepper({ currentStep }: { currentStep: number }) {
  const steps = [
    { num: 1, label: 'Identidad' },
    { num: 2, label: 'Industria' },
    { num: 3, label: 'Conocimiento' },
    { num: 4, label: 'Cerebro' },
    { num: 5, label: 'Canales' },
    { num: 6, label: 'Activación' },
  ];

  return (
    <div className="mb-14 px-2 md:px-8">
      <div className="flex items-center justify-between relative max-w-3xl mx-auto">
        {/* Background Track Line */}
        <div className="absolute top-1/2 left-0 w-full h-[2px] bg-white/5 rounded-full -translate-y-1/2" />
        
        {/* Animated Glowing Progress Line */}
        <motion.div
          className="absolute top-1/2 left-0 h-[2px] bg-gradient-to-r from-primary to-purple-500 rounded-full -translate-y-1/2 shadow-[0_0_15px_rgba(6,182,212,0.6)]"
          initial={{ width: 0 }}
          animate={{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }}
          transition={{ duration: 0.8, ease: "easeInOut" }}
        />

        {steps.map((s) => {
          const isCompleted = s.num < currentStep;
          const isActive = s.num === currentStep;
          const isPending = s.num > currentStep;

          return (
            <div key={s.num} className="relative z-10 flex flex-col items-center">
              {/* Dynamic Aura for the active step */}
              {isActive && (
                <motion.div 
                  className="absolute inset-0 m-auto w-10 h-10 rounded-full bg-primary/20 blur-md"
                  animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0.8, 0.5] }}
                  transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
                />
              )}
              
              <motion.div
                className={`relative z-10 w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center border backdrop-blur-md transition-colors duration-500 ${
                  isCompleted
                    ? 'bg-primary border-primary text-white shadow-[0_0_20px_rgba(6,182,212,0.4)]'
                    : isActive
                    ? 'bg-black/60 border-primary text-primary shadow-[0_0_25px_rgba(6,182,212,0.6)]'
                    : 'bg-black/40 border-white/10 text-white/20'
                }`}
                animate={{
                  scale: isActive ? 1.15 : 1,
                }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
              >
                {isCompleted ? (
                  <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring" }}>
                    <Check className="w-4 h-4 sm:w-5 sm:h-5" strokeWidth={3} />
                  </motion.div>
                ) : (
                  <span className={`text-[11px] sm:text-xs font-black ${isActive ? 'text-transparent bg-clip-text bg-gradient-to-br from-primary to-purple-400' : ''}`}>
                    {s.num}
                  </span>
                )}
              </motion.div>
              
              <div className="absolute -bottom-8 w-max">
                <span className={`text-[9px] font-black uppercase tracking-[0.15em] transition-all duration-500 ${
                  isActive 
                    ? 'text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]' 
                    : isCompleted
                    ? 'text-primary/70'
                    : 'text-white/20'
                }`}>
                  {s.label}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
