"use client";

import { motion } from "framer-motion";

const features = [
  {
    num: "01",
    title: "Inteligencia Orquestada.",
    desc: "Un agente de ventas que colabora en tiempo real con un agente de soporte. Comunicación inter-agentes para resolver el 100% del ticket del usuario sin intervención humana.",
    align: "left"
  },
  {
    num: "02",
    title: "Conciliación Instantánea.",
    desc: "Olvídate de las capturas de pantalla de transferencias. Cobro regional nativo conectado a tu base de datos, validando pagos al instante.",
    align: "right"
  },
  {
    num: "03",
    title: "Políticas Inquebrantables.",
    desc: "SOPs (Procedimientos Operativos) estrictos y cumplimiento forzado. Cero alucinaciones. Si no está en el manual, no se ofrece.",
    align: "left"
  }
];

export function FeatureZigZag() {
  return (
    <section className="py-32 bg-background relative border-t border-white/[0.02]">
      <div className="container mx-auto px-4 max-w-6xl">
        {features.map((feature, idx) => (
          <motion.div 
            key={idx}
            initial={{ opacity: 0, y: 100 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className={`flex flex-col mb-32 last:mb-0 ${
              feature.align === "left" ? "md:items-start text-left" : "md:items-end md:text-right"
            }`}
          >
            <div className="flex flex-col relative w-full md:w-2/3">
              <span className="absolute -top-20 -left-10 text-[10rem] font-black text-white/[0.03] select-none pointer-events-none -z-10">
                {feature.num}
              </span>
              <h3 className="text-4xl md:text-6xl font-black text-white tracking-tighter mb-6 mix-blend-difference">
                {feature.title}
              </h3>
              <p className="text-xl md:text-2xl text-slate-400 font-medium leading-relaxed max-w-xl">
                {feature.desc}
              </p>
            </div>
            {/* Visual Abstract representation to avoid cliché images */}
            <div className={`w-full md:w-1/2 h-1 mt-12 bg-gradient-to-r from-emerald-500 to-cyan-500 ${feature.align === "left" ? "self-start origin-left" : "self-end origin-right"} opacity-20`} />
          </motion.div>
        ))}
      </div>
    </section>
  );
}
