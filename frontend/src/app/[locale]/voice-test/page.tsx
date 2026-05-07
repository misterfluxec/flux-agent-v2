import { VoiceTestClient } from '@/components/voice/VoiceTestClient';
import { getTranslations } from 'next-intl/server';

export async function generateMetadata({ params: { locale } }: { params: { locale: string } }) {
  const t = await getTranslations({ locale, namespace: 'voice' });
  return {
    title: t('page_title'),
    description: t('page_description')
  };
}

export default function VoiceTestPage({ params: { locale } }: { params: { locale: string } }) {
  // En producción, obtener tenant_id desde sesión/auth
  const tenantId = 'demo-tenant-id'; // Reemplazar con lógica real

  return (
    <div className="min-h-screen bg-background flex flex-col items-center p-4 relative">
      <div className="w-full max-w-4xl bg-yellow-500/10 border border-yellow-500/20 text-yellow-500 p-3 mb-6 rounded-md text-center text-sm font-semibold flex items-center justify-center gap-2">
        <span className="bg-yellow-500 text-black px-2 py-0.5 rounded text-xs uppercase tracking-wider font-bold">Dev / Debug Only</span>
        Esta herramienta es exclusiva para diagnóstico de WebRTC/STT/TTS. Para producción, usa el Playground integrado en el Editor de Agentes.
      </div>
      <VoiceTestClient tenantId={tenantId} />
    </div>
  );
}
