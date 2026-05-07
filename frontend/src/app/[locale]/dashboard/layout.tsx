'use client';

import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import { useTranslations } from 'next-intl';
import { useState } from 'react';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const t = useTranslations('nav');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Estructura Flexbox rígida para evitar desbordes
  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      
      {/* Sidebar Desktop (Fijo) */}
      <div className="hidden lg:flex lg:flex-shrink-0">
        <div className="w-64 flex flex-col bg-card border-r border-border">
          <Sidebar />
        </div>
      </div>

      {/* Sidebar Mobile (Overlay) */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div className="fixed inset-0 bg-black/50" onClick={() => setSidebarOpen(false)} />
          <div className="relative w-64 flex flex-col bg-card border-r border-border animate-in slide-in-from-left">
            <Sidebar />
          </div>
        </div>
      )}

      {/* Área Principal */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header fijo superior */}
        <Header onMenuToggle={() => setSidebarOpen(true)} />
        
        {/* Contenido scrolleable independiente */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 bg-muted/20">
          <div className="mx-auto max-w-7xl">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
