"use client";

import { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Points, PointMaterial } from "@react-three/drei";
import { motion } from "framer-motion";

function ParticleCloud(props: any) {
  const ref = useRef<any>(null);
  
  const sphere = useMemo(() => {
    const positions = new Float32Array(3000 * 3);
    for (let i = 0; i < 3000; i++) {
      const r = 2.5 * Math.cbrt(Math.random());
      const theta = Math.random() * 2 * Math.PI;
      const phi = Math.acos(2 * Math.random() - 1);
      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = r * Math.cos(phi);
    }
    return positions;
  }, []);

  useFrame((state, delta) => {
    if (ref.current) {
      ref.current.rotation.x -= delta / 10;
      ref.current.rotation.y -= delta / 15;
    }
  });

  return (
    <group rotation={[0, 0, Math.PI / 4]}>
      <Points ref={ref} positions={sphere} stride={3} frustumCulled={false} {...props}>
        <PointMaterial
          transparent
          color="#06b6d4"
          size={0.015}
          sizeAttenuation={true}
          depthWrite={false}
        />
      </Points>
    </group>
  );
}

export function Hero3D() {
  return (
    <section className="relative w-full h-[100svh] flex flex-col items-center justify-center overflow-hidden bg-background">
      {/* 3D Background Layer */}
      <div className="absolute inset-0 z-0">
        <Canvas camera={{ position: [0, 0, 4] }}>
          <ParticleCloud />
        </Canvas>
      </div>

      {/* Massive Typographic Layer - Broken Grid / Brutalist */}
      <div className="z-10 container mx-auto px-4 flex flex-col items-start justify-center pointer-events-none mt-20">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        >
          <p className="text-emerald-400 font-mono text-sm md:text-base tracking-widest uppercase mb-4">
            [ / OS_INIT_SEQUENCE_STARTED ]
          </p>
        </motion.div>
        
        <motion.h1 
          className="text-6xl md:text-8xl lg:text-[10rem] font-black leading-[0.85] tracking-tighter text-white mix-blend-difference"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
        >
          ORQUESTA
          <br />
          <span className="text-emerald-500/90 mix-blend-screen">LA VENTA.</span>
        </motion.h1>

        <motion.div 
          className="mt-8 md:mt-12 max-w-xl pointer-events-auto"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.4 }}
        >
          <p className="text-lg md:text-xl text-slate-300 font-medium leading-relaxed border-l-2 border-cyan-500 pl-4 mb-8">
            No contrates un bot plano. Despliega un Sistema Operativo Comercial que razona, negocia y cobra de manera autónoma, 24/7.
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <button className="bg-emerald-500 hover:bg-emerald-400 text-black font-bold px-8 py-4 rounded-none transition-all duration-300 hover:translate-x-1 hover:-translate-y-1 hover:shadow-[4px_4px_0px_#06b6d4]">
              Desplegar Agente
            </button>
            <button className="border border-slate-600 hover:border-white text-white px-8 py-4 rounded-none transition-all duration-300 bg-black/20 backdrop-blur-md">
              Ver Demo Técnica
            </button>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
