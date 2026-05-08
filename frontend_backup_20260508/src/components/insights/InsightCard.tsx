import { Lightbulb, AlertTriangle, TrendingDown, ArrowRight } from 'lucide-react';
import { AIInsight } from '@/types/insights';

export function InsightCard({ insight }: { insight: AIInsight }) {
  const getIcon = () => {
    switch (insight.type) {
      case 'stock_alert': return <AlertTriangle className="w-5 h-5 text-orange-500" />;
      case 'sentiment_drop': return <TrendingDown className="w-5 h-5 text-red-500" />;
      default: return <Lightbulb className="w-5 h-5 text-blue-500" />;
    }
  };

  return (
    <div className="bg-card border border-border rounded-2xl p-5 hover:border-primary/40 hover:shadow-lg transition-all relative overflow-hidden group">
      {insight.actionRequired && (
        <div className="absolute top-0 left-0 w-1.5 h-full bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.4)]" />
      )}
      <div className="flex items-start gap-4">
        <div className="p-3 bg-muted rounded-2xl group-hover:bg-primary/5 transition-colors shrink-0">
          {getIcon()}
        </div>
        <div className="space-y-2">
          <h4 className="font-bold text-sm text-foreground tracking-tight">{insight.title}</h4>
          <p className="text-xs text-muted-foreground leading-relaxed font-medium">{insight.message}</p>
          
          <div className="flex items-center justify-between pt-3">
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-16 bg-muted rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary rounded-full transition-all duration-1000" 
                  style={{ width: `${insight.confidence * 100}%` }} 
                />
              </div>
              <span className="text-[10px] text-muted-foreground font-black">
                {(insight.confidence * 100).toFixed(0)}%
              </span>
            </div>
            
            {insight.actionRequired && (
              <button className="flex items-center gap-1.5 text-[10px] font-black text-orange-500 hover:text-orange-600 uppercase tracking-widest transition-colors active:scale-95">
                Tomar Acción <ArrowRight className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
