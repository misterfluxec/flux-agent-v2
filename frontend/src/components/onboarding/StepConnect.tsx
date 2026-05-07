import { useTranslations } from 'next-intl';
import { MessageSquare, Phone, Globe } from 'lucide-react';
import { OnboardingData } from '@/hooks/useOnboardingWizard';

interface Props {
  data: Pick<OnboardingData, 'channel' | 'phone'>;
  onChange: (field: keyof OnboardingData, value: string) => void;
  onNext: () => void;
  onBack: () => void;
}

export function StepConnect({ data, onChange, onNext, onBack }: Props) {
  const t = useTranslations('onboarding.connect');
  const channels = [
    { id: 'whatsapp', icon: MessageSquare, label: t('channel_wa') },
    { id: 'telegram', icon: Phone, label: t('channel_tg') },
    { id: 'web', icon: Globe, label: t('channel_web') },
  ];

  return (
    <div className="space-y-6 animate-in slide-in-from-bottom-4 fade-in duration-500">
      <div className="text-center space-y-2">
        <div className="inline-flex p-3 bg-primary/10 rounded-full mb-2"><MessageSquare className="w-6 h-6 text-primary" /></div>
        <h2 className="text-2xl font-bold">{t('title')}</h2>
        <p className="text-muted-foreground">{t('description')}</p>
      </div>
      <div className="space-y-5 max-w-md mx-auto">
        <div className="grid grid-cols-3 gap-3">
          {channels.map((ch) => (
            <button
              key={ch.id}
              onClick={() => onChange('channel', ch.id)}
              className={`flex flex-col items-center gap-2 p-4 rounded-xl border transition ${
                data.channel === ch.id ? 'border-primary bg-primary/10 shadow-sm' : 'border-border hover:bg-accent'
              }`}
            >
              <ch.icon className="w-6 h-6" />
              <span className="text-sm font-medium">{ch.label}</span>
            </button>
          ))}
        </div>
        {data.channel === 'whatsapp' && (
          <div className="animate-in slide-in-from-top-2 duration-300">
            <label className="block text-sm font-medium mb-2">{t('phone_label')}</label>
            <input
              type="tel"
              value={data.phone}
              onChange={(e) => onChange('phone', e.target.value.replace(/[^0-9+]/g, ''))}
              placeholder="+593 99 999 9999"
              className="w-full px-4 py-3 bg-card border border-border rounded-lg focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none transition"
            />
            <p className="text-xs text-muted-foreground mt-2">{t('phone_hint')}</p>
          </div>
        )}
      </div>
      <div className="flex gap-3 max-w-md mx-auto">
        <button onClick={onBack} className="flex-1 py-3 border border-border rounded-lg font-medium hover:bg-accent transition">{t('back')}</button>
        <button onClick={onNext} className="flex-1 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition">{t('next')}</button>
      </div>
    </div>
  );
}
