'use client';
import { useTranslations } from 'next-intl';
import { TrendingUp, Users, ShoppingCart, DollarSign, ArrowUpRight, ArrowDownRight, Target, Zap } from 'lucide-react';
import { MOCK_ROI } from '@/types/connectors';

export default function AnalyticsPage() {
  const t = useTranslations('analytics');
  const m = MOCK_ROI;

  const metrics = [
    { label: t('conversations'), value: m.conversations, icon: MessageSquare, trend: m.trend, color: 'text-blue-500' },
    { label: t('leads'), value: m.qualifiedLeads, icon: Target, trend: m.trend - 2, color: 'text-purple-500' },
    { label: t('sales'), value: m.salesAttributed, icon: ShoppingCart, trend: m.trend + 1.5, color: 'text-orange-500' },
    { label: t('revenue'), value: `$${m.revenueAttributed.toLocaleString()}`, icon: DollarSign, trend: m.trend + 3.2, color: 'text-green-500' },
  ];

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      <div className="flex flex-col md:flex-row items-start md:items-end justify-between gap-4">
        <div>
           <h1 className="text-3xl font-black tracking-tight">{t('title')}</h1>
           <p className="text-muted-foreground mt-1">Mide el impacto real de tu agente en tus ventas y captación de clientes.</p>
        </div>
        <div className="bg-primary/5 border border-primary/20 px-4 py-2 rounded-2xl flex items-center gap-3">
           <Zap className="w-5 h-5 text-primary fill-primary/20" />
           <div>
             <p className="text-[10px] font-bold uppercase tracking-widest text-primary/70 leading-none">Cálculo de ROI</p>
             <p className="text-sm font-bold text-primary">Actualizado hace 2 min</p>
           </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((met, i) => (
          <div key={i} className="bg-card border border-border rounded-2xl p-6 shadow-sm hover:shadow-md transition-all">
            <div className="flex items-center justify-between mb-4">
              <div className={`p-2 rounded-xl bg-muted group-hover:scale-110 transition-transform`}>
                <met.icon className={`w-5 h-5 ${met.color}`} />
              </div>
              <div className={`flex items-center gap-1 text-[10px] font-black uppercase tracking-tighter ${met.trend >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {met.trend >= 0 ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                {Math.abs(met.trend)}%
              </div>
            </div>
            <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest">{met.label}</p>
            <p className="text-3xl font-black mt-1 tracking-tight">{met.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Embudo de Conversión */}
        <div className="lg:col-span-2 bg-card border border-border rounded-3xl p-8 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full -mr-20 -mt-20 blur-3xl" />
          <h3 className="text-xl font-black mb-8 flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-primary" />
            {t('conversion_funnel')}
          </h3>
          <div className="space-y-6 relative z-10">
            <div className="flex items-center gap-4 group">
              <div className="flex-1">
                 <div className="flex justify-between items-end mb-2">
                    <span className="text-xs font-bold text-muted-foreground uppercase">{t('visitors')}</span>
                    <span className="text-sm font-black">4,200</span>
                 </div>
                 <div className="h-4 bg-muted rounded-full overflow-hidden">
                    <div className="h-full w-full bg-muted-foreground/20 rounded-full" />
                 </div>
              </div>
            </div>

            <div className="flex items-center gap-4 group">
              <div className="flex-1 ml-8">
                 <div className="flex justify-between items-end mb-2">
                    <span className="text-xs font-bold text-primary uppercase">{t('chats')}</span>
                    <span className="text-sm font-black text-primary">1,240 <span className="text-[10px] opacity-60 ml-1">({((1240/4200)*100).toFixed(1)}%)</span></span>
                 </div>
                 <div className="h-4 bg-primary/20 rounded-full overflow-hidden">
                    <div className="h-full w-[29.5%] bg-primary rounded-full shadow-[0_0_12px_rgba(59,130,246,0.5)]" />
                 </div>
              </div>
            </div>

            <div className="flex items-center gap-4 group">
              <div className="flex-1 ml-16">
                 <div className="flex justify-between items-end mb-2">
                    <span className="text-xs font-bold text-green-500 uppercase">{t('sales')}</span>
                    <span className="text-sm font-black text-green-500">94 <span className="text-[10px] opacity-60 ml-1">({((94/1240)*100).toFixed(1)}%)</span></span>
                 </div>
                 <div className="h-4 bg-green-500/20 rounded-full overflow-hidden">
                    <div className="h-full w-[7.6%] bg-green-500 rounded-full shadow-[0_0_12px_rgba(34,197,94,0.5)]" />
                 </div>
              </div>
            </div>
          </div>
          <p className="text-center text-[10px] font-bold text-muted-foreground/60 mt-10 uppercase tracking-[0.2em]">{t('funnel_note')}</p>
        </div>

        {/* Card Lateral con Insight */}
        <div className="bg-gradient-to-br from-primary to-blue-700 rounded-3xl p-8 text-white flex flex-col justify-between shadow-xl shadow-primary/20">
           <div className="space-y-6">
              <div className="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur-md">
                 <TrendingUp className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-2xl font-black leading-tight">Tu Agente se está pagando solo.</h4>
                <p className="text-white/70 text-sm mt-4 leading-relaxed">
                  Con una tasa de conversión del <b>7.6%</b>, FluxAgent ha generado un retorno de <b>12x</b> sobre el costo de tu suscripción este mes.
                </p>
              </div>
           </div>
           <button className="w-full py-4 bg-white text-primary rounded-2xl font-bold text-sm shadow-lg hover:bg-opacity-90 transition-all active:scale-95 mt-12">
             Ver Reporte Detallado
           </button>
        </div>
      </div>
    </div>
  );
}

// Helper icons needed for metrics
const MessageSquare = (props: any) => (
  <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
)
