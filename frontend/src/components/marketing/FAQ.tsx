'use client';
import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

export const FAQ = ({ content }: { content: any }) => {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <section className="py-24 px-6 relative border-t border-white/5 bg-black/50">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-16">
          <span className="text-amber-400 text-sm font-semibold tracking-widest uppercase mb-4 block">{content.badge}</span>
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            {content.title_1}{' '}
            <span className="bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">{content.title_2}</span>
          </h2>
        </div>

        <div className="space-y-4">
          {content.items.slice(0, 5).map((item: any, i: number) => (
            <div 
              key={i} 
              className="border border-white/10 rounded-xl bg-white/[0.02] overflow-hidden"
            >
              <button 
                onClick={() => setOpen(open === i ? null : i)}
                className="w-full flex items-center justify-between p-6 text-left"
              >
                <span className="font-bold text-lg">{item.q}</span>
                <ChevronDown className={cn("w-5 h-5 text-gray-400 transition-transform", open === i && "rotate-180")} />
              </button>
              {open === i && (
                <div className="px-6 pb-6 text-gray-400 leading-relaxed">
                  {item.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
