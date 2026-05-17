"use client";

import { useQuery } from "@tanstack/react-query";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AlertTriangle, CheckCircle2, Loader2, RefreshCw } from "lucide-react";
import { fetchSystemHealth, SystemHealthStatus, CircuitState, CircuitBreakerStatus } from "@/lib/api/system";

// =============================================================================
// COMPONENTE PRINCIPAL: BANNER DE ESTADO
// =============================================================================

interface CircuitBreakerBannerProps {
  /** Polling interval en milisegundos (default: 30s) */
  refreshInterval?: number;
  
  /** Mostrar solo si hay problemas (ocultar cuando todo está bien) */
  showOnlyOnIssues?: boolean;
  
  /** Callback cuando el usuario hace clic en "Ver detalles" */
  onShowDetails?: () => void;
}

export function CircuitBreakerBanner({
  refreshInterval = 30000,
  showOnlyOnIssues = true,
  onShowDetails,
}: CircuitBreakerBannerProps = {}) {
  const { data: health, isLoading, error, refetch } = useQuery<SystemHealthStatus, Error>({
    queryKey: ["system-health"],
    queryFn: fetchSystemHealth,
    refetchInterval: refreshInterval,
    refetchOnWindowFocus: true,
    enabled: !showOnlyOnIssues, // Si showOnlyOnIssues, solo fetch si hay problemas detectados
  });

  // Determinar si hay circuit breakers en status OPEN (problemas activos)
  const activeBreakers = health?.circuits 
    ? Object.entries(health.circuits).filter(
        ([_, circuit]) => circuit.state === "OPEN"
      )
    : [];
  
  const hasIssues = activeBreakers.length > 0 || health?.status === "degraded";

  // Si showOnlyOnIssues y no hay problemas, no renderizar nada
  if (showOnlyOnIssues && !hasIssues && !isLoading && !error) {
    return null;
  }

  // =============================================================================
  // RENDER: ESTADO DE CARGA
  // =============================================================================
  if (isLoading) {
    return (
      <Alert className="bg-muted/50 border-muted">
        <Loader2 className="h-4 w-4 animate-spin" />
        <AlertDescription className="ml-2 text-sm text-muted-foreground">
          Verificando status del sistema...
        </AlertDescription>
      </Alert>
    );
  }

  // =============================================================================
  // RENDER: ESTADO DE ERROR
  // =============================================================================
  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>⚠️ No se pudo verificar el status</AlertTitle>
        <AlertDescription className="flex items-center gap-2">
          <span className="text-sm">
            Error al conectar con el servicio de salud. 
            {error.message && <span className="ml-1 text-muted-foreground">({error.message})</span>}
          </span>
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs"
            onClick={() => refetch()}
          >
            <RefreshCw className="h-3 w-3 mr-1" />
            Reintentar
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  // =============================================================================
  // RENDER: SIN PROBLEMAS (pero showOnlyOnIssues=false)
  // =============================================================================
  if (!hasIssues && !showOnlyOnIssues) {
    return (
      <Alert className="bg-emerald-50 border-emerald-200">
        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
        <AlertTitle className="text-emerald-800">✅ Todos los sistemas operativos</AlertTitle>
        <AlertDescription className="text-sm text-emerald-700">
          Última verificación: {new Date(health!.timestamp).toLocaleTimeString("es-EC")}
        </AlertDescription>
      </Alert>
    );
  }

  // =============================================================================
  // RENDER: CON PROBLEMAS ACTIVOS
  // =============================================================================
  return (
    <Alert className="bg-amber-50 border-amber-200">
      <AlertTriangle className="h-4 w-4 text-amber-600" />
      <AlertTitle className="text-amber-800">
        ⚠️ Servicios en mantenimiento temporal
      </AlertTitle>
      <AlertDescription className="text-sm text-amber-800 space-y-2">
        <p>
          Algunos servicios están experimentando problemas. 
          La funcionalidad básica sigue disponible.
        </p>
        
        {/* Lista de servicios afectados */}
        {activeBreakers.length > 0 && (
          <div className="mt-2 space-y-1">
            <p className="font-medium">Servicios afectados:</p>
            <ul className="list-disc list-inside space-y-0.5 ml-1">
              {activeBreakers.map(([name, circuit]) => (
                <li key={name} className="flex items-center gap-2">
                  <span className="capitalize">{formatServiceName(name)}</span>
                  {circuit.recoveryTimeout && (
                    <span className="text-xs text-muted-foreground">
                      (se renueva en ~{Math.ceil(circuit.recoveryTimeout / 60)}min)
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Acciones */}
        <div className="flex items-center gap-2 pt-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-xs"
            onClick={() => refetch()}
          >
            <RefreshCw className="h-3 w-3 mr-1" />
            Actualizar status
          </Button>
          
          {onShowDetails && (
            <Button
              variant="link"
              size="sm"
              className="h-7 px-0 text-xs text-amber-700 hover:text-amber-900"
              onClick={onShowDetails}
            >
              Ver detalles técnicos →
            </Button>
          )}
        </div>
      </AlertDescription>
    </Alert>
  );
}

// =============================================================================
// UTILIDADES
// =============================================================================

/**
 * Formatea name técnico de circuito a name legible
 */
function formatServiceName(name: string): string {
  const mapping: Record<string, string> = {
    "ollama_llm": "LLM (Inteligencia Artificial)",
    "whatsapp_cloud": "WhatsApp Cloud API",
    "redis_cache": "Servicio de Cache",
    "postgres_db": "Base de Datos",
    "stt_service": "Reconocimiento de Voz",
    "tts_service": "Síntesis de Voz",
  };
  return mapping[name] || name.replace(/_/g, " ");
}
