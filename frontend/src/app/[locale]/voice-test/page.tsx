"use client";

import { VoiceTestClient } from '@/components/voice/VoiceTestClient';
import { useTenant } from '@/context/TenantContext';

export default function VoiceTestPage() {
  const { tenantId } = useTenant();

  return (
    <div className="min-h-screen bg-background flex flex-col items-center p-4 relative">
      <div className="w-full max-w-4xl bg-yellow-500/10 border border-yellow-500/20 text-yellow-500 p-3 mb-6 rounded-md text-center text-sm font-semibold flex items-center justify-center gap-2">
        <span className="bg-yellow-500 text-black px-2 py-0.5 rounded text-xs uppercase tracking-wider font-bold">Dev / Debug Only</span>
        Esta herramienta es exclusiva para diagnóstico de WebRTC/STT/TTS. Para producción, usa el Playground integrado en el Editor de Agentes.
      </div>
      <VoiceTestClient tenantId={tenantId || "00000000-0000-0000-0000-000000000000"} />
    </div>
  );
}

