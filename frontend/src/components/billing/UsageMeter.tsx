import { MessageSquare, Bot, Database } from 'lucide-react';

const ICONS = { message: MessageSquare, bot: Bot, database: Database };

export function UsageMeter({ label, used, limit, icon, unit = '' }: { label: string; used: number; limit: number; icon: keyof typeof ICONS; unit?: string }) {
  const percent = Math.min(100, (used / limit) * 100);
  const isWarning = percent >= 80;
  const isCritical = percent >= 95;
  const Icon = ICONS[icon];

  return (
    <div className="bg-card border border-border rounded-xl p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <div className={`p-1.5 rounded-lg ${isCritical ? 'bg-red-500/10 text-red-500' : isWarning ? 'bg-yellow-500/10 text-yellow-500' : 'bg-primary/10 text-primary'}`}>
            <Icon className="w-4 h-4" />
          </div>
          {label}
        </div>
        <span className={`text-xs font-bold ${isCritical ? 'text-red-500' : isWarning ? 'text-yellow-500' : 'text-primary'}`}>
          {used}{unit} / {limit}{unit}
        </span>
      </div>
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div 
          className={`h-full transition-all duration-1000 ease-out rounded-full ${
            isCritical ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.4)]' : 
            isWarning ? 'bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.4)]' : 
            'bg-primary shadow-[0_0_8px_rgba(59,130,246,0.4)]'
          }`} 
          style={{ width: `${percent}%` }} 
        />
      </div>
      <div className="flex justify-between mt-2">
         <span className="text-[10px] text-muted-foreground font-medium">{percent.toFixed(0)}% Utilizado</span>
         {isWarning && (
           <p className="text-[10px] font-bold animate-pulse text-yellow-500">
             {isCritical ? '⚠️ Límite crítico' : '⚠️ Cerca del límite'}
           </p>
         )}
      </div>
    </div>
  );
}
