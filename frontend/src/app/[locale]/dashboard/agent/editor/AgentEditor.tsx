"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AgentEditProvider } from "./context/AgentEditContext";
import { useAgentTabPersistence, AgentTab } from "./hooks/useAgentTabPersistence";
import { AgentConfigTab } from "./tabs/AgentConfigTab";
import { AgentAnalyticsTab } from "./tabs/AgentAnalyticsTab";
import { AgentKnowledgeTab } from "./tabs/AgentKnowledgeTab";
import { AgentChannelsTab } from "./tabs/AgentChannelsTab";
import { Skeleton } from "@/components/ui/skeleton";
import AgentPlayground from "@/components/AgentPlayground";

interface AgentEditorProps {
  agentId: string;
  initialTab?: AgentTab;
}

/**
 * Componente principal que unifica toda la configuración del agente
 * Usa tabs para separar responsabilidades y contexto para status compartido
 */
export function AgentEditor({ agentId, initialTab = "config" }: AgentEditorProps) {
  const { activeTab, setActiveTab, isInitialized } = useAgentTabPersistence(initialTab);

  // Mientras se inicializa la persistencia, mostrar skeleton
  if (!isInitialized) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-full max-w-md" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  // TODO: Get real tenantId if needed, for now passing default or reading from a context
  const tenantId = "default";

  return (
    <AgentEditProvider initialAgentId={agentId}>
      <div className="space-y-6">
        {/* Header con título y status de guardado */}
        <AgentEditorHeader agentId={agentId} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Columna Izquierda: Configuración (2/3) */}
          <div className="lg:col-span-2">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid grid-cols-2 md:grid-cols-4 lg:w-auto lg:inline-flex">
                <TabsTrigger value="config" className="text-sm">
                  ⚙️ Configuración
                </TabsTrigger>
                <TabsTrigger value="analytics" className="text-sm">
                  📊 Analytics
                </TabsTrigger>
                <TabsTrigger value="knowledge" className="text-sm">
                  🧠 Conocimiento
                </TabsTrigger>
                <TabsTrigger value="channels" className="text-sm">
                  🔌 Canales
                </TabsTrigger>
              </TabsList>

              {/* Contenido de cada tab */}
              <TabsContent value="config" className="mt-6">
                <AgentConfigTab agentId={agentId} />
              </TabsContent>

              <TabsContent value="analytics" className="mt-6">
                <AgentAnalyticsTab agentId={agentId} />
              </TabsContent>

              <TabsContent value="knowledge" className="mt-6">
                <AgentKnowledgeTab agentId={agentId} />
              </TabsContent>

              <TabsContent value="channels" className="mt-6">
                <AgentChannelsTab agentId={agentId} />
              </TabsContent>
            </Tabs>
          </div>

          {/* Columna Derecha: Simulador Omnicanal (1/3) */}
          <div className="lg:col-span-1">
            <div className="sticky top-6">
              <AgentPlayground agentId={agentId} tenantId={tenantId} />
            </div>
          </div>
        </div>
      </div>
    </AgentEditProvider>
  );
}

/**
 * Header con título y status de guardado (reutilizable)
 */
function AgentEditorHeader({ agentId }: { agentId: string }) {
  // Aquí podrías cargar el name del agente para mostrarlo
  // Por ahora usamos un placeholder
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">🤖 Configurar Agente</h1>
        <p className="text-muted-foreground text-sm mt-1">
          ID: <code className="bg-muted px-1 py-0.5 rounded text-xs">{agentId.slice(0, 8)}...</code>
        </p>
      </div>
      
      {/* Indicador de cambios no guardados */}
      <UnsavedChangesIndicator />
    </div>
  );
}

/**
 * Indicador visual de cambios pendientes
 */
function UnsavedChangesIndicator() {
  // Este componente consumirá el contexto para mostrar status
  // Lo implementaremos después de tener los tabs base
  return null; // Placeholder - se implementará en siguiente iteración
}
