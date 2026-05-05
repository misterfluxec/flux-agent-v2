import { useTranslations } from 'next-intl';
import { User } from 'lucide-react';
import { OnboardingData } from '@/hooks/useOnboardingWizard';

interface Props {
  data: Pick<OnboardingData, 'name' | 'tone'>;
  onChange: (field: keyof OnboardingData, value: string) => void;
  onNext: () => void;
}

export function StepIdentity({ data, onChange, onNext }: Props) {
  const t = useTranslations('onboarding.identity');
  const isValid = data.name.trim().length >= 2;

  return (
    <div className="space-y-6 animate-in slide-in-from-bottom-4 fade-in duration-500">
      <div className="text-center space-y-2">
        <div className="inline-flex p-3 bg-primary/10 rounded-full mb-2"><User className="w-6 h-6 text-primary" /></div>
        <h2 className="text-2xl font-bold">{t('title')}</h2>
        <p className="text-muted-foreground">{t('description')}</p>
      </div>
      <div className="space-y-5 max-w-md mx-auto">
        <div>
          <label className="block text-sm font-medium mb-2">{t('name_label')}</label>
          <input
            type="text"
            value={data.name}
            onChange={(e) => onChange('name', e.target.value)}
            placeholder={t('name_placeholder')}
            className="w-full px-4 py-3 bg-card border border-border rounded-lg focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none transition"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-3">{t('tone_label')}</label>
          <div className="grid grid-cols-2 gap-3">
            {['profesional', 'amigable', 'tecnico', 'divertido'].map((tone) => (
              <button
                key={tone}
                onClick={() => onChange('tone', tone as any)}
                className={`p-3 rounded-lg border text-sm font-medium capitalize transition ${
                  data.tone === tone ? 'border-primary bg-primary/10 text-primary' : 'border-border hover:bg-accent'
                }`}
              >
                {t(`tone_${tone}` as any)}
              </button>
            ))}
          </div>
        </div>
      </div>
      <button onClick={onNext} disabled={!isValid} className="w-full py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition">
        {t('next')}
      </button>
    </div>
  );
}
