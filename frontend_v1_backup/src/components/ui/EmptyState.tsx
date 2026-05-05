import React from 'react';
import { LucideIcon } from 'lucide-react';

interface Props {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({ icon: Icon, title, description, action }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center animate-slide-up">
      <div className="relative mb-6">
        <div className="absolute -inset-4 bg-gray-800/30 blur-2xl rounded-full" />
        <div className="relative p-6 bg-gray-900/50 border border-gray-800/50 rounded-full shadow-xl">
          <Icon className="w-10 h-10 text-gray-600" />
        </div>
      </div>
      <h3 className="text-xl font-bold text-gray-200 tracking-tight">{title}</h3>
      <p className="text-sm text-gray-500 max-w-sm mt-3 leading-relaxed">
        {description}
      </p>
      {action && (
        <button 
          onClick={action.onClick}
          className="mt-8 px-8 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-black transition-all shadow-lg shadow-indigo-600/20 active:scale-95"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
