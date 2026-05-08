"use client";

import { useEffect } from "react";
import { toast } from "sonner";

/**
 * Hook para detectar y notificar rate limiting basado en headers HTTP
 * Lee headers estándar: x-rate-limit-remaining, x-rate-limit-reset
 */
export function useRateLimitIndicator(response?: Response) {
  useEffect(() => {
    if (!response) return;

    const remaining = response.headers.get('x-rate-limit-remaining');
    const reset = response.headers.get('x-rate-limit-reset');
    const limit = response.headers.get('x-rate-limit-limit');

    // Notificar si quedan pocas peticiones
    if (remaining && parseInt(remaining) < 5) {
      const resetTime = reset ? new Date(parseInt(reset) * 1000) : null;
      const timeUntilReset = resetTime ? formatDistanceToNow(resetTime, { addSuffix: false }) : '';
      
      toast.warning(
        `⚠️ Límite de peticiones: ${remaining} restantes${
          timeUntilReset ? `. Se renueva en ${timeUntilReset}` : ''
        }`,
        { 
          duration: 5000,
          position: "top-right",
          id: "rate-limit-warning" // Prevenir duplicados
        }
      );
    }

    // Log para debugging en desarrollo
    if (process.env.NODE_ENV === 'development' && limit) {
      console.log('Rate Limit Info:', {
        limit,
        remaining,
        reset: reset ? new Date(parseInt(reset) * 1000) : null,
      });
    }
  }, [response]);
}

/**
 * Utilidad para formatear distancia de tiempo (similar a date-fns pero sin dependencia)
 */
function formatDistanceToNow(date: Date, options: { addSuffix?: boolean } = {}): string {
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);

  if (Math.abs(diffSeconds) < 60) {
    return options.addSuffix ? `${Math.abs(diffSeconds)} segundos` : `${Math.abs(diffSeconds)}s`;
  }
  if (Math.abs(diffMinutes) < 60) {
    return options.addSuffix ? `${Math.abs(diffMinutes)} minutos` : `${Math.abs(diffMinutes)}m`;
  }
  return options.addSuffix ? `${Math.abs(diffHours)} horas` : `${Math.abs(diffHours)}h`;
}
