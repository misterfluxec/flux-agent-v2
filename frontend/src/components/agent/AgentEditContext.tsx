// =============================================================================
// FLUXAGENT V2 — AGENT EDIT CONTEXT
// =============================================================================
// Contexto compartido para edición de agente entre tabs
// Permite cambios acumulados y guardado atómico
// =============================================================================

'use client';

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

// =============================================================================
// TYPES
// =============================================================================

interface AgentField {
  key: string;
  value: any;
  dirty: boolean;
}

interface AgentEditState {
  agentId: string;
  originalData: any;
  changes: Record<string, AgentField>;
  isDirty: boolean;
  isSaving: boolean;
}

interface AgentEditContextType {
  agentId: string;
  changes: Record<string, AgentField>;
  isDirty: boolean;
  isSaving: boolean;
  registerField: (key: string, value: any) => void;
  updateField: (key: string, value: any) => void;
  triggerSave: () => Promise<void>;
  resetChanges: () => void;
}

// =============================================================================
// CONTEXT
// =============================================================================

const AgentEditContext = createContext<AgentEditContextType | null>(null);

interface AgentEditProviderProps {
  children: ReactNode;
  agentId: string;
  initialData: any;
  onSave: (changes: Record<string, any>) => Promise<void>;
}

export function AgentEditProvider({ children, agentId, initialData, onSave }: AgentEditProviderProps) {
  const [state, setState] = useState<AgentEditState>({
    agentId,
    originalData: initialData,
    changes: {},
    isDirty: false,
    isSaving: false
  });

  // Registrar un campo (para inicialización)
  const registerField = useCallback((key: string, value: any) => {
    setState(prev => {
      if (prev.changes[key]) return prev; // Ya existe
      
      const newChanges = {
        ...prev.changes,
        [key]: {
          key,
          value,
          dirty: JSON.stringify(value) !== JSON.stringify(prev.originalData?.[key])
        }
      };
      
      return {
        ...prev,
        changes: newChanges,
        isDirty: Object.values(newChanges).some(field => field.dirty)
      };
    });
  }, [initialData]);

  // Actualizar un campo existente
  const updateField = useCallback((key: string, value: any) => {
    setState(prev => {
      const newChanges = {
        ...prev.changes,
        [key]: {
          key,
          value,
          dirty: JSON.stringify(value) !== JSON.stringify(prev.originalData?.[key])
        }
      };
      
      return {
        ...prev,
        changes: newChanges,
        isDirty: Object.values(newChanges).some(field => field.dirty)
      };
    });
  }, [initialData]);

  // Trigger save con todos los cambios
  const triggerSave = useCallback(async () => {
    if (!state.isDirty || state.isSaving) return;

    setState(prev => ({ ...prev, isSaving: true }));

    try {
      // Preparar cambios para enviar
      const changesToSave: Record<string, any> = {};
      Object.values(state.changes).forEach(field => {
        if (field.dirty) {
          changesToSave[field.key] = field.value;
        }
      });

      await onSave(changesToSave);
      
      // Resetear status después de guardar exitosamente
      setState(prev => ({
        ...prev,
        originalData: { ...prev.originalData, ...changesToSave },
        changes: {},
        isDirty: false,
        isSaving: false
      }));
    } catch (error) {
      console.error('Error saving agent:', error);
      setState(prev => ({ ...prev, isSaving: false }));
      throw error;
    }
  }, [state.changes, state.isDirty, state.isSaving, onSave]);

  // Resetear cambios
  const resetChanges = useCallback(() => {
    setState(prev => ({
      ...prev,
      changes: {},
      isDirty: false
    }));
  }, []);

  const contextValue: AgentEditContextType = {
    agentId: state.agentId,
    changes: state.changes,
    isDirty: state.isDirty,
    isSaving: state.isSaving,
    registerField,
    updateField,
    triggerSave,
    resetChanges
  };

  return (
    <AgentEditContext.Provider value={contextValue}>
      {children}
    </AgentEditContext.Provider>
  );
}

// =============================================================================
// HOOK
// =============================================================================

export function useAgentEditContext() {
  const context = useContext(AgentEditContext);
  if (!context) {
    throw new Error('useAgentEditContext must be used within AgentEditProvider');
  }
  return context;
}

// =============================================================================
// UTILITY HOOKS
// =============================================================================

export function useAgentField<T = any>(key: string, initialValue?: T) {
  const { registerField, updateField, changes } = useAgentEditContext();
  
  // Registrar campo si no existe
  useState(() => {
    if (!changes[key] && initialValue !== undefined) {
      registerField(key, initialValue);
    }
  });

  const field = changes[key];
  
  const setValue = (value: T) => {
    updateField(key, value);
  };

  return {
    value: field?.value ?? initialValue,
    dirty: field?.dirty ?? false,
    setValue,
    isDirty: field?.dirty ?? false
  };
}

export function useAgentSaveButton() {
  const { triggerSave, isDirty, isSaving } = useAgentEditContext();
  
  return {
    triggerSave,
    isDirty,
    isSaving,
    canSave: isDirty && !isSaving
  };
}
