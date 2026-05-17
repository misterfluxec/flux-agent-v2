'use client';
import React from 'react';

export const Industries = ({ content }: { content: any }) => (
  <section className="py-24 px-6 relative overflow-hidden">
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-16">
        <span className="text-cyan-400 text-sm font-semibold tracking-widest uppercase mb-4 block">{content.badge}</span>
        <h2 className="text-4xl md:text-5xl font-bold mb-6">
          {content.title_1}{' '}
          <span className="bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent">{content.title_2}</span>
        </h2>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {content.items.slice(0, 4).map((item: any, idx: number) => (
          <div key={idx} className="group p-6 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
            <div className="text-4xl mb-4 group-hover:scale-110 transition-transform origin-left">{item.icon}</div>
            <h3 className="text-lg font-bold mb-2">{item.name}</h3>
            <p className="text-gray-400 text-sm leading-relaxed">{item.description}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);
