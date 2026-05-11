import { api } from "./client";

export interface Recommendation {
  id: string;
  type: string;
  title: string;
  context: string;
  actions: { label: string; variant: string }[];
}

export const getFeed = () => 
  api.get<{ feed: Recommendation[]; generated_at: string }>("/api/v1/insights/feed");
