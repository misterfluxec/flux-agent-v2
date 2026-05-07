import { useTranslations } from 'next-intl';
import { CheckCircle, Loader2 } from 'lucide-react';

interface Props {
  isLoading: boolean;
  onSubmit: () => void;
}

export function StepComplete({ isLoading, onSubmit }: Props) {
  const t = useTranslations('onboarding.complete');
  return (
    <div className="space-y-6 text-center max-w-md mx-auto animate-in zoom-in-95 fade-in duration-500">
      <div className="inline-flex p-4 bg-green-500/10 rounded-full mb-2">
        {isLoading ? <Loader2 className="w-8 h-8 text-primary animate-spin" /> : <CheckCircle className="w-8 h-8 text-green-500" />}
      </div>
      <h2 className="text-2xl font-bold">{t('title')}</h2>
      <p className="text-muted-foreground">{t('description')}</p>
      {!isLoading && (
        <button onClick={onSubmit} className="w-full py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 shadow-lg shadow-primary/20 transition hover:scale-[1.02]">
          {t('start')}
        </button>
      )}
      {isLoading && (
        <div className="space-y-2 mt-4">
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div className="h-full bg-primary animate-progress w-full" />
          </div>
          <p className="text-xs text-muted-foreground animate-pulse">{t('loading')}</p>
        </div>
      )}
    </div>
  );
}
