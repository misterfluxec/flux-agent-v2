"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";

export function LiveChatSimulation() {
  const [messages, setMessages] = useState<any[]>([]);

  useEffect(() => {
    // Sequence of conversation
    const sequence = [
      { type: "user", text: "Hola, necesito renovar mi plan pro por 6 meses más.", delay: 1000 },
      { type: "system", text: "[Action: Check DB] -> Status: Active | Rate: $99", delay: 2500 },
      { type: "agent", text: "¡Claro! Te he aplicado el descuento semestral. Son $495 en total. ¿Te envío el link de pago?", delay: 4000 },
      { type: "user", text: "Sí, por favor.", delay: 5500 },
      { type: "system", text: "[Action: Generate Stripe Link] -> Link generated.", delay: 7000 },
      { type: "agent", text: "Aquí tienes: https://pay.fluxagent.io/x1y2. Se activará automáticamente al pagar.", delay: 8500 },
    ];

    let timeouts: NodeJS.Timeout[] = [];

    sequence.forEach((msg) => {
      const t = setTimeout(() => {
        setMessages((prev) => [...prev, msg]);
      }, msg.delay);
      timeouts.push(t);
    });

    return () => timeouts.forEach(clearTimeout);
  }, []);

  return (
    <section className="relative py-24 bg-[#020617] overflow-hidden">
      <div className="container mx-auto px-4 flex flex-col lg:flex-row items-center gap-12">
        
        {/* Left Side: The Chat Interface */}
        <div className="w-full lg:w-1/2">
          <motion.div 
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="flux-glass p-6 rounded-2xl h-[500px] flex flex-col overflow-y-auto space-y-4"
          >
            <div className="border-b border-white/10 pb-4 mb-4 flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-emerald-500 flux-glow-green animate-pulse" />
              <span className="font-mono text-sm text-emerald-400 uppercase tracking-widest">FluxAgent Voice/Text</span>
            </div>
            
            {messages.filter(m => m.type !== "system").map((msg, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`max-w-[80%] p-4 rounded-2xl text-sm ${
                  msg.type === "user" 
                    ? "bg-slate-800 text-white self-start rounded-tl-sm" 
                    : "bg-emerald-900/40 border border-emerald-500/20 text-emerald-100 self-end rounded-tr-sm"
                }`}
              >
                {msg.text}
              </motion.div>
            ))}
          </motion.div>
        </div>

        {/* Right Side: The Terminal/System Thinking */}
        <div className="w-full lg:w-1/2">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 text-white tracking-tight">
            Transparencia <span className="text-cyan-400">Total.</span>
          </h2>
          <p className="text-slate-400 text-lg mb-8 leading-relaxed">
            Mientras el agente negocia con el cliente de forma empática, tú tienes acceso en tiempo real a su "hilo de pensamiento". 
            Conoce exactamente qué APIs está consultando y qué reglas está aplicando.
          </p>

          <motion.div 
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="bg-black border border-cyan-900/50 p-6 rounded-xl font-mono text-sm md:text-base text-cyan-400 h-[300px] overflow-y-auto"
          >
            <div className="text-slate-500 mb-4">// System Log: Negotiation Sequence</div>
            {messages.filter(m => m.type === "system").map((msg, i) => (
              <motion.div 
                key={`sys-${i}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mb-3"
              >
                <span className="text-emerald-500">{`> `}</span>
                {msg.text}
              </motion.div>
            ))}
            <motion.div 
              animate={{ opacity: [1, 0] }}
              transition={{ repeat: Infinity, duration: 0.8 }}
              className="inline-block w-2 h-4 bg-cyan-400 mt-2"
            />
          </motion.div>
        </div>

      </div>
    </section>
  );
}
