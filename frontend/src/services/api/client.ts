const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:9000";

class ApiClient {
  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const token = typeof window !== 'undefined' ? localStorage.getItem("flux_token") : null;
    const headers = { 
        "Content-Type": "application/json", 
        ...(token ? { Authorization: `Bearer ${token}` } : {}) 
    };
    
    // Support relative paths
    const fullUrl = path.startsWith("http") ? path : `${API_BASE}${path}`;
    
    const res = await fetch(fullUrl, { ...options, headers });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Error desconocido" }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  }

  get<T>(path: string) { return this.request<T>(path, { method: "GET" }); }
  post<T>(path: string, body: any) { return this.request<T>(path, { method: "POST", body: JSON.stringify(body) }); }
  patch<T>(path: string, body: any) { return this.request<T>(path, { method: "PATCH", body: JSON.stringify(body) }); }
}

export const api = new ApiClient();
