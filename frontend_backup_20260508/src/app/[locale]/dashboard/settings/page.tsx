"use client";

import { useState } from "react";
import { 
  Building, Users, CreditCard, Shield, 
  Bell, AlertTriangle, Trash2, CheckCircle2,
  ChevronRight, ExternalLink, Mail, UserPlus
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

type TabType = "profile" | "team" | "billing" | "security";

export default function ConfiguracionPage() {
  const [activeTab, setActiveTab] = useState<TabType>("profile");

  const tabs = [
    { id: "profile", label: "Perfil de Empresa", icon: Building },
    { id: "team", label: "Gestión de Equipo", icon: Users },
    { id: "billing", label: "Facturación y Plan", icon: CreditCard },
    { id: "security", label: "Seguridad y Notificaciones", icon: Shield },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-20">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-white tracking-tight">Configuración</h1>
          <p className="text-slate-400 mt-1">
            Gestiona los ajustes globales, suscripción y colaboradores de FluxAgent.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* Sidebar Navigation */}
        <div className="lg:col-span-1 space-y-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
              className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl text-sm font-bold transition-all duration-300 ${
                activeTab === tab.id 
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20 translate-x-1" 
                  : "text-slate-400 hover:bg-white/5 hover:text-white"
              }`}
            >
              <tab.icon size={18} className={activeTab === tab.id ? "text-white" : "text-slate-500"} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content Area */}
        <div className="lg:col-span-3">
          <div className="bg-slate-900/40 backdrop-blur-xl border border-white/5 rounded-[32px] p-8 shadow-2xl overflow-hidden relative">
            <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full -mr-32 -mt-32 blur-3xl pointer-events-none" />
            
            {activeTab === "profile" && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-500">
                <div className="flex items-center gap-3 pb-6 border-b border-white/5">
                  <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center">
                    <Building className="text-indigo-400" size={24} />
                  </div>
                  <div>
                    <h2 className="text-xl font-black text-white">Perfil de Empresa</h2>
                    <p className="text-xs text-slate-500 font-bold uppercase tracking-widest">Identidad Corporativa</p>
                  </div>
                </div>

                <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-sm font-bold text-slate-300 ml-1">Nombre Legal</label>
                      <input 
                        type="text" 
                        placeholder="Ej. Mi Negocio S.A."
                        className="w-full bg-black/40 border border-white/5 rounded-2xl px-5 py-4 text-sm text-white focus:outline-none focus:border-indigo-500/50 focus:ring-4 focus:ring-indigo-500/5 transition-all"
                        defaultValue="La Bodega EC"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-bold text-slate-300 ml-1">Industria</label>
                      <select className="w-full bg-black/40 border border-white/5 rounded-2xl px-5 py-4 text-sm text-white focus:outline-none focus:border-indigo-500/50 focus:ring-4 focus:ring-indigo-500/5 transition-all appearance-none">
                        <option>Retail / E-commerce</option>
                        <option>Servicios B2B</option>
                        <option>Bienes Raíces</option>
                        <option>Tecnología</option>
                      </select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-bold text-slate-300 ml-1">Sitio Web Oficial</label>
                    <div className="relative">
                      <input 
                        type="url" 
                        placeholder="https://www.labodegaec.com"
                        className="w-full bg-black/40 border border-white/5 rounded-2xl px-5 py-4 text-sm text-white focus:outline-none focus:border-indigo-500/50 focus:ring-4 focus:ring-indigo-500/5 transition-all pl-12"
                      />
                      <ExternalLink className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                    </div>
                  </div>

                  <div className="pt-6 flex justify-end">
                    <Button className="rounded-2xl h-14 px-8 font-black bg-indigo-600 hover:bg-indigo-700 text-white shadow-xl shadow-indigo-500/20">
                      Guardar Cambios
                    </Button>
                  </div>
                </form>
              </div>
            )}

            {activeTab === "team" && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-500">
                <div className="flex items-center justify-between pb-6 border-b border-white/5">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 flex items-center justify-center">
                      <Users className="text-emerald-400" size={24} />
                    </div>
                    <div>
                      <h2 className="text-xl font-black text-white">Gestión de Equipo</h2>
                      <p className="text-xs text-slate-500 font-bold uppercase tracking-widest">Colaboradores</p>
                    </div>
                  </div>
                  <Button variant="outline" className="rounded-xl border-white/10 text-white hover:bg-white/5">
                    <UserPlus size={18} className="mr-2" /> Invitar
                  </Button>
                </div>

                <div className="space-y-4">
                  {[
                    { name: "Admin Principal", email: "admin@labodegaec.com", role: "Owner", avatar: "A" },
                    { name: "Soporte Ventas", email: "ventas@labodegaec.com", role: "Manager", avatar: "V" },
                  ].map((member, i) => (
                    <div key={i} className="flex items-center justify-between p-4 bg-black/20 border border-white/5 rounded-2xl">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold">
                          {member.avatar}
                        </div>
                        <div>
                          <p className="text-sm font-bold text-white">{member.name}</p>
                          <p className="text-xs text-slate-500">{member.email}</p>
                        </div>
                      </div>
                      <span className="px-3 py-1 bg-white/5 rounded-lg text-[10px] font-black uppercase tracking-widest text-slate-400">
                        {member.role}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === "billing" && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-500">
                <div className="flex items-center gap-3 pb-6 border-b border-white/5">
                  <div className="w-12 h-12 rounded-2xl bg-amber-500/10 flex items-center justify-center">
                    <CreditCard className="text-amber-400" size={24} />
                  </div>
                  <div>
                    <h2 className="text-xl font-black text-white">Plan de Suscripción</h2>
                    <p className="text-xs text-slate-500 font-bold uppercase tracking-widest">Facturación</p>
                  </div>
                </div>

                <div className="bg-indigo-600 rounded-[24px] p-8 text-white relative overflow-hidden shadow-2xl">
                  <div className="absolute top-0 right-0 p-4">
                    <span className="bg-white/20 backdrop-blur-md px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest">Activo</span>
                  </div>
                  <h3 className="text-2xl font-black">Plan Flux Pro Max</h3>
                  <p className="text-white/70 mt-2 text-sm max-w-sm">
                    Agentes ilimitados, RAG avanzado y soporte prioritario 24/7.
                  </p>
                  <div className="mt-8 flex items-end gap-2">
                    <span className="text-4xl font-black">$499</span>
                    <span className="text-white/60 mb-1 text-sm">/ mes</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Button variant="outline" className="rounded-2xl h-14 border-white/10 text-white hover:bg-white/5">
                    Historial de Facturas
                  </Button>
                  <Button variant="outline" className="rounded-2xl h-14 border-white/10 text-white hover:bg-white/5">
                    Cambiar Método de Pago
                  </Button>
                </div>
              </div>
            )}

            {activeTab === "security" && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-500">
                <div className="flex items-center gap-3 pb-6 border-b border-white/5">
                  <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center">
                    <Shield className="text-blue-400" size={24} />
                  </div>
                  <div>
                    <h2 className="text-xl font-black text-white">Seguridad y Notificaciones</h2>
                    <p className="text-xs text-slate-500 font-bold uppercase tracking-widest">Protección de Cuenta</p>
                  </div>
                </div>

                <div className="space-y-6">
                  <div className="flex items-center justify-between p-4 bg-black/20 border border-white/5 rounded-2xl">
                    <div className="flex items-center gap-3">
                      <Bell className="text-slate-400" size={20} />
                      <div>
                        <p className="text-sm font-bold text-white">Notificaciones vía WhatsApp</p>
                        <p className="text-xs text-slate-500">Recibe alertas críticas de ventas</p>
                      </div>
                    </div>
                    <div className="w-12 h-6 bg-indigo-600 rounded-full relative p-1 cursor-pointer">
                      <div className="w-4 h-4 bg-white rounded-full ml-auto" />
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-4 bg-black/20 border border-white/5 rounded-2xl">
                    <div className="flex items-center gap-3">
                      <Shield className="text-slate-400" size={20} />
                      <div>
                        <p className="text-sm font-bold text-white">Autenticación de Dos Factores</p>
                        <p className="text-xs text-slate-500">Máxima seguridad para tu equipo</p>
                      </div>
                    </div>
                    <div className="w-12 h-6 bg-slate-800 rounded-full relative p-1 cursor-pointer">
                      <div className="w-4 h-4 bg-white/40 rounded-full" />
                    </div>
                  </div>
                </div>
              </div>
            )}

          </div>

          {/* Zona de Peligro - Siempre visible al fondo de config */}
          <div className="mt-8">
            <div className="bg-red-500/5 border border-red-500/20 rounded-[32px] overflow-hidden backdrop-blur-sm">
              <div className="bg-red-500/10 px-8 py-5 border-b border-red-500/20 flex items-center gap-3">
                <AlertTriangle className="text-red-500" size={20} />
                <h2 className="text-lg font-black text-red-500 uppercase tracking-tight">Zona de Peligro</h2>
              </div>
              <div className="p-8 flex flex-col md:flex-row items-center justify-between gap-8">
                <div className="space-y-2">
                  <h3 className="text-white font-black text-xl flex items-center gap-2">
                    <Trash2 size={20} className="text-red-500" />
                    Resetear Inteligencia
                  </h3>
                  <p className="text-slate-400 text-sm max-w-xl leading-relaxed">
                    Esta acción eliminará permanentemente todos los documentos, textos y productos indexados. Tu agente volverá a su estado base sin conocimientos adicionales.
                  </p>
                </div>
                <Button 
                  variant="destructive"
                  className="rounded-[20px] px-10 h-16 font-black shadow-2xl shadow-red-500/20 whitespace-nowrap"
                  onClick={async () => {
                    if (confirm("¿Estás absolutamente seguro? Esta acción borrará TODO el conocimiento entrenado y no se puede deshacer.")) {
                      try {
                        const { clearBrain } = await import('@/lib/api');
                        const res = await clearBrain();
                        toast.success(res.mensaje, { 
                          description: `${res.chunks_eliminados} fragmentos de memoria eliminados.`
                        });
                      } catch (e) {
                        toast.error("Error al vaciar el cerebro");
                      }
                    }
                  }}
                >
                  Vaciar Cerebro IA
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
