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
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <VoiceTestClient tenantId={tenantId} />
    </div>
  );
}
