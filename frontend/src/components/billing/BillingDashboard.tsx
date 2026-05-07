'use client';
import { useTranslations } from 'next-intl';
import { CreditCard, TrendingUp, AlertTriangle, Shield, CheckCircle, ArrowRight } from 'lucide-react';
import { UsageMeter } from './UsageMeter';
import { PlanCard } from './PlanCard';
import { PLANS, Subscription, UsageMetrics } from '@/types/billing';

interface Props {
  subscription: Subscription;
  usage: UsageMetrics;
  currentPlanId: string;
  onUpgrade: (planId: string) => void;
  onManageBilling: () => void;
}

export function BillingDashboard({ subscription, usage, currentPlanId, onUpgrade, onManageBilling }: Props) {
  const t = useTranslations('billing');
  const isPastDue = subscription.status === 'past_due';
  const currentPlan = PLANS.find(p => p.id === currentPlanId)!;

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      {/* Header Informativo */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h1 className="text-3xl font-black tracking-tight">Facturación</h1>
          <p className="text-muted-foreground mt-2">Gestiona tu suscripción, métodos de pago y revisa tu consumo mensual.</p>
        </div>
        <div className="bg-primary/5 border border-primary/20 px-4 py-2 rounded-2xl flex items-center gap-3">
           <TrendingUp className="w-5 h-5 text-primary" />
           <div>
             <p className="text-[10px] font-bold uppercase tracking-widest text-primary/70 leading-none">Estado de Cuenta</p>
             <p className="text-sm font-bold text-primary">{t('status_' + subscription.status as any)}</p>
           </div>
        </div>
      </div>

      {/* Alerta de Pago Pendiente */}
      {isPastDue && (
        <div className="bg-destructive/10 border border-destructive/20 rounded-2xl p-5 flex items-start gap-4 animate-in fade-in slide-in-from-top-4 duration-500">
          <div className="bg-destructive/20 p-2 rounded-full">
            <AlertTriangle className="w-6 h-6 text-destructive" />
          </div>
          <div className="flex-1">
            <h3 className="font-bold text-destructive text-lg leading-none">{t('payment_failed_title')}</h3>
            <p className="text-sm text-foreground/70 mt-2">{t('payment_failed_desc')}</p>
            <button onClick={onManageBilling} className="mt-4 flex items-center gap-2 bg-destructive text-destructive-foreground px-4 py-2 rounded-xl text-sm font-bold hover:bg-destructive/90 transition shadow-md">
              <CreditCard className="w-4 h-4" /> {t('update_payment')} <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Métricas de Uso */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <UsageMeter label={t('messages')} used={usage.messagesUsed} limit={usage.messagesLimit} icon="message" />
        <UsageMeter label={t('agents')} used={usage.agentsUsed} limit={usage.agentsLimit} icon="bot" />
        <UsageMeter label={t('storage')} used={usage.storageUsedGB} limit={usage.storageLimitGB} icon="database" unit="GB" />
      </div>

      {/* Plan Actual & Acciones Rápidas */}
      <div className="bg-card border border-border rounded-2xl p-8 relative overflow-hidden shadow-sm group">
        <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-bl-full -mr-10 -mt-10 transition-transform group-hover:scale-110" />
        <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div className="flex items-center gap-6">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center text-white shadow-lg">
               <Shield className="w-8 h-8" />
            </div>
            <div>
              <h2 className="text-2xl font-black">{currentPlan.name} Plan</h2>
              <p className="text-muted-foreground text-sm mt-1 font-medium">
                {subscription.status === 'active' 
                  ? t('active_until', { date: new Date(subscription.currentPeriodEnd).toLocaleDateString() }) 
                  : t('status_' + subscription.status as any)}
              </p>
            </div>
          </div>
          <div className="flex w-full md:w-auto gap-3">
            <button onClick={onManageBilling} className="flex-1 md:flex-none px-6 py-3 border border-border rounded-xl text-sm font-bold hover:bg-accent transition-all flex items-center justify-center gap-2">
              <CreditCard className="w-4 h-4" /> {t('manage_billing')}
            </button>
            <button onClick={() => onUpgrade('pro')} className="flex-1 md:flex-none px-6 py-3 bg-primary text-primary-foreground rounded-xl text-sm font-bold hover:bg-primary/90 transition-all shadow-md active:scale-95">
              {t('upgrade')}
            </button>
          </div>
        </div>
      </div>

      {/* Comparativa de Planes */}
      <div className="pt-8">
        <div className="text-center mb-10">
          <h3 className="text-2xl font-black mb-2">{t('compare_plans')}</h3>
          <p className="text-muted-foreground">Escala tu negocio con el plan que mejor se adapte a tus necesidades.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {PLANS.map(plan => (
            <PlanCard 
              key={plan.id} 
              plan={plan} 
              isCurrent={plan.id === currentPlanId} 
              onSelect={onUpgrade} 
            />
          ))}
        </div>
      </div>

      {/* Seguridad & Cumplimiento */}
      <div className="bg-muted/30 border border-border rounded-2xl p-8 mt-12 relative overflow-hidden">
        <div className="absolute top-4 right-4 opacity-5">
           <Shield className="w-24 h-24" />
        </div>
        <h3 className="text-lg font-bold flex items-center gap-2 mb-6">
          <div className="w-8 h-8 rounded-lg bg-green-500/10 flex items-center justify-center">
            <Shield className="w-5 h-5 text-green-500" />
          </div>
          {t('security_compliance')}
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { key: 'encryption', desc: 'AES-256 Bit' },
            { key: 'gdpr', desc: 'Data Privacy' },
            { key: 'whatsapp_compliance', desc: 'Meta Approved' },
            { key: 'audit_logs', desc: 'Immutable Logs' }
          ].map(item => (
            <div key={item.key} className="flex flex-col gap-1 p-4 rounded-xl bg-card border border-border/50">
              <div className="flex items-center gap-2 font-bold text-sm text-foreground">
                <CheckCircle className="w-4 h-4 text-green-500" />
                {t(item.key as any)}
              </div>
              <p className="text-[10px] text-muted-foreground ml-6 uppercase tracking-widest font-bold">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
