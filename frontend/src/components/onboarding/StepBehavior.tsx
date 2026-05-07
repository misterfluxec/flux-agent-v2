import { useTranslations } from 'next-intl';
import { Shield, Zap, Calendar, Sliders } from 'lucide-react';
import { OnboardingData } from '@/hooks/useOnboardingWizard';

interface Props {
  data: Pick<OnboardingData, 'behavior'>;
  onChange: (field: keyof OnboardingData, value: string) => void;
  onNext: () => void;
  onBack: () => void;
}

export function StepBehavior({ data, onChange, onNext, onBack }: Props) {
  const t = useTranslations('onboarding.behavior');
  const behaviors = [
    { id: 'ventas_agresivas', icon: Zap, label: t('behavior_sales') },
    { id: 'soporte_tecnico', icon: Shield, label: t('behavior_support') },
    { id: 'reservas', icon: Calendar, label: t('behavior_bookings') },
    { id: 'personalizado', icon: Sliders, label: t('behavior_custom') },
  ];

  return (
    <div className="space-y-6 animate-in slide-in-from-bottom-4 fade-in duration-500">
      <div className="text-center space-y-2">
        <div className="inline-flex p-3 bg-primary/10 rounded-full mb-2"><Zap className="w-6 h-6 text-primary" /></div>
        <h2 className="text-2xl font-bold">{t('title')}</h2>
        <p className="text-muted-foreground">{t('description')}</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg mx-auto">
        {behaviors.map((b) => (
          <button
            key={b.id}
            onClick={() => onChange('behavior', b.id)}
            className={`flex items-center gap-3 p-4 rounded-xl border text-left transition ${
              data.behavior === b.id ? 'border-primary bg-primary/10 shadow-sm' : 'border-border hover:bg-accent'
            }`}
          >
            <b.icon className="w-5 h-5 text-muted-foreground" />
            <span className="font-medium">{b.label}</span>
          </button>
        ))}
      </div>
      <div className="flex gap-3 max-w-lg mx-auto">
        <button onClick={onBack} className="flex-1 py-3 border border-border rounded-lg font-medium hover:bg-accent transition">{t('back')}</button>
        <button onClick={onNext} className="flex-1 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition">{t('next')}</button>
      </div>
    </div>
  );
}
