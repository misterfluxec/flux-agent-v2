'use client';
import React from 'react';
import { Shield, Server } from 'lucide-react';

export const SmartInfra = ({ content }: { content: any }) => (
  <section className="py-24 px-6 relative bg-gradient-to-b from-[#0a0a0f] to-[#12121a] border-t border-white/5 overflow-hidden">
    <div className="max-w-6xl mx-auto">
      <div className="grid lg:grid-cols-2 gap-16 items-center">
        <div>
          <span className="text-emerald-400 text-sm font-semibold tracking-widest uppercase mb-4 block">{content.badge}</span>
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            {content.title_1}
            <br />
            <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">{content.title_2}</span>
          </h2>
          <p className="text-xl text-gray-400 mb-8 leading-relaxed">
            {content.subtitle}
          </p>
          <ul className="space-y-4">
            {content.points.map((point: string, i: number) => (
              <li key={i} className="flex items-start gap-3">
                <Shield className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
                <span className="text-gray-300">{point}</span>
              </li>
            ))}
          </ul>
        </div>
        
        <div className="relative">
          <div className="absolute inset-0 bg-emerald-500/10 blur-3xl rounded-full" />
          <div className="relative bg-[#0a0a0f] border border-white/10 rounded-2xl p-8 shadow-2xl overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 to-cyan-500" />
            <div className="flex items-center gap-3 mb-6">
              <Server className="w-5 h-5 text-emerald-400" />
              <span className="text-sm font-mono text-emerald-400">STATUS: PROTECTED</span>
            </div>
            <div className="space-y-4 font-mono text-xs md:text-sm">
              <div className="flex justify-between items-center bg-white/5 p-3 rounded">
                <span className="text-gray-400">Data Sovereignty</span>
                <span className="text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">LOCAL</span>
              </div>
              <div className="flex justify-between items-center bg-white/5 p-3 rounded">
                <span className="text-gray-400">Compute Core</span>
                <span className="text-cyan-400 bg-cyan-500/10 px-2 py-1 rounded">HYBRID</span>
              </div>
              <div className="flex justify-between items-center bg-white/5 p-3 rounded">
                <span className="text-gray-400">Privacy Mode</span>
                <span className="text-purple-400 bg-purple-500/10 px-2 py-1 rounded">ACTIVE</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
);
