"use client";

import { useState, useEffect } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, CheckCircle2, RefreshCw, X } from "lucide-react";
import { Button } from "@/components/ui/button";

// =============================================================================
// TIPOS Y ESTADO DEL CIRCUIT BREAKER
// =============================================================================

interface CircuitBreakerStatus {
  service: string;
  status: "CLOSED" | "OPEN" | "HALF_OPEN";
  lastFailure?: Date;
  nextRetry?: Date;
  failureCount?: number;
  threshold?: number;
}

interface SystemHealthResponse {
  status: "healthy" | "degraded" | "down";
  services: CircuitBreakerStatus[];
  timestamp: string;
}

// =============================================================================
// COMPONENTE PRINCIPAL: CIRCUIT BREAKER BANNER
// =============================================================================

export function CircuitBreakerBanner() {
  const [systemHealth, setSystemHealth] = useState<SystemHealthResponse | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  // Simular datos para demostración (reemplazar con llamada real a /health)
  useEffect(() => {
    // TODO: Reemplazar con llamada real a /api/health
    // const { data } = useQuery<SystemHealthResponse>({
    //   queryKey: ['system-health'],
    //   refetchInterval: 30000, // Cada 30 segundos
    // });
    
    // Datos simulados para demostración
    const mockData: SystemHealthResponse = {
      status: "healthy",
      services: [
        {
          service: "ollama",
          status: "CLOSED",
          failureCount: 0,
          threshold: 5,
        },
        {
          service: "postgres",
          status: "CLOSED",
          failureCount: 0,
          threshold: 5,
        },
        {
          service: "redis",
          status: "CLOSED",
          failureCount: 0,
          threshold: 5,
        },
      ],
      timestamp: new Date().toISOString(),
    };
    
    setSystemHealth(mockData);
    setIsVisible(mockData.status !== "healthy");
  }, []);

  // Determinar si mostrar banner basado en estado del sistema
  const shouldShowBanner = isVisible && systemHealth && systemHealth.status !== "healthy";

  // Función para reintentar manualmente
  const handleRetry = async () => {
    setIsRetrying(true);
    try {
      // TODO: Llamar a endpoint de retry si existe
      // await fetch('/api/health/retry', { method: 'POST' });
      
      // Simular retry para demostración
      setTimeout(() => {
        setSystemHealth(prev => prev ? { ...prev, status: "healthy" } : null);
        setIsVisible(false);
        setIsRetrying(false);
      }, 2000);
    } catch (error) {
      setIsRetrying(false);
    }
  };

  // Función para cerrar banner manualmente
  const handleDismiss = () => {
    setIsVisible(false);
  };

  if (!shouldShowBanner) {
    return null;
  }

  return (
    <Alert 
      className={`
        border-l-4 transition-all duration-300
        ${systemHealth?.status === 'down' 
          ? 'border-red-500 bg-red-50 text-red-800' 
          : 'border-amber-500 bg-amber-50 text-amber-800'
        }
      `}
    >
      <div className="flex items-start justify-between w-full">
        <div className="flex items-start gap-3 flex-1">
          <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <AlertDescription className="text-sm font-medium">
              <div className="flex items-center gap-2 mb-2">
                <span>
                  {systemHealth?.status === 'down' 
                    ? '⚠️ Sistema temporalmente fuera de servicio' 
                    : '⚡ Sistema con funcionalidad limitada'
                  }
                </span>
                {isRetrying && (
                  <span className="flex items-center gap-1 text-xs">
                    <RefreshCw className="h-3 w-3 animate-spin" />
                    Reintentando...
                  </span>
                )}
              </div>
              
              {/* Detalles de servicios afectados */}
              {systemHealth?.services && systemHealth.services.length > 0 && (
                <div className="mt-3 space-y-2">
                  <p className="text-xs font-medium">Servicios afectados:</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                    {systemHealth.services
                      .filter(service => service.status !== "CLOSED")
                      .map((service) => (
                        <div 
                          key={service.service}
                          className="flex items-center gap-2 p-2 rounded bg-white/50 border border-current/20"
                        >
                          <div className={`
                            h-2 w-2 rounded-full
                            ${service.status === 'OPEN' ? 'bg-red-500' : 'bg-amber-500'}
                          `} />
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium capitalize">{service.service}</p>
                            <p className="text-[10px] opacity-75">
                              {service.status === 'OPEN' ? 'Circuito abierto' : 'Semi-abierto'}
                              {service.failureCount && service.threshold && (
                                <span> ({service.failureCount}/{service.threshold} fallos)</span>
                              )}
                            </p>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              )}
              
              {/* Acciones recomendadas */}
              <div className="mt-3 p-3 rounded bg-white/30 border border-current/20">
                <p className="text-xs font-medium mb-1">Acciones recomendadas:</p>
                <ul className="text-xs space-y-1">
                  {systemHealth?.status === 'down' ? (
                    <>
                      <li>• Espere unos minutos y recargue la página</li>
                      <li>• Verifique su conexión a internet</li>
                      <li>• Contacte a soporte si el problema persiste</li>
                    </>
                  ) : (
                    <>
                      <li>• Algunas funciones pueden estar limitadas</li>
                      <li>• Los datos se sincronizarán cuando el sistema se recupere</li>
                      <li>• Puede continuar trabajando con funcionalidad básica</li>
                    </>
                  )}
                </ul>
              </div>
            </AlertDescription>
          </div>
        </div>
        
        {/* Acciones del banner */}
        <div className="flex items-center gap-2 ml-4">
          {systemHealth?.status === 'degraded' && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleRetry}
              disabled={isRetrying}
              className="text-xs"
            >
              <RefreshCw className={`h-3 w-3 mr-1 ${isRetrying ? 'animate-spin' : ''}`} />
              {isRetrying ? 'Reintentando...' : 'Reintentar'}
            </Button>
          )}
          
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDismiss}
            className="text-xs hover:bg-current/10"
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      </div>
    </Alert>
  );
}

// =============================================================================
// COMPONENTE AUXILIAR: INDICADOR DE SERVICIO INDIVIDUAL
// =============================================================================

interface ServiceIndicatorProps {
  service: CircuitBreakerStatus;
  compact?: boolean;
}

export function ServiceIndicator({ service, compact = false }: ServiceIndicatorProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'CLOSED': return 'bg-emerald-500';
      case 'OPEN': return 'bg-red-500';
      case 'HALF_OPEN': return 'bg-amber-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'CLOSED': return 'Operativo';
      case 'OPEN': return 'Fuera de servicio';
      case 'HALF_OPEN': return 'Limitado';
      default: return 'Desconocido';
    }
  };

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <div className={`h-2 w-2 rounded-full ${getStatusColor(service.status)}`} />
        <span className="text-xs capitalize">{service.service}</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border bg-card">
      <div className={`h-3 w-3 rounded-full ${getStatusColor(service.status)}`} />
      <div className="flex-1">
        <p className="text-sm font-medium capitalize">{service.service}</p>
        <p className="text-xs text-muted-foreground">{getStatusText(service.status)}</p>
        {service.failureCount && service.failureCount > 0 && (
          <p className="text-xs text-amber-600">
            {service.failureCount} fallos recientes
          </p>
        )}
      </div>
    </div>
  );
}
