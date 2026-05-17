import { apiClient } from "@/lib/api-client";

export interface LeadData {
  id: string;
  name: string;
  phone: string;
  email: string;
  canal: string;
  status: string;
  monto: number;
  fecha: string;
  sentimiento: number;
}

export async function fetchLeads(): Promise<LeadData[]> {
  const { data } = await apiClient.get<LeadData[]>("/crm/leads");
  return data;
}
