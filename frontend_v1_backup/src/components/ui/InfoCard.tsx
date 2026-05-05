import { Info, Lightbulb } from 'lucide-react';

export function InfoCard({ title, description, tip }: { title: string; description: string; tip: string }) {
  return (
    <div className="bg-[#111111] border border-gray-800 rounded-xl p-5 space-y-3">
      <div className="flex items-start gap-3">
        <Info className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
        <div>
          <h3 className="font-semibold text-white">{title}</h3>
          <p className="text-sm text-gray-400 mt-1 leading-relaxed">{description}</p>
        </div>
      </div>
      {tip && (
        <div className="flex items-start gap-2 bg-blue-500/5 border border-blue-500/10 rounded-lg p-3 text-xs text-gray-300">
          <Lightbulb className="w-4 h-4 text-yellow-400 shrink-0 mt-0.5" />
          {tip}
        </div>
      )}
    </div>
  );
}
