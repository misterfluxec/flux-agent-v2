import { v4 as uuidv4 } from "uuid";
import { trackEvent } from "./telemetry";

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:9000";
const API_PREFIX = "/api/v1";

export class OperationalError extends Error {
  constructor(
    public payload: {
      status: number;
      code: string;
      message: string;
      correlationId: string;
      url: string;
    }
  ) {
    super(payload.message);
    this.name = "OperationalError";
  }
}

export type ApiResponse<T> = {
  data: T;
  correlationId?: string;
};

class ApiClient {
  private async request<T = any>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    // If endpoint already has /api/v1, don't prefix it again. If it's absolute, keep it.
    let url = endpoint;
    if (!endpoint.startsWith("http")) {
      url = endpoint.startsWith(API_PREFIX) ? `${API_BASE_URL}${endpoint}` : `${API_BASE_URL}${API_PREFIX}${endpoint}`;
    }

    const correlationId = uuidv4();
    const token = typeof window !== "undefined" ? localStorage.getItem("flux_token") : null;

    // We don't overwrite headers if they are FormData (browser sets boundary automatically)
    const isFormData = options.body instanceof FormData;
    
    const headers: HeadersInit = {
      "X-Correlation-ID": correlationId,
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    };

    if (!isFormData && !("Content-Type" in headers)) {
      (headers as any)["Content-Type"] = "application/json";
    }

    const startMs = Date.now();

    try {
      const response = await fetch(url, { ...options, headers });
      const latencyMs = Date.now() - startMs;

      if (!response.ok) {
        if (response.status === 401 && typeof window !== "undefined") {
          localStorage.removeItem("flux_token");
          window.location.href = "/login";
        }

        const errorData = await response.json().catch(() => ({}));
        
        const errorPayload = {
          status: response.status,
          code: errorData.error_code || "UNKNOWN_ERROR",
          message: errorData.detail || errorData.message || "Operational Error",
          correlationId,
          url,
        };

        // Telemetry Error Logging
        trackEvent("api.error", {
          ...errorPayload,
          method: options.method || "GET",
          latency_ms: latencyMs,
        });

        throw new OperationalError(errorPayload);
      }

      // Track successful request latency for specific critical paths if needed
      if (latencyMs > 1000) {
         trackEvent("api.slow_request", { url, latency_ms: latencyMs, correlationId });
      }

      // Handle empty responses
      if (response.status === 204) {
        return { data: {} as T, correlationId };
      }

      // Ensure we extract headers or correlation
      const data = await response.json().catch(() => ({}));
      
      // Preserve the Axios-like response format
      return { data, correlationId };
    } catch (error) {
      if (error instanceof OperationalError) throw error;
      
      // Network errors (CORS, offline, etc)
      trackEvent("api.network_error", { url, error: String(error) });
      throw new OperationalError({
        status: 0,
        code: "NETWORK_ERROR",
        message: "Error de red o conexión rechazada",
        correlationId,
        url,
      });
    }
  }

  get<T = any>(endpoint: string, options?: RequestInit) {
    return this.request<T>(endpoint, { ...options, method: "GET" });
  }

  post<T = any>(endpoint: string, body?: any, options?: RequestInit) {
    return this.request<T>(endpoint, {
      ...options,
      method: "POST",
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
  }

  put<T = any>(endpoint: string, body?: any, options?: RequestInit) {
    return this.request<T>(endpoint, {
      ...options,
      method: "PUT",
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
  }

  patch<T = any>(endpoint: string, body?: any, options?: RequestInit) {
    return this.request<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
  }

  delete<T = any>(endpoint: string, options?: RequestInit) {
    return this.request<T>(endpoint, { ...options, method: "DELETE" });
  }
}

export const apiClient = new ApiClient();
