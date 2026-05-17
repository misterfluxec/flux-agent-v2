"use client";

import { UnifiedCustomerView, type UnifiedCustomer } from "@/components/crm/UnifiedCustomerView";
import { FEATURES } from "@/config/features";
import { Users, Info } from "lucide-react";

// Datos de demostración unificados (Leads + Clientes)
const MOCK_UNIFIED_DATA: UnifiedCustomer[] = [
  { id: "1", name: "Carlos Mendoza", email: "carlos@tech.com", phone: "+34 600 111 222", status: "lead", pipelineStage: "nuevo", value: 1200, lastInteraction: "2026-05-15", source: "whatsapp" },
  { id: "2", name: "Ana Martínez", email: "ana@design.io", phone: "+34 600 333 444", status: "lead", pipelineStage: "interesado", value: 3500, lastInteraction: "2026-05-14", source: "web" },
  { id: "3", name: "Juan Pérez", email: "juan@perez.es", phone: "+34 600 555 666", status: "active", value: 12500, lastInteraction: "2026-05-10", source: "web" },
  { id: "4", name: "Marta Sánchez", email: "marta@corp.com", phone: "+34 600 777 888", status: "vip", value: 45000, lastInteraction: "2026-05-01", source: "whatsapp" },
  { id: "5", name: "Sofía Vega", email: "sofia@startup.co", phone: "+34 600 999 000", status: "lead", pipelineStage: "contactado", value: 800, lastInteraction: "2026-05-16", source: "web" },
];

export default function CustomersPage() {
  // Si el CRM unificado está desactivado, podríamos mostrar la vista antigua.
  // Pero aquí forzamos la nueva arquitectura "Pro Max".
  
  return (
    <div className="space-y-8 animate-entry">
      <header className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Users className="w-4 h-4 text-emerald-400" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-emerald-400/80">Ecosistema de Clientes</span>
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight">Directorio <span className="text-emerald-400">Maestro</span></h1>
        </div>
        
        {FEATURES.ENABLE_UNIFIED_CRM && (
          <div className="hidden md:flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg">
            <Info className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest">CRM Unificado Activo</span>
          </div>
        )}
      </header>

      <UnifiedCustomerView initialData={MOCK_UNIFIED_DATA} />
    </div>
  );
}
