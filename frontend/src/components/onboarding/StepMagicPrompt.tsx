import { useState } from 'react';
import { OnboardingData } from '@/hooks/useOnboardingWizard';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Sparkles, CheckCircle2, Cpu, BrainCircuit } from 'lucide-react';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';

interface Props {
  data: OnboardingData;
  onChange: (field: keyof OnboardingData, value: any) => void;
  onNext: () => void;
  onBack: () => void;
}

export function StepMagicPrompt({ data, onChange, onNext, onBack }: Props) {
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGeneratePrompt = async () => {
    if (!data.business_description || data.business_description.length < 10) {
      toast.error('Por favor describe tu negocio con un poco más de detalle.');
      return;
    }

    setIsGenerating(true);
    
    // Simulate cognitive synthesis
    setTimeout(() => {
      const generatedPrompt = `Eres ${data.name || 'un asistente'}, experto en la industria de ${data.industria || 'tu sector'}. 
Tu objetivo principal es asistir a los clientes de forma amable, directa y orientada a resultados.

Contexto del Negocio:
${data.business_description}

Reglas de Comportamiento:
1. Mantén un tono profesional pero cercano.
2. Si el cliente pregunta por un producto, revisa la base de conocimientos antes de responder.
3. Nunca inventes precios ni promociones que no estén en tu contexto.
4. Siempre intenta guiar la conversación hacia una conversión o cierre.`;
      
      onChange('system_prompt', generatedPrompt);
      setIsGenerating(false);
      toast.success('🧠 Enlaces neuronales creados exitosamente');
    }, 3000);
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
          className="inline-flex p-3 rounded-full bg-primary/10 border border-primary/20 mb-4 shadow-[0_0_30px_rgba(6,182,212,0.15)]"
        >
          <BrainCircuit className="w-8 h-8 text-primary" strokeWidth={1.5} />
        </motion.div>
        <h2 className="text-2xl md:text-3xl font-bold text-foreground tracking-tight">
          Sintetizar <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-purple-400">Cerebro Mágico</span>
        </h2>
        <p className="text-muted-foreground text-xs md:text-sm max-w-md mx-auto">
          Dale vida a tu agente. Describe tu visión y nuestra IA estructurará la matriz cognitiva perfecta.
        </p>
      </div>

      <div className="max-w-2xl mx-auto space-y-8 relative z-10">
        <motion.div 
          className="space-y-3 relative group"
          whileHover={{ scale: 1.01 }}
          transition={{ type: "spring", stiffness: 300, damping: 20 }}
        >
          <div className="absolute -inset-1 bg-gradient-to-r from-primary/20 to-purple-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition duration-500" />
          <div className="relative bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-2xl">
            <label className="text-xs font-black text-white/50 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-primary" />
              1. ADN del Negocio
            </label>
            <textarea
              value={data.business_description}
              onChange={(e) => onChange('business_description', e.target.value)}
              placeholder="Ej: Somos una zapatería online que vende calzado deportivo premium. Nuestro valor principal es el envío rápido y las devoluciones gratuitas..."
              className="w-full bg-transparent border-none px-0 py-2 text-sm text-white/90 placeholder:text-white/20 outline-none resize-none min-h-[80px]"
            />
          </div>
        </motion.div>

        <div className="flex justify-center relative">
          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Button
              onClick={handleGeneratePrompt}
              disabled={isGenerating || data.business_description.length < 5}
              className="relative overflow-hidden h-14 px-10 rounded-full bg-gradient-to-r from-cyan-500 via-primary to-purple-500 border border-white/20 text-white font-bold tracking-widest uppercase text-[11px] shadow-[0_0_40px_rgba(6,182,212,0.4)] disabled:opacity-50"
            >
              {isGenerating ? (
                <span className="flex items-center gap-3 relative z-10">
                  <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 2, ease: "linear" }}>
                    <Sparkles className="w-5 h-5 text-white" />
                  </motion.div>
                  Sintetizando Consciencia...
                </span>
              ) : (
                <span className="flex items-center gap-3 relative z-10">
                  <Sparkles className="w-5 h-5" />
                  Despertar Agente
                </span>
              )}
              {/* Shimmer effect */}
              <motion.div 
                className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/40 to-transparent skew-x-12"
                animate={{ translateX: ['100%', '-100%'] }}
                transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
              />
            </Button>
          </motion.div>
        </div>

        <AnimatePresence>
          {data.system_prompt && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="pt-4"
            >
              <div className="relative bg-primary/[0.03] backdrop-blur-3xl border border-primary/20 rounded-2xl p-6 shadow-[inset_0_0_30px_rgba(6,182,212,0.05)]">
                <div className="flex items-center justify-between mb-4">
                  <label className="text-xs font-black text-primary uppercase tracking-[0.2em] flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4" />
                    2. Matriz Cognitiva (System Prompt)
                  </label>
                  <span className="text-[9px] font-bold text-primary/50 uppercase tracking-widest border border-primary/20 px-2 py-1 rounded-full">
                    Editable
                  </span>
                </div>
                <textarea
                  value={data.system_prompt}
                  onChange={(e) => onChange('system_prompt', e.target.value)}
                  className="w-full bg-transparent border-none p-0 text-xs md:text-sm font-mono text-primary/80 outline-none min-h-[160px] resize-y leading-relaxed"
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
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
            disabled={!data.system_prompt}
            variant="outline"
            className="h-12 px-10 border-white/10 bg-white/5 text-white hover:bg-white/10 rounded-full text-xs font-black uppercase tracking-[0.2em] backdrop-blur-md transition-all disabled:opacity-20 shadow-2xl"
          >
            Siguiente Fase ➔
          </Button>
        </motion.div>
      </div>
    </motion.div>
  );
}
