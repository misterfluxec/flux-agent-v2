"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { BarChart3, MessageSquare, TrendingUp } from "lucide-react";

interface AgentAnalyticsTabProps {
  agentId: string;
}

export function AgentAnalyticsTab({ agentId }: AgentAnalyticsTabProps) {
  // TODO: Conectar a endpoint /analytics/agent/{id} cuando esté disponible
  // Por ahora mostramos un status informativo
  
  return (
    <div className="space-y-4">
      <Alert>
        <BarChart3 className="h-4 w-4" />
        <AlertDescription>
          <strong>Próximamente:</strong> Analytics detallados por agente. 
          Mientras tanto, revisa las métricas globales en la sección{" "}
          <a href="/dashboard/metrics" className="underline">Métricas</a>.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricPlaceholder 
          icon={MessageSquare}
          label="Conversaciones"
          value="—"
          description="Total de interacciones con este agente"
        />
        <MetricPlaceholder 
          icon={TrendingUp}
          label="Tasa de Conversión"
          value="—"
          description="Porcentaje de leads que se convierten en ventas"
        />
        <MetricPlaceholder 
          icon={BarChart3}
          label="Satisfacción"
          value="—"
          description="Puntuación promedio basada en feedback"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">📈 Actividad Reciente</CardTitle>
          <CardDescription>Últimas 24 horas</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">
            Gráfico de actividad (próximamente)
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function MetricPlaceholder({ 
  icon: Icon, 
  label, 
  value, 
  description 
}: { 
  icon: React.ComponentType<{ className?: string }>; 
  label: string; 
  value: string; 
  description: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      </CardContent>
    </Card>
  );
}
