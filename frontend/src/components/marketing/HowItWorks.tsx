'use client';
import React from 'react';

export const HowItWorks = ({ content }: { content: any }) => (
  <section className="py-24 px-6 relative bg-white/5 border-t border-white/10 overflow-hidden">
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-16">
        <span className="text-purple-400 text-sm font-semibold tracking-widest uppercase mb-4 block">{content.badge}</span>
        <h2 className="text-4xl md:text-5xl font-bold mb-6">
          {content.title_1}
          <br />
          <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">{content.title_2}</span>
        </h2>
      </div>

      <div className="grid md:grid-cols-3 gap-8 relative">
        <div className="hidden md:block absolute top-12 left-[15%] right-[15%] h-0.5 bg-gradient-to-r from-purple-500/0 via-purple-500/50 to-cyan-500/0"></div>
        {content.items.map((item: any, idx: number) => (
          <div key={idx} className="relative z-10 text-center p-6">
            <div className="w-24 h-24 mx-auto bg-[#0a0a0f] border-2 border-purple-500/30 rounded-2xl flex items-center justify-center mb-6 shadow-xl shadow-purple-500/10 rotate-3 hover:rotate-0 transition-transform">
              <span className="text-4xl font-black bg-gradient-to-br from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                {item.step}
              </span>
            </div>
            <h3 className="text-xl font-bold mb-3">{item.title}</h3>
            <p className="text-gray-400 leading-relaxed text-sm md:text-base">{item.description}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);
