"use client";

import { Settings, Building, Bell, Shield, AlertTriangle, Trash2, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function ConfiguracionPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Configuración</h1>
        <p className="text-sm text-slate-400 mt-1">
          Ajustes generales, perfil de empresa y seguridad de la cuenta.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Nav de config */}
        <div className="lg:col-span-1 space-y-2">
          {[
            { label: "Perfil de Empresa", icon: Building, active: true },
            { label: "Notificaciones", icon: Bell, active: false },
            { label: "Seguridad y Accesos", icon: Shield, active: false },
          ].map((tab, i) => (
            <button
              key={i}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                tab.active 
                  ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20" 
                  : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 border border-transparent"
              }`}
            >
              <tab.icon size={18} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Formulario principal */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-slate-200 mb-6 flex items-center gap-2">
            <Building className="text-indigo-500" size={20} />
            Perfil de Empresa
          </h2>

          <form className="space-y-5" onSubmit={(e) => e.preventDefault()}>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">Nombre de la Empresa</label>
              <input 
                type="text" 
                placeholder="Ej. Mi Negocio S.A."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">Industria</label>
                <select className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500">
                  <option>E-commerce</option>
                  <option>Servicios B2B</option>
                  <option>Bienes Raíces</option>
                  <option>Otro</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">Zona Horaria</label>
                <select className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500">
                  <option>America/Guayaquil (GMT-5)</option>
                  <option>America/Bogota (GMT-5)</option>
                  <option>America/Mexico_City (GMT-6)</option>
                </select>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">Sitio Web</label>
              <input 
                type="url" 
                placeholder="https://www.minegocio.com"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="pt-4 border-t border-slate-800 flex justify-end">
              <button 
                type="submit"
                className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-5 py-2.5 rounded-lg transition-colors"
              >
                Guardar Cambios
              </button>
            </div>
          </form>
        </div>

        {/* Zona de Peligro - Ahora en Configuración */}
        <div className="lg:col-span-3 mt-8">
          <div className="bg-red-500/5 border border-red-500/20 rounded-xl overflow-hidden">
            <div className="bg-red-500/10 px-6 py-4 border-b border-red-500/20 flex items-center gap-3">
              <AlertTriangle className="text-red-500" size={20} />
              <h2 className="text-lg font-bold text-red-500">Zona de Peligro</h2>
            </div>
            <div className="p-6 flex flex-col md:flex-row items-center justify-between gap-6">
              <div>
                <h3 className="text-slate-100 font-bold text-base flex items-center gap-2">
                  <Trash2 size={18} />
                  Vaciar Cerebro de la IA
                </h3>
                <p className="text-slate-400 text-sm mt-1 max-w-xl">
                  Esta acción eliminará permanentemente todos los documentos, textos y productos indexados en el Centro de Datos. Tu agente volverá a su estado base sin conocimientos adicionales.
                </p>
              </div>
              <Button 
                variant="destructive"
                className="rounded-xl px-8 h-12 font-bold shadow-lg shadow-red-500/20"
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
                Vaciar Base de Datos
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
