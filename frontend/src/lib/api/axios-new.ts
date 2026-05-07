import axios from "axios";
import { useGlobalRateLimitMonitor } from "@/hooks/useRateLimitIndicator-new";

// Instancia base configurada
export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
  // Timeouts para prevenir hanging requests
  timeout: 30000,
});

// Hook para aplicar rate limit monitoring global
export function useApiRateLimitMonitoring() {
  useGlobalRateLimitMonitor(api, {
    warningThreshold: 3, // Advertir cuando queden ≤3 requests
    toastDuration: 4000,
  });
}

// Uso en layout principal:
// function RootLayout({ children }) {
//   useApiRateLimitMonitoring();
//   return <>{children}</>;
// }
