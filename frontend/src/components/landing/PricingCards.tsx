"use client";

import { motion } from "framer-motion";

export function PricingCards() {
  return (
    <section className="py-32 bg-[#020617] relative">
      <div className="container mx-auto px-4">
        <div className="text-center mb-24">
          <h2 className="text-5xl md:text-7xl font-black text-white tracking-tighter mb-6">
            Potencia <span className="text-emerald-500">Operativa.</span>
          </h2>
          <p className="text-xl text-slate-400 font-medium max-w-2xl mx-auto">
            Deja de calcular "gastos de software" y empieza a medir tu capacidad de ejecución.
          </p>
        </div>

        <div className="flex flex-col md:flex-row gap-8 justify-center items-stretch max-w-5xl mx-auto">
          {/* Base Plan */}
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="flex-1 p-8 border border-white/10 bg-black/40 rounded-none flex flex-col"
          >
            <h3 className="text-2xl font-bold text-white mb-2">Agente Base</h3>
            <div className="text-4xl font-black text-white mb-6">$99<span className="text-lg text-slate-500 font-normal">/mes</span></div>
            <ul className="space-y-4 mb-8 flex-1 text-slate-400">
              <li className="flex gap-2 items-center">
                <div className="w-1.5 h-1.5 bg-cyan-500" />
                Voz y Texto Ilimitado
              </li>
              <li className="flex gap-2 items-center">
                <div className="w-1.5 h-1.5 bg-cyan-500" />
                Flujos de Venta SOP
              </li>
              <li className="flex gap-2 items-center">
                <div className="w-1.5 h-1.5 bg-cyan-500" />
                Conciliación Manual
              </li>
            </ul>
            <button className="w-full py-4 border border-slate-700 hover:border-cyan-500 text-white transition-colors">
              Iniciar Base
            </button>
          </motion.div>

          {/* Pro Plan - Elevated */}
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: -20 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="flex-1 p-8 border border-emerald-500/30 bg-emerald-950/20 backdrop-blur-md rounded-none flex flex-col relative shadow-[0_20px_50px_-12px_rgba(16,185,129,0.15)]"
          >
            <div className="absolute top-0 right-0 bg-emerald-500 text-black text-xs font-bold px-3 py-1 uppercase tracking-wider">
              Autónomo
            </div>
            <h3 className="text-2xl font-bold text-white mb-2">Agente Pro</h3>
            <div className="text-4xl font-black text-emerald-400 mb-6">$299<span className="text-lg text-emerald-700 font-normal">/mes</span></div>
            <ul className="space-y-4 mb-8 flex-1 text-emerald-100/70">
              <li className="flex gap-2 items-center">
                <div className="w-1.5 h-1.5 bg-emerald-500" />
                Todo lo del Base
              </li>
              <li className="flex gap-2 items-center">
                <div className="w-1.5 h-1.5 bg-emerald-500" />
                Orquestación Multi-Agente
              </li>
              <li className="flex gap-2 items-center">
                <div className="w-1.5 h-1.5 bg-emerald-500" />
                Conexión a BD y Pagos
              </li>
              <li className="flex gap-2 items-center">
                <div className="w-1.5 h-1.5 bg-emerald-500" />
                Soporte Prioritario
              </li>
            </ul>
            <button className="w-full py-4 bg-emerald-500 hover:bg-emerald-400 text-black font-bold transition-colors shadow-[0_0_20px_rgba(16,185,129,0.3)]">
              Desplegar OS
            </button>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
