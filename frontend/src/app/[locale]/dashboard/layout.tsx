"use client";

import { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { CircuitBreakerBanner } from "@/components/system/CircuitBreakerBanner";

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
        // userAvatar="/avatars/user.jpg" // opcional
      />
      
      <main className="flex-1 overflow-y-auto bg-muted/30">
        {/* Banner de circuit breaker (se muestra solo si hay servicios en mantenimiento) */}
        <CircuitBreakerBanner />
        
        {/* Contenido de la página */}
        {children}
      </main>
    </div>
  );
}
