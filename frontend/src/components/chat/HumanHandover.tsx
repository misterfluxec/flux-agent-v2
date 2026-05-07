'use client';
import { UserPlus, X, ShieldCheck } from 'lucide-react';
import { useState } from 'react';
import { useTranslations } from 'next-intl';

export function HumanHandover({ chatId, agentName }: { chatId: string, agentName: string }) {
  const t = useTranslations('chat');
  const [showModal, setShowModal] = useState(false);
  const [isAssigning, setIsAssigning] = useState(false);

  const handleAssign = async () => {
    setIsAssigning(true);
    // Simular llamada a API
    await new Promise(r => setTimeout(r, 1000));
    console.log(`Assigned ${chatId} to ${agentName}`);
    setIsAssigning(false);
    setShowModal(false);
  };

  return (
    <>
      <button 
        onClick={() => setShowModal(true)}
        className="flex items-center gap-2 px-4 py-2 bg-yellow-500/10 text-yellow-600 hover:bg-yellow-500/20 rounded-xl text-xs font-black uppercase tracking-wider transition-all active:scale-95 shadow-sm"
      >
        <UserPlus className="w-3.5 h-3.5" /> {t('assign_human')}
      </button>

      {showModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-card border border-border rounded-3xl p-8 max-w-sm w-full space-y-6 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-yellow-500/5 rounded-bl-full -mr-12 -mt-12" />
            
            <div className="flex justify-between items-start relative z-10">
              <div className="w-12 h-12 rounded-2xl bg-yellow-500/20 flex items-center justify-center text-yellow-600">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <button onClick={() => setShowModal(false)} className="text-muted-foreground hover:text-foreground">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2 relative z-10">
              <h3 className="font-black text-2xl tracking-tight">{t('assign_to_human')}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {t('assign_desc', { agent: agentName })}
              </p>
            </div>

            <div className="flex gap-3 relative z-10">
              <button 
                onClick={() => setShowModal(false)} 
                className="flex-1 py-3 text-sm font-bold text-muted-foreground hover:bg-accent rounded-2xl transition-all"
              >
                Cancelar
              </button>
              <button 
                disabled={isAssigning}
                onClick={handleAssign}
                className="flex-1 py-3 bg-primary text-primary-foreground rounded-2xl text-sm font-black shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all active:scale-95 disabled:opacity-50"
              >
                {isAssigning ? t('assigning') : 'Confirmar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
