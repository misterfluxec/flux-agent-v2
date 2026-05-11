import { api } from "./client";

export interface Explanation {
  signals: string[];
  policy_applied: string;
  confidence_pct: number;
  source: string;
}

export const getDecision = (context: "lead" | "handoff" | "response", entityId: string) => 
  api.get<Explanation>(`/api/v1/explain/decision?context=${context}&entity_id=${entityId}`);
