"use client";

import { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { CircuitBreakerBanner } from "@/components/system/CircuitBreakerBanner";
import { OperationalHealthBar } from "@/components/system/OperationalHealthBar";
import { CommandPalette } from "@/components/layout/CommandPalette";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        tenantName="Mi Empresa"
        userName="Usuario"
      />
      
      <main className="flex-1 flex flex-col overflow-hidden bg-[#0A0A0B]">
        {/* Global Operational Health Bar */}
        <OperationalHealthBar />
        
        {/* Circuit breaker (solo si hay servicios caídos) */}
        <CircuitBreakerBanner />
        
        {/* Contenido de la página con scroll */}
        <div className="flex-1 overflow-y-auto">
          {children}
        </div>
      </main>
      
      {/* Cmd+K Global Palette (Yanua Overlay) */}
      <CommandPalette />
    </div>
  );
}
