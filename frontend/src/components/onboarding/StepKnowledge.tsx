import { useTranslations } from 'next-intl';
import { Database, FileText, Globe, Upload } from 'lucide-react';
import { OnboardingData } from '@/hooks/useOnboardingWizard';

interface Props {
  data: Pick<OnboardingData, 'knowledgeSource' | 'knowledgeValue'>;
  onChange: (field: keyof OnboardingData, value: string) => void;
  onNext: () => void;
  onBack: () => void;
}

export function StepKnowledge({ data, onChange, onNext, onBack }: Props) {
  const t = useTranslations('onboarding.knowledge');
  const sources = [
    { id: 'manual', icon: Upload, label: t('source_manual') },
    { id: 'sheets', icon: FileText, label: t('source_sheets') },
    { id: 'website', icon: Globe, label: t('source_website') },
    { id: 'database', icon: Database, label: t('source_db') },
  ];

  return (
    <div className="space-y-6 animate-in slide-in-from-bottom-4 fade-in duration-500">
      <div className="text-center space-y-2">
        <div className="inline-flex p-3 bg-primary/10 rounded-full mb-2"><Database className="w-6 h-6 text-primary" /></div>
        <h2 className="text-2xl font-bold">{t('title')}</h2>
        <p className="text-muted-foreground">{t('description')}</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg mx-auto">
        {sources.map((src) => (
          <button
            key={src.id}
            onClick={() => onChange('knowledgeSource', src.id)}
            className={`flex items-center gap-3 p-4 rounded-xl border text-left transition ${
              data.knowledgeSource === src.id ? 'border-primary bg-primary/10 shadow-sm' : 'border-border hover:bg-accent'
            }`}
          >
            <src.icon className="w-5 h-5 text-muted-foreground" />
            <span className="font-medium">{src.label}</span>
          </button>
        ))}
      </div>

      <div className="max-w-lg mx-auto h-[60px]">
        {data.knowledgeSource === 'website' && (
          <div className="animate-in fade-in slide-in-from-top-2">
             <input
              type="url"
              placeholder="https://mi-empresa.com"
              value={data.knowledgeValue || ''}
              onChange={(e) => onChange('knowledgeValue', e.target.value)}
              className="w-full px-4 py-3 bg-card border border-border rounded-lg focus:ring-2 focus:ring-primary/50 outline-none transition"
             />
          </div>
        )}
        {data.knowledgeSource === 'manual' && (
          <div className="animate-in fade-in slide-in-from-top-2">
             <input
              type="file"
              accept=".pdf,.txt,.csv"
              onChange={(e) => onChange('knowledgeValue', e.target.files?.[0]?.name || '')}
              className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20 transition-all cursor-pointer"
             />
          </div>
        )}
        {data.knowledgeSource === 'sheets' && (
           <p className="text-sm text-muted-foreground text-center animate-in fade-in mt-2">Conectaremos tu Google Sheets en el dashboard tras finalizar.</p>
        )}
        {data.knowledgeSource === 'database' && (
           <p className="text-sm text-muted-foreground text-center animate-in fade-in mt-2">Configurarás las credenciales de tu base de datos desde Ajustes Avanzados.</p>
        )}
      </div>

      <div className="flex gap-3 max-w-lg mx-auto">
        <button onClick={onBack} className="flex-1 py-3 border border-border rounded-lg font-medium hover:bg-accent transition">{t('back')}</button>
        <button onClick={onNext} className="flex-1 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition">{t('next')}</button>
      </div>
    </div>
  );
}
