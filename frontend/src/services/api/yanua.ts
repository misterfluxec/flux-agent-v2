import { api } from "./client";

export interface ReasoningRequest {
  query: string;
  context_scope?: string;
}

export const postReasoning = (payload: ReasoningRequest) => 
  api.post<{ status: string; message: string; estimated_ms: number }>("/api/v1/yanua/reason", payload);
