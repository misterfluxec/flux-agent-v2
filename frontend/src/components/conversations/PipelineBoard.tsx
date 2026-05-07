import { useTranslations } from 'next-intl';
import { Conversation, PipelineStage } from '@/types/conversation';
import { Star, TrendingUp, MoreVertical } from 'lucide-react';

interface Props {
  conversations: Conversation[];
  onUpdateStage: (id: string, stage: PipelineStage) => void;
}

const STAGES: PipelineStage[] = ['new', 'qualified', 'negotiation', 'closed'];

export function PipelineBoard({ conversations, onUpdateStage }: Props) {
  const t = useTranslations('conversations');
  
  return (
    <div className="flex-1 overflow-x-auto p-6 bg-accent/5 custom-scrollbar">
      <div className="flex gap-6 h-full items-start">
        {STAGES.map(stage => {
          const stageConvs = conversations.filter(c => c.pipelineStage === stage);
          return (
            <div key={stage} className="flex-1 min-w-[280px] max-w-[320px] flex flex-col bg-muted/40 rounded-2xl border border-border/60 overflow-hidden">
              <div className="p-4 border-b border-border/60 flex justify-between items-center bg-card/30">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    stage === 'new' ? 'bg-blue-500' : 
                    stage === 'qualified' ? 'bg-purple-500' :
                    stage === 'negotiation' ? 'bg-orange-500' : 'bg-green-500'
                  }`} />
                  <span className="font-bold text-xs uppercase tracking-wider text-foreground/80">{t(`stage_${stage}` as any)}</span>
                </div>
                <span className="bg-primary/10 text-primary text-[10px] font-bold px-2 py-0.5 rounded-full border border-primary/10">{stageConvs.length}</span>
              </div>
              
              <div className="p-3 space-y-3 flex-1 overflow-y-auto custom-scrollbar min-h-[400px]">
                {stageConvs.map(c => (
                  <div key={c.id} className="bg-card p-4 rounded-xl border border-border shadow-sm hover:shadow-md hover:border-primary/20 transition-all group cursor-grab active:cursor-grabbing">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex flex-col">
                        <span className="font-semibold text-sm group-hover:text-primary transition-colors">{c.contactName}</span>
                        <span className="text-[10px] text-muted-foreground">{c.contactPhone}</span>
                      </div>
                      <button className="text-muted-foreground hover:text-foreground">
                        <MoreVertical className="w-4 h-4" />
                      </button>
                    </div>
                    
                    <p className="text-[11px] text-muted-foreground mb-4 line-clamp-2 leading-relaxed italic">"{c.lastMessage}"</p>
                    
                    <div className="flex items-center justify-between mb-4">
                       <div className="flex items-center gap-1.5">
                          <TrendingUp className="w-3 h-3 text-primary" />
                          <span className="text-[10px] font-bold">Score: {c.leadScore}</span>
                       </div>
                       <div className="flex items-center gap-1">
                         {[1, 2, 3].map(i => (
                           <Star key={i} className={`w-2.5 h-2.5 ${i <= (c.leadScore/30) ? 'text-yellow-500 fill-yellow-500' : 'text-muted'}`} />
                         ))}
                       </div>
                    </div>

                    <div className="pt-3 border-t border-border/50">
                      <select 
                        value={c.pipelineStage} 
                        onChange={(e) => onUpdateStage(c.id, e.target.value as PipelineStage)}
                        className="w-full text-[10px] font-bold bg-muted border border-border rounded-lg px-2 py-1.5 outline-none focus:ring-1 focus:ring-primary/30 transition-all appearance-none cursor-pointer"
                      >
                        {STAGES.map(s => <option key={s} value={s}>{t(`stage_${s}` as any)}</option>)}
                      </select>
                    </div>
                  </div>
                ))}
                
                {stageConvs.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-12 border-2 border-dashed border-border/40 rounded-xl opacity-40">
                    <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center mb-2">
                       <TrendingUp className="w-5 h-5" />
                    </div>
                    <p className="text-[10px] font-medium px-4 text-center leading-tight">{t('drop_here')}</p>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
