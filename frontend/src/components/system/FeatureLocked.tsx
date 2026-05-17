"use client";

import React from "react";
import { Lock, ArrowUpCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

interface FeatureLockedProps {
  title?: string;
  description?: string;
  className?: string;
}

export function FeatureLocked({ 
  title = "Función Premium", 
  description = "Mejora tu plan para acceder a esta capacidad operacional.",
  className = ""
}: FeatureLockedProps) {
  const router = useRouter();

  return (
    <div className={`relative overflow-hidden rounded-2xl border border-indigo-100 bg-gradient-to-b from-indigo-50/50 to-white p-8 text-center shadow-sm ${className}`}>
      {/* Decorative background elements */}
      <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-indigo-100/50 blur-2xl" />
      <div className="absolute -left-6 -bottom-6 h-24 w-24 rounded-full bg-blue-100/50 blur-2xl" />
      
      <div className="relative z-10 flex flex-col items-center">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-100 text-indigo-600 ring-4 ring-white shadow-sm">
          <Lock className="h-6 w-6" />
        </div>
        
        <h3 className="mb-2 text-lg font-bold text-slate-800">{title}</h3>
        <p className="mb-6 max-w-sm text-sm text-slate-500">
          {description}
        </p>
        
        <Button 
          onClick={() => router.push('/dashboard/settings/billing')}
          className="bg-indigo-600 text-white hover:bg-indigo-700 font-semibold px-6 shadow-sm"
        >
          <ArrowUpCircle className="mr-2 h-4 w-4" />
          Mejorar Plan
        </Button>
      </div>
    </div>
  );
}
