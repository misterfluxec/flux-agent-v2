"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  ReactNode,
} from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateAgent, AgentUpdate, AgentResponse } from "@/lib/api/agents";
import { toast } from "sonner"; // o tu librería de toasts preferida

// =============================================================================
// TIPOS Y ESTADO
// =============================================================================

/**
 * Estado acumulado de cambios pendientes para guardado atómico
 * Permite que múltiples tabs registren cambios antes de enviar 1 PUT
 */
interface PendingChanges {
  [field: string]: any;
}

/**
 * Contexto compartido para edición de agente
 * Expone status + acciones para todos los componentes hijos
 */
interface AgentEditContextValue {
  // Estado
  agentId: string | null;
  pendingChanges: PendingChanges;
  hasUnsavedChanges: boolean;
  isSaving: boolean;

  // Acciones
  setAgentId: (id: string | null) => void;
  registerField: <K extends keyof AgentUpdate>(field: K, value: AgentUpdate[K]) => void;
  registerBulkChanges: (changes: Partial<AgentUpdate>) => void;
  discardChanges: () => void;
  triggerSave: () => Promise<boolean>;
  
  // Metadata
  lastSavedAt: Date | null;
  saveError: Error | null;
}

// =============================================================================
// CREACIÓN DEL CONTEXTO
// =============================================================================

const AgentEditContext = createContext<AgentEditContextValue | undefined>(undefined);

/**
 * Provider que envuelve la página /dashboard/agent
 * Maneja status compartido entre tabs + lógica de guardado atómico
 * 
 * @example
 * <AgentEditProvider initialAgentId="uuid">
 *   <AgentEditor />
 * </AgentEditProvider>
 */
export function AgentEditProvider({
  children,
  initialAgentId,
}: {
  children: ReactNode;
  initialAgentId?: string;
}) {
  const queryClient = useQueryClient();
  
  // Estado local del contexto
  const [agentId, setAgentId] = useState<string | null>(initialAgentId ?? null);
  const [pendingChanges, setPendingChanges] = useState<PendingChanges>({});
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [saveError, setSaveError] = useState<Error | null>(null);

  // 🔑 Mutación para guardar cambios en backend (con invalidación de cache)
  const saveMutation = useMutation<{ mensaje: string }, Error, { agentId: string; changes: Partial<AgentUpdate> }>({
    mutationFn: ({ agentId, changes }) => updateAgent(agentId, changes),
    onSuccess: (data, variables) => {
      // Invalidar cache del agente específico
      queryClient.invalidateQueries({ queryKey: ["agent", variables.agentId] });
      
      // Invalidar analytics si los cambios pueden afectar métricas
      const metricsAffectedFields = ["agent_type", "system_prompt", "sales_script", "model", "channels", "temperature"];
      const hasMetricsImpact = Object.keys(variables.changes).some(field => 
        metricsAffectedFields.includes(field)
      );
      if (hasMetricsImpact) {
        queryClient.invalidateQueries({ queryKey: ["analytics"] });
      }
      
      // Actualizar status local
      setPendingChanges({});
      setLastSavedAt(new Date());
      setSaveError(null);
      
      // Feedback al usuario
      toast.success("✅ Cambios guardados correctamente", {
        duration: 3000,
        position: "top-right",
      });
    },
    onError: (error, variables) => {
      setSaveError(error);
      toast.error("❌ Error al guardar cambios", {
        description: error.message,
        duration: 5000,
        position: "top-right",
        action: {
          label: "Reintentar",
          onClick: () => triggerSave(),
        },
      });
    },
  });

  // =============================================================================
  // ACCIONES EXPUESTAS (para usar en tabs y componentes hijos)
  // =============================================================================

  /**
   * Registrar un cambio individual (usado por inputs en tabs)
   * Ej: registerField('name', 'Nuevo Nombre')
   */
  const registerField = useCallback(<K extends keyof AgentUpdate>(
    field: K,
    value: AgentUpdate[K]
  ) => {
    setPendingChanges(prev => ({
      ...prev,
      [field]: value,
    }));
  }, []);

  /**
   * Registrar múltiples cambios a la vez (usado por formularios complejos)
   * Ej: registerBulkChanges({ name: 'X', tone: 'profesional' })
   */
  const registerBulkChanges = useCallback((changes: Partial<AgentUpdate>) => {
    setPendingChanges(prev => ({
      ...prev,
      ...changes,
    }));
  }, []);

  /**
   * Descartar todos los cambios pendientes
   * Útil para botón "Cancelar" o navegación sin guardar
   */
  const discardChanges = useCallback(() => {
    setPendingChanges({});
    setSaveError(null);
    toast.info("🗑️ Cambios descartados", {
      duration: 2000,
      position: "top-right",
    });
  }, []);

  /**
   * Disparar guardado de todos los cambios acumulados
   * @returns Promise<boolean> - true si éxito, false si error
   */
  const triggerSave = useCallback(async (): Promise<boolean> => {
    if (!agentId) {
      toast.error("⚠️ No hay agente seleccionado", {
        position: "top-right",
      });
      return false;
    }
    
    if (Object.keys(pendingChanges).length === 0) {
      toast.info("ℹ️ No hay cambios pendientes para guardar", {
        position: "top-right",
      });
      return true;
    }

    try {
      await saveMutation.mutateAsync({
        agentId,
        changes: pendingChanges,
      });
      return true;
    } catch {
      return false;
    }
  }, [agentId, pendingChanges, saveMutation]);

  // =============================================================================
  // VALOR DEL CONTEXTO (exportado para consumo)
  // =============================================================================

  const value: AgentEditContextValue = {
    // Estado
    agentId,
    pendingChanges,
    hasUnsavedChanges: Object.keys(pendingChanges).length > 0,
    isSaving: saveMutation.isPending,
    
    // Acciones
    setAgentId,
    registerField,
    registerBulkChanges,
    discardChanges,
    triggerSave,
    
    // Metadata
    lastSavedAt,
    saveError,
  };

  return (
    <AgentEditContext.Provider value={value}>
      {children}
    </AgentEditContext.Provider>
  );
}

// =============================================================================
// HOOK PARA CONSUMIR EL CONTEXTO (punto de entrada principal)
// =============================================================================

/**
 * Hook principal para usar en tabs de "Mi Agente"
 * 
 * @throws Error si se usa fuera de AgentEditProvider
 * 
 * @example
 * function IdentityForm() {
 *   const { registerField, triggerSave, isSaving } = useAgentEditContext();
 *   
 *   return (
 *     <Input 
 *       value={agent.name} 
 *       onChange={(e) => registerField('name', e.target.value)}
 *     />
 *   );
 * }
 */
export function useAgentEditContext(): AgentEditContextValue {
  const context = useContext(AgentEditContext);
  
  if (context === undefined) {
    throw new Error(
      "useAgentEditContext must be used within an AgentEditProvider. " +
      "Wrap your component tree with <AgentEditProvider>."
    );
  }
  
  return context;
}

// =============================================================================
// HOOKS AUXILIARES PARA CASOS COMUNES (bonus de productividad)
// =============================================================================

/**
 * Hook para auto-guardar después de un delay de inactividad (debounce)
 * Útil para campos que cambian frecuentemente (ej: texto largo)
 * 
 * @param delay - Milisegundos de espera antes de auto-guardar (default: 2000)
 */
export function useAutoSave(delay: number = 2000) {
  const { pendingChanges, triggerSave, hasUnsavedChanges } = useAgentEditContext();
  
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const debouncedSave = useCallback(
    debounce(() => {
      if (hasUnsavedChanges) {
        triggerSave();
      }
    }, delay),
    [pendingChanges, hasUnsavedChanges, triggerSave, delay]
  );
  
  // Activar auto-save cuando hay cambios pendientes
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const effectDeps = [JSON.stringify(pendingChanges), hasUnsavedChanges];
  
  useEffect(() => {
    if (hasUnsavedChanges) {
      debouncedSave();
    }
    return () => debouncedSave.cancel?.();
  }, effectDeps);
  
  return { 
    hasUnsavedChanges, 
    isAutoSaving: debouncedSave.isPending,
    cancelAutoSave: debouncedSave.cancel 
  } as const;
}

/**
 * Hook para confirmar navegación con cambios no guardados
 * Útil para prevenir pérdida de datos al cambiar de tab o página
 */
export function useUnsavedChangesWarning(enabled: boolean = true) {
  const { hasUnsavedChanges } = useAgentEditContext();
  
  useEffect(() => {
    if (!enabled || !hasUnsavedChanges) return;
    
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = ''; // Requerido para Chrome
      return '';
    };
    
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [enabled, hasUnsavedChanges]);
  
  // Nota: Para navegación interna (React Router), usar prompt personalizado
}

// =============================================================================
// UTILIDAD: DEBOUNCE (implementación simple sin dependencias externas)
// =============================================================================

function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): T & { cancel?: () => void; isPending?: boolean } {
  let timeout: ReturnType<typeof setTimeout> | null = null;
  let pending = false;
  
  const debounced = function (this: any, ...args: Parameters<T>) {
    pending = true;
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => {
      pending = false;
      func.apply(this, args);
    }, wait);
  } as T & { cancel?: () => void; isPending?: boolean };
  
  debounced.cancel = () => {
    if (timeout) {
      clearTimeout(timeout);
      timeout = null;
      pending = false;
    }
  };
  
  Object.defineProperty(debounced, "isPending", {
    get: () => pending,
  });
  
  return debounced;
}
