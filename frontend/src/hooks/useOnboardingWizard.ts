import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api/axios';

export interface OnboardingData {
  nombre: string;
  avatar: string | null;
  industria: string;
  conocimiento_cargado: boolean;
  whatsapp_conectado: boolean;
}

const DEFAULT_DATA: OnboardingData = {
  nombre: 'Yanua',
  avatar: null,
  industria: '',
  conocimiento_cargado: false,
  whatsapp_conectado: false,
};

export function useOnboardingWizard() {
  const [step, setStep] = useState(1);
  const [data, setData] = useState<OnboardingData>(DEFAULT_DATA);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const updateData = (updates: Partial<OnboardingData>) => {
    setData((prev) => ({ ...prev, ...updates }));
  };

  const nextStep = () => {
    setStep((prev) => Math.min(prev + 1, 5));
  };

  const prevStep = () => {
    setStep((prev) => Math.max(prev - 1, 1));
  };

  const submitOnboarding = async () => {
    setIsLoading(true);
    try {
      // Magia Backend: Autoconfiguración inteligente según industria
      // Mapeamos la industria seleccionada al tipo de agente y el prompt predeterminado
      let agentType = "sales";
      if (data.industria === "clinica" || data.industria === "educacion") agentType = "bookings";
      if (data.industria === "tecnologia" || data.industria === "seguridad") agentType = "support";

      const payload = {
        nombre: data.nombre || 'Yanua',
        descripcion: `Agente especializado en la industria: ${data.industria}`,
        agent_type: agentType,
        specialty: data.industria,
        canales: ["web_chat", "whatsapp"]
      };

      await api.post('/agents', payload);
      
      // Una vez creado, ir al dashboard de activación
      router.push('/dashboard');
    } catch (error) {
      console.error('Error finalizando el onboarding:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    step,
    data,
    isLoading,
    updateData,
    nextStep,
    prevStep,
    submitOnboarding,
  };
}
