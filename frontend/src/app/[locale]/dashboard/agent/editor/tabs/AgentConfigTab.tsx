"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchAgent, AgentResponse } from "@/lib/api/agents";
import { useAgentEditContext } from "../context/AgentEditContext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";

interface AgentConfigTabProps {
  agentId: string;
}

export function AgentConfigTab({ agentId }: AgentConfigTabProps) {
  const { registerField } = useAgentEditContext();

  const { data: agent, isLoading, error } = useQuery<AgentResponse, Error>({
    queryKey: ["agent", agentId],
    queryFn: () => fetchAgent(agentId),
    enabled: !!agentId,
  });

  if (isLoading) {
    return <ConfigTabSkeleton />;
  }

  if (error || !agent) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <p className="text-destructive text-sm">
            No se pudo cargar la configuración del agente. 
            <button 
              className="underline ml-1"
              onClick={() => window.location.reload()}
            >
              Reintentar
            </button>
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Sección: Identidad Básica */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">🪪 Identidad del Agente</CardTitle>
          <CardDescription>Información fundamental que define a tu agente</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nombre *</Label>
              <Input
                id="name"
                defaultValue={agent.name}
                onChange={(e) => registerField("name", e.target.value)}
                placeholder="Ej: Asistente de Ventas Premium"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="agent_type">Tipo de Agente *</Label>
              <Select
                defaultValue={agent.agent_type}
                onValueChange={(value) => registerField("agent_type", value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sales">🛒 Ventas</SelectItem>
                  <SelectItem value="support">🎧 Soporte</SelectItem>
                  <SelectItem value="bookings">📅 Reservas</SelectItem>
                  <SelectItem value="custom">⚙️ Personalizado</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Descripción Pública</Label>
            <Textarea
              id="description"
              defaultValue={agent.description || ""}
              onChange={(e) => registerField("description", e.target.value)}
              placeholder="Breve descripción que verán tus clientes"
              rows={2}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="language">Idioma Principal</Label>
              <Select
                defaultValue={agent.language}
                onValueChange={(value) => registerField("language", value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Español (Ecuador)">🇪🇨 Español (EC)</SelectItem>
                  <SelectItem value="Español (México)">🇲🇽 Español (MX)</SelectItem>
                  <SelectItem value="English">🇺🇸 English</SelectItem>
                  <SelectItem value="Português">🇧🇷 Português</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="tone">Tono de Comunicación</Label>
              <Select
                defaultValue={agent.tone}
                onValueChange={(value) => registerField("tone", value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="profesional">💼 Profesional</SelectItem>
                  <SelectItem value="amigable">😊 Amigable</SelectItem>
                  <SelectItem value="entusiasta">🚀 Entusiasta</SelectItem>
                  <SelectItem value="formal">🎩 Formal</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="gender">Género de Voz</Label>
              <Select
                defaultValue={agent.gender}
                onValueChange={(value) => registerField("gender", value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="femenino">👩 Femenino</SelectItem>
                  <SelectItem value="masculino">👨 Masculino</SelectItem>
                  <SelectItem value="neutral">⚖️ Neutral</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Separator />

      {/* Sección: Personalidad y Comportamiento */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">🧠 Personalidad & Comportamiento</CardTitle>
          <CardDescription>Define cómo piensa y actúa tu agente</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="personality">Personalidad (descripción corta)</Label>
            <Textarea
              id="personality"
              defaultValue={agent.personality || ""}
              onChange={(e) => registerField("personality", e.target.value)}
              placeholder="Ej: Paciente, empático, orientado a soluciones..."
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="instructions">Instrucciones Específicas</Label>
            <Textarea
              id="instructions"
              defaultValue={agent.instructions || ""}
              onChange={(e) => registerField("instructions", e.target.value)}
              placeholder="Reglas de comportamiento, límites, protocolos de escalación..."
              rows={4}
            />
            <p className="text-xs text-muted-foreground">
              Estas instructions se inyectan en el prompt del sistema. Sé específico.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="model">Modelo LLM</Label>
              <Select
                defaultValue={agent.model}
                onValueChange={(value) => registerField("model", value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="qwen2.5:3b">Qwen 2.5 3B (rápido)</SelectItem>
                  <SelectItem value="qwen2.5:7b">Qwen 2.5 7B (equilibrado)</SelectItem>
                  <SelectItem value="llama3:8b">Llama 3 8B (calidad)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="temperature">
                Creatividad: {agent.temperature?.toFixed(2)}
              </Label>
              <Input
                id="temperature"
                type="range"
                min="0"
                max="1"
                step="0.1"
                defaultValue={agent.temperature}
                onChange={(e) => registerField("temperature", parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                0 = preciso y repetitivo • 1 = creativo y variable
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ConfigTabSkeleton() {
  return (
    <div className="space-y-6">
      {[1, 2].map((section) => (
        <Card key={section}>
          <CardHeader>
            <Skeleton className="h-5 w-48" />
            <Skeleton className="h-4 w-72" />
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="space-y-2">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
