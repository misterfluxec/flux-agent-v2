import { useState, useEffect, useRef, useCallback } from 'react';
import { useForm, UseFormReturn } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { toast } from 'sonner';

// ==========================================
// SCHEMAS (zod)
// ==========================================
export const wizardSchema = z.object({
  sourceType: z.enum(['file', 'web', 'database']),
  file: z.any().optional(),
  url: z.string().optional().or(z.literal('')),
  mapping: z.any().optional(),
  syncEnabled: z.boolean().optional(),
  syncFrequency: z.enum(['hourly', 'daily', 'weekly', 'monthly']).optional(),
});

export type WizardFormData = z.infer<typeof wizardSchema>;

// ==========================================
// WEBSOCKET INTERFACES
// ==========================================
export interface WebSocketMessage {
  task_id: string;
  step: 'pending' | 'parsing' | 'chunking' | 'embedding' | 'indexing' | 'completado' | 'error' | string;
  percentage: number;
  message: string;
  timestamp: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
}

export interface IngestionProgress {
  percentage: number;
  currentStep: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
}

// ==========================================
// HOOK
// ==========================================
export function useIngestionWizard(tenantId: string) {
  const [currentStep, setCurrentStep] = useState(1);
  const [taskId, setTaskId] = useState<string | null>(null);
  
  // WS State
  const [progress, setProgress] = useState<IngestionProgress>({
    percentage: 0,
    currentStep: 'pending',
    status: 'pending'
  });
  const [logs, setLogs] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Form State
  const form = useForm<WizardFormData>({
    resolver: zodResolver(wizardSchema),
    defaultValues: {
      sourceType: 'file',
      syncEnabled: false,
    },
    mode: 'onChange'
  });

  // ==========================================
  // NAVIGATION
  // ==========================================
  const nextStep = async () => {
    // Validar paso actual antes de avanzar
    let isValid = true;
    if (currentStep === 1) {
      isValid = await form.trigger('sourceType');
    } else if (currentStep === 2) {
      const type = form.getValues('sourceType');
      if (type === 'file') {
        const file = form.getValues('file');
        if (!file) {
          form.setError('file', { type: 'manual', message: 'Archivo es requerido' });
          isValid = false;
        } else {
          form.clearErrors('file');
        }
      }
      if (type === 'web') isValid = await form.trigger('url');
    }
    
    if (isValid && currentStep < 6) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const jumpToStep = (step: number) => {
    if (step < currentStep) {
      setCurrentStep(step);
    }
  };

  const resetWizard = () => {
    form.reset();
    setCurrentStep(1);
    setTaskId(null);
    setProgress({ percentage: 0, currentStep: 'pending', status: 'pending' });
    setLogs([]);
  };

  // ==========================================
  // WEBSOCKET CONNECTION (Paso 5)
  // ==========================================
  const connectWebSocket = useCallback((targetTenantId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    // Obtener la URL WS correcta (maneja dev y prod)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Asumiendo que la API está en el mismo host o manejado por proxy de NextJS
    // En el docker compose backend está en el puerto 8000
    // Usamos la URL del backend
    const wsBaseUrl = process.env.NEXT_PUBLIC_BACKEND_URL 
      ? process.env.NEXT_PUBLIC_BACKEND_URL.replace('http', 'ws')
      : `${protocol}//${window.location.host}`;
      
    const wsUrl = `${wsBaseUrl}/api/v1/ingest/ws/ingestion/${targetTenantId}`;
    
    console.log("Connecting WS to:", wsUrl);
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WS Connected');
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };

    ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        setProgress({
          percentage: data.percentage || 0,
          currentStep: data.step || 'processing',
          status: data.status || 'processing'
        });
        
        if (data.message) {
          setLogs(prev => {
            // Evitar duplicados consecutivos exactos
            if (prev[prev.length - 1] === data.message) return prev;
            return [...prev, data.message];
          });
        }

        if (data.status === 'completed') {
          toast.success("Ingesta completada con éxito");
          // Avanzar automáticamente al paso 6 tras un breve delay
          setTimeout(() => setCurrentStep(6), 1500);
        } else if (data.status === 'error') {
          toast.error("Error durante la ingesta: " + data.message);
        }
      } catch (error) {
        console.error('Error parsing WS message', error);
      }
    };

    ws.onclose = () => {
      console.log('WS Disconnected, retrying...');
      // Simple backoff
      reconnectTimeoutRef.current = setTimeout(() => {
        if (currentStep === 5) {
          connectWebSocket(targetTenantId);
        }
      }, 2000);
    };

    ws.onerror = (error) => {
      console.error('WS Error:', error);
      ws.close();
    };

    wsRef.current = ws;
  }, [currentStep]);

  useEffect(() => {
    if (currentStep === 5 && tenantId) {
      connectWebSocket(tenantId);
    }
    
    return () => {
      if (currentStep !== 5 && wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [currentStep, tenantId, connectWebSocket]);

  // ==========================================
  // API CALLS
  // ==========================================
  const startIngestion = async () => {
    const data = form.getValues();
    
    try {
      const agentId = localStorage.getItem('flux_agent_id') || undefined;
      let resData;
      
      if (data.sourceType === 'file' && data.file) {
        // Usar la función centralizada api.ts para evitar errores de CORS y URL
        const { uploadDocument } = await import('@/lib/api');
        resData = await uploadDocument(data.file, agentId);
      } else if (data.sourceType === 'web' && data.url) {
        const { ingestUrl } = await import('@/lib/api');
        resData = await ingestUrl(data.url, agentId);
      } else {
        throw new Error('No hay datos válidos para la ingesta');
      }

      setTaskId(resData.job_id);
      
      // Pasar al paso 5 (Processing)
      setCurrentStep(5);
      toast.success("Proceso iniciado en background");
      
    } catch (error: any) {
      console.error("Error starting ingestion:", error);
      toast.error(error.message || "Error al conectar con el servidor");
    }
  };

  return {
    form,
    currentStep,
    nextStep,
    prevStep,
    jumpToStep,
    resetWizard,
    startIngestion,
    progress,
    logs,
    taskId
  };
}
