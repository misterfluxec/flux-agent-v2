import React from 'react';

export function SkeletonCard() {
  return (
    <div className="relative overflow-hidden bg-gray-800/40 rounded-xl border border-gray-800/50 p-6 space-y-4 shadow-card">
      {/* Pulse Effect */}
      <div className="animate-pulse flex space-x-4">
        <div className="rounded-full bg-gray-700/50 h-10 w-10"></div>
        <div className="flex-1 space-y-3 py-1">
          <div className="h-2 bg-gray-700/50 rounded w-3/4"></div>
          <div className="space-y-2">
            <div className="grid grid-cols-3 gap-4">
              <div className="h-2 bg-gray-700/50 rounded col-span-2"></div>
              <div className="h-2 bg-gray-700/50 rounded col-span-1"></div>
            </div>
            <div className="h-2 bg-gray-700/50 rounded w-1/2"></div>
          </div>
        </div>
      </div>
      {/* Gradient Overlay for Shine */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full animate-[shimmer_2s_infinite]" />
    </div>
  );
}
