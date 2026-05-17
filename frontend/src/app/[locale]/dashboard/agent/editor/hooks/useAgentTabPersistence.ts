"use client";

import { useState, useEffect } from "react";

const TAB_STORAGE_KEY = "fluxagent:agent:activeTab";
const VALID_TABS = ["config", "analytics", "knowledge", "channels"] as const;
export type AgentTab = (typeof VALID_TABS)[number];

/**
 * Hook para persistir el tab is_active en localStorage
 * Previene que el usuario pierda su posición al recargar
 */
export function useAgentTabPersistence(defaultTab: AgentTab = "config") {
  const [activeTab, setActiveTab] = useState<AgentTab>(defaultTab);
  const [isInitialized, setIsInitialized] = useState(false);

  // Cargar tab guardado al montar (solo en cliente)
  useEffect(() => {
    try {
      const saved = localStorage.getItem(TAB_STORAGE_KEY) as AgentTab;
      if (saved && VALID_TABS.includes(saved)) {
        setActiveTab(saved);
      }
    } catch (error) {
      // Ignorar errores de localStorage (modo incógnito, etc.)
      console.warn("No se pudo cargar preferencia de tab:", error);
    } finally {
      setIsInitialized(true);
    }
  }, []);

  // Guardar tab cuando cambia
  useEffect(() => {
    if (!isInitialized) return;
    try {
      localStorage.setItem(TAB_STORAGE_KEY, activeTab);
    } catch (error) {
      console.warn("No se pudo guardar preferencia de tab:", error);
    }
  }, [activeTab, isInitialized]);

  // Handler tipado para onValueChange de Tabs
  const handleTabChange = (value: string) => {
    if (VALID_TABS.includes(value as AgentTab)) {
      setActiveTab(value as AgentTab);
    }
  };

  return {
    activeTab,
    setActiveTab: handleTabChange,
    isInitialized,
  } as const;
}
