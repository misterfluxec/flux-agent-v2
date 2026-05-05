import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';export type OnboardingData = {
  name: string;
  tone: 'profesional' | 'amigable' | 'tecnico' | 'divertido';
  knowledgeSource: 'manual' | 'sheets' | 'website' | 'database';
  knowledgeValue?: string; // For URL or File name
  behavior: 'ventas_agresivas' | 'soporte_tecnico' | 'reservas' | 'personalizado';
  channel: 'whatsapp' | 'telegram' | 'web';
  phone: string;
};

export function useOnboardingWizard() {
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [data, setData] = useState<OnboardingData>({
    name: '',
    tone: 'profesional',
    knowledgeSource: 'manual',
    knowledgeValue: '',
    behavior: 'ventas_agresivas',
    channel: 'whatsapp',
    phone: '',
  });

  const getSystemPromptForBehavior = (behavior: string) => {
    switch (behavior) {
      case 'ventas_agresivas':
        return "Actúa como un vendedor estrella ('Closer'). Tu objetivo es guiar la conversación rápidamente hacia el cierre de la venta. Haz preguntas de calificación, identifica los puntos de dolor del cliente y presenta nuestra solución de forma irresistible. Usa técnicas de urgencia y escasez cuando sea apropiado. Sé directo, persuasivo y muy proactivo.";
      case 'soporte_tecnico':
        return "Actúa como un ingeniero de soporte técnico empático y resolutivo. Escucha atentamente el problema del cliente, pide detalles específicos de forma ordenada y proporciona pasos claros para la resolución. Si no conoces la respuesta, no la inventes; indica que escalarás el problema. Mantén siempre la calma y un tono tranquilizador.";
      case 'reservas':
        return "Actúa como un conserje o agente de reservas altamente eficiente y cortés. Tu objetivo principal es ayudar al cliente a agendar una cita o reserva. Confirma siempre la fecha, hora y detalles relevantes. Sé servicial, ofrece alternativas si la opción deseada no está disponible y asegúrate de cerrar la confirmación de manera clara.";
      default:
        return "Actúa como un asistente versátil. Adapta tus respuestas a las necesidades del cliente, manteniendo un equilibrio entre amabilidad, eficiencia y proactividad para resolver sus dudas o dirigirlo al siguiente paso de su viaje.";
    }
  };

  const updateData = useCallback((updates: Partial<OnboardingData>) => {
    setData(prev => ({ ...prev, ...updates }));
  }, []);

  const nextStep = useCallback(() => setStep(prev => Math.min(prev + 1, 5)), []);
  const prevStep = useCallback(() => setStep(prev => Math.max(prev - 1, 1)), []);

  const submitOnboarding = useCallback(async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('flux_token');
      if (!token) throw new Error('No token found');

      const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.labodegaec.com";
      
      const payload = {
        nombre: data.name || 'Mi Primer Agente',
        area: 'Orquestador Principal',
        tono: data.tone,
        agent_type: data.behavior,
        system_prompt: getSystemPromptForBehavior(data.behavior),
        canales: [data.channel],
        // In a real scenario, the phone is linked via WhatsApp Cloud API setup later, 
        // but we start the configuration here.
      };

      const res = await fetch(`${BACKEND_URL}/api/v1/agents`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        console.error('API Error:', errData);
        throw new Error('Failed to create agent');
      }

      // Mark onboarding complete
      if (typeof window !== 'undefined') {
        localStorage.setItem('onboarding_complete', 'true');
        document.cookie = "onboarding_complete=true; path=/; max-age=31536000";
        
        const segments = window.location.pathname.split('/');
        const locale = segments[1];
        const isLocale = ['en', 'es', 'pt'].includes(locale);
        
        const dashboardPath = isLocale ? `/${locale}/dashboard` : '/dashboard';
        window.location.href = dashboardPath;
      }
    } catch (error) {
      console.error('Onboarding failed:', error);
      // Even if API fails (e.g. backend not fully set up), we might want to let them in for testing
      // but in production, we should show a toast error.
      alert("Hubo un problema configurando el agente. Intenta de nuevo.");
    } finally {
      setIsLoading(false);
    }
  }, [data]);

  return { step, data, isLoading, updateData, nextStep, prevStep, submitOnboarding };
}
