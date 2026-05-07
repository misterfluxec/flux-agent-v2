// =============================================================================
// AGENT PAGE - SHELL MINIMALISTA
// =============================================================================
// Este archivo SOLO monta el AgentEditor. 
// Toda la lógica vive en /editor/ para mantener separación de responsabilidades.
// =============================================================================

import { AgentEditor } from "./editor/AgentEditor";

interface AgentPageProps {
  params: {
    locale: string;
    id: string; // ID del agente desde la URL
  };
}

export default function AgentPage({ params }: AgentPageProps) {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <AgentEditor agentId={params.id} />
    </div>
  );
}
