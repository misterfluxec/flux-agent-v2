'use client';

import { useParams, useRouter } from 'next/navigation';
import { Bot, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AgentEditor } from './editor/AgentEditor';

export default function AgentPage() {
  const params = useParams();
  const router = useRouter();

  // Si no hay ID, mostrar formulario de creación
  if (!params.id) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="text-center space-y-4">
          <Bot className="w-16 h-16 mx-auto text-muted-foreground" />
          <h1 className="text-2xl font-bold">Crear Nuevo Agente</h1>
          <p className="text-muted-foreground">Selecciona un agente existente o crea uno nuevo desde el dashboard</p>
          <Button onClick={() => router.push('/dashboard')}>
            Volver al Dashboard
          </Button>
        </div>
      </div>
    );
  }

  // Si hay ID, mostrar el editor unificado
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <AgentEditor agentId={params.id as string} />
    </div>
  );
}
