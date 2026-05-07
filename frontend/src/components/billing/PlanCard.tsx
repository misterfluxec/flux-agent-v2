import { Check, Star } from 'lucide-react';
import { Plan } from '@/types/billing';

export function PlanCard({ plan, isCurrent, onSelect }: { plan: Plan; isCurrent: boolean; onSelect: (id: string) => void }) {
  const isEnterprise = plan.id === 'enterprise';
  const isPro = plan.id === 'pro';

  return (
    <div className={`relative border rounded-2xl p-6 flex flex-col transition-all duration-300 ${
      isCurrent 
      ? 'border-primary bg-primary/5 ring-1 ring-primary/20 scale-[1.02]' 
      : 'border-border bg-card hover:border-primary/40 hover:shadow-lg'
    }`}>
      {isPro && !isCurrent && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-[10px] font-bold px-3 py-1 rounded-full shadow-md uppercase tracking-wider">
          Recomendado
        </div>
      )}

      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="font-bold text-xl">{plan.name}</h3>
          <p className="text-xs text-muted-foreground mt-1">Ideal para {
            plan.id === 'starter' ? 'emprendedores' : 
            plan.id === 'pro' ? 'negocios en crecimiento' : 'grandes empresas'
          }</p>
        </div>
        {isCurrent && (
          <div className="bg-primary/20 text-primary p-1 rounded-full">
            <Star className="w-4 h-4 fill-primary" />
          </div>
        )}
      </div>

      <div className="mb-6">
        <div className="flex items-baseline gap-1">
          <span className="text-4xl font-black">${plan.price}</span>
          <span className="text-muted-foreground text-sm font-medium">/{plan.interval === 'month' ? 'mes' : 'año'}</span>
        </div>
      </div>

      <div className="space-y-4 mb-8 flex-1">
        <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground/60">¿Qué incluye?</p>
        <ul className="space-y-3">
          {plan.features.map((f, i) => (
            <li key={i} className="flex items-start gap-3 text-sm text-foreground/80">
              <div className="mt-0.5 w-4 h-4 rounded-full bg-green-500/10 flex items-center justify-center shrink-0">
                <Check className="w-2.5 h-2.5 text-green-500" strokeWidth={3} />
              </div> 
              {f}
            </li>
          ))}
        </ul>
      </div>

      <button 
        onClick={() => onSelect(plan.id)} 
        disabled={isCurrent}
        className={`w-full py-3 rounded-xl font-bold text-sm transition-all shadow-sm ${
          isCurrent 
          ? 'bg-muted text-muted-foreground cursor-not-allowed' 
          : isEnterprise 
            ? 'bg-secondary text-secondary-foreground hover:bg-secondary/90'
            : 'bg-primary text-primary-foreground hover:bg-primary/90 hover:shadow-md active:scale-95'
        }`}
      >
        {isCurrent ? 'Plan Actual' : isEnterprise ? 'Contactar Ventas' : 'Actualizar Ahora'}
      </button>
    </div>
  );
}
