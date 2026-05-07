import axios from "axios";
// Instancia base configurada
export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// Hook para aplicar rate limit monitoring global (disabled until re-implemented)
export function useApiRateLimitMonitoring() {
  // Disabled
}
