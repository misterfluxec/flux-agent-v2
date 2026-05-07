"use client";

import { useEffect } from "react";
import { toast } from "sonner"; // o tu librería de toasts preferida
import { useQueryClient } from "@tanstack/react-query";

// =============================================================================
// CONFIGURACIÓN DEL HOOK
// =============================================================================

interface RateLimitHeaders {
  limit: number | null;
  remaining: number | null;
  reset: number | null; // Unix timestamp
  retryAfter: number | null; // Segundos hasta que se pueda reintentar
}

interface UseRateLimitIndicatorOptions {
  /** Mostrar toast solo cuando quedan <= X requests */
  warningThreshold?: number;
  
  /** Duración del toast en milisegundos */
  toastDuration?: number;
  
  /** Callback personalizado cuando se excede el límite */
  onLimitExceeded?: () => void;
  
  /** Habilitar/deshabilitar el hook dinámicamente */
  enabled?: boolean;
}

const DEFAULT_OPTIONS: Required<UseRateLimitIndicatorOptions> = {
  warningThreshold: 5,
  toastDuration: 5000,
  onLimitExceeded: () => {},
  enabled: true,
};

// =============================================================================
// HOOK PRINCIPAL
// =============================================================================

/**
 * Hook para monitorear headers de rate limit en respuestas HTTP
 * y mostrar advertencias proactivas al usuario
 * 
 * @param response - Respuesta de fetch/axios para inspeccionar headers
 * @param options - Configuración opcional del comportamiento
 * 
 * @example
 * // Con axios
 * const response = await api.get('/analytics/overview');
 * useRateLimitIndicator(response);
 * 
 * // Con fetch nativo
 * const response = await fetch('/api/data');
 * useRateLimitIndicator(response);
 */
export function useRateLimitIndicator(
  response: Response | { headers: Headers; status?: number } | null | undefined,
  options?: UseRateLimitIndicatorOptions
) {
  const queryClient = useQueryClient();
  const opts = { ...DEFAULT_OPTIONS, ...options };

  useEffect(() => {
    if (!opts.enabled || !response?.headers) return;

    const headers = parseRateLimitHeaders(response.headers);
    
    // =============================================================================
    // CASO 1: Límite excedido (429 Too Many Requests)
    // =============================================================================
    if (headers.retryAfter !== null || response.status === 429) {
      const retryAfter = headers.retryAfter ?? 60; // Default 60s si no especificado
      
      // Mostrar toast de error con acción de reintentar
      toast.error("⚠️ Límite de peticiones excedido", {
        description: `Vuelve a intentar en ${formatDuration(retryAfter)}`,
        duration: opts.toastDuration,
        action: {
          label: "Reintentar",
          onClick: () => {
            // Invalidar queries relevantes para forzar refetch
            queryClient.refetchQueries({
              predicate: (query) => query.state.status === "error",
            });
            opts.onLimitExceeded();
          },
        },
      });
      
      // Callback personalizado para lógica adicional
      opts.onLimitExceeded();
      return;
    }

    // =============================================================================
    // CASO 2: Advertencia preventiva (quedan pocos requests)
    // =============================================================================
    if (
      headers.remaining !== null &&
      headers.remaining <= opts.warningThreshold &&
      headers.reset !== null
    ) {
      const timeUntilReset = Math.max(0, headers.reset * 1000 - Date.now());
      
      // Evitar spam de toasts: solo mostrar si es la primera vez que llega a este umbral
      const toastId = `rate-limit-warning-${headers.limit}`;
      
      toast.warning("⚠️ Casi alcanzas el límite de peticiones", {
        id: toastId,
        description: `Quedan ${headers.remaining} requests. Se renueva en ${formatDuration(timeUntilReset / 1000)}`,
        duration: opts.toastDuration,
      });
    }

    // =============================================================================
    // CASO 3: Reset exitoso (el límite se renovó)
    // =============================================================================
    if (headers.remaining === headers.limit && headers.limit !== null) {
      // Dismiss cualquier toast de advertencia previo
      toast.dismiss(`rate-limit-warning-${headers.limit}`);
    }

  }, [response, opts, queryClient]);
}

// =============================================================================
// UTILIDADES INTERNAS
// =============================================================================

/**
 * Parsea headers estándar de rate limit (RFC 6585 + convenciones comunes)
 */
function parseRateLimitHeaders(headers: Headers): RateLimitHeaders {
  const getHeader = (names: string[]): number | null => {
    for (const name of names) {
      const value = headers.get(name);
      if (value) {
        const parsed = parseInt(value, 10);
        if (!isNaN(parsed)) return parsed;
      }
    }
    return null;
  };

  return {
    // Límite total permitido en la ventana
    limit: getHeader([
      "x-rate-limit-limit",
      "ratelimit-limit",
      "x-limit",
    ]),
    
    // Requests restantes en la ventana actual
    remaining: getHeader([
      "x-rate-limit-remaining",
      "ratelimit-remaining",
      "x-remaining",
    ]),
    
    // Timestamp Unix cuando se renueva el límite
    reset: getHeader([
      "x-rate-limit-reset",
      "ratelimit-reset",
      "x-reset",
    ]),
    
    // Segundos hasta que se pueda reintentar (para 429)
    retryAfter: getHeader([
      "retry-after",
      "x-retry-after",
    ]),
  };
}

/**
 * Formatea duración en segundos a string legible
 */
function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.ceil(seconds)}s`;
  if (seconds < 3600) return `${Math.ceil(seconds / 60)}min`;
  return `${Math.ceil(seconds / 3600)}h`;
}

// =============================================================================
// HOOK AUXILIAR: MONITOREO GLOBAL DE RATE LIMIT
// =============================================================================

/**
 * Hook para interceptar todas las respuestas de una instancia axios/fetch
 * y aplicar rate limit indicator automáticamente
 * 
 * @example
 * // Con axios
 * const api = axios.create({ baseURL: '/api' });
 * useGlobalRateLimitMonitor(api);
 */
export function useGlobalRateLimitMonitor(
  httpClient: {
    interceptors: {
      response: {
        use: (onFulfilled: (res: any) => any, onRejected: (err: any) => any) => void;
      };
    };
  },
  options?: UseRateLimitIndicatorOptions
) {
  useEffect(() => {
    const onFulfilled = (response: any) => {
      // Crear objeto compatible con Response para el hook
      const mockResponse = {
        headers: new Headers(response.headers),
        status: response.status,
      };
      useRateLimitIndicator(mockResponse, options);
      return response;
    };

    const onRejected = (error: any) => {
      if (error.response) {
        const mockResponse = {
          headers: new Headers(error.response.headers),
          status: error.response.status,
        };
        useRateLimitIndicator(mockResponse, options);
      }
      return Promise.reject(error);
    };

    httpClient.interceptors.response.use(onFulfilled, onRejected);

    // Cleanup: remover interceptors al desmontar (opcional, depende de la lib)
    return () => {
      // Nota: axios no permite remover interceptors fácilmente,
      // pero en la práctica no es crítico para este caso de uso
    };
  }, [httpClient, options]);
}
