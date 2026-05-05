"use client";

import { useEffect, useState } from "react";
import { Database, Cloud, Settings, Key, Zap, CheckCircle2, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";

type GatewayStatus = {
  evolution_api: { status: string; latency_ms: number };
  cloudflare_tunnel: { status: string; latency_ms: number };
  api_keys: { groq: string; openai: string; stripe: string };
};

export default function GatewaysPage() {
  const [status, setStatus] = useState<GatewayStatus | null>(null);

  useEffect(() => {
    fetchGateways();
  }, []);

  const fetchGateways = async () => {
    try {
      const res = await api.get("/admin/gateways");
      setStatus(res.data);
    } catch (e) {
      console.error("Error fetching gateways", e);
    }
  };

  if (!status) return <div className="p-8 text-center text-slate-400">Analizando conexiones globales...</div>;

  return (
    <div className="space-y-8 animate-entry max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <Database className="w-6 h-6 text-indigo-400" />
          Panel de Puertas de Enlace (Gateways)
        </h1>
        <p className="text-slate-400 text-sm mt-1">Conectividad central de WhatsApp, Túneles y Proveedores IA.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Evolution API */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10"><Zap size={100} /></div>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-emerald-500/10 rounded-xl"><Database className="w-6 h-6 text-emerald-400" /></div>
            <div>
              <h2 className="font-semibold text-lg text-slate-200">Evolution API</h2>
              <p className="text-xs text-slate-500">Motor de Instancias WhatsApp</p>
            </div>
          </div>
          <div className="flex justify-between items-center bg-slate-950 p-4 rounded-xl border border-slate-800">
            <div>
              <p className="text-xs text-slate-500 mb-1">Estado del Servicio</p>
              <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                <CheckCircle2 size={16} /> {status.evolution_api.status.toUpperCase()}
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-slate-500 mb-1">Latencia Core</p>
              <p className="text-slate-300 font-mono text-sm">{status.evolution_api.latency_ms} ms</p>
            </div>
          </div>
        </div>

        {/* Cloudflare Tunnel */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10"><Cloud size={100} /></div>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-blue-500/10 rounded-xl"><Cloud className="w-6 h-6 text-blue-400" /></div>
            <div>
              <h2 className="font-semibold text-lg text-slate-200">Cloudflare Tunnel</h2>
              <p className="text-xs text-slate-500">Exposición Segura al Exterior</p>
            </div>
          </div>
          <div className="flex justify-between items-center bg-slate-950 p-4 rounded-xl border border-slate-800">
            <div>
              <p className="text-xs text-slate-500 mb-1">Estado de Conexión</p>
              <div className="flex items-center gap-1.5 text-blue-400 font-semibold">
                <CheckCircle2 size={16} /> {status.cloudflare_tunnel.status.toUpperCase()}
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-slate-500 mb-1">Latencia a Edge</p>
              <p className="text-slate-300 font-mono text-sm">{status.cloudflare_tunnel.latency_ms} ms</p>
            </div>
          </div>
        </div>

        {/* API Keys */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl md:col-span-2">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-amber-500/10 rounded-xl"><Key className="w-6 h-6 text-amber-400" /></div>
              <div>
                <h2 className="font-semibold text-lg text-slate-200">Gestor de API Keys Globales</h2>
                <p className="text-xs text-slate-500">Credenciales maestras (Encriptadas en BBDD)</p>
              </div>
            </div>
            <button className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg flex items-center gap-2 transition">
              <Settings size={16} /> Administrar Llaves
            </button>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex justify-between items-center">
              <span className="text-sm font-semibold text-slate-300">Groq (Llama 3)</span>
              {status.api_keys.groq === "✓" ? <CheckCircle2 className="text-emerald-500" size={18}/> : <AlertTriangle className="text-red-500" size={18}/>}
            </div>
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex justify-between items-center">
              <span className="text-sm font-semibold text-slate-300">OpenAI</span>
              {status.api_keys.openai === "✓" ? <CheckCircle2 className="text-emerald-500" size={18}/> : <AlertTriangle className="text-red-500" size={18}/>}
            </div>
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex justify-between items-center">
              <span className="text-sm font-semibold text-slate-300">Stripe (Pagos)</span>
              {status.api_keys.stripe === "✓" ? <CheckCircle2 className="text-emerald-500" size={18}/> : <AlertTriangle className="text-red-500" size={18}/>}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
