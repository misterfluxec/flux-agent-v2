"use client";

import { ReactNode, useState } from "react";
import Link from "next/link";
import { 
  ShieldAlert, 
  Activity, 
  Users, 
  Server, 
  Ticket, 
  Database, 
  LogOut, 
  Cpu, 
  Settings, 
  Terminal, 
  MessageSquare, 
  Bell, 
  ChevronDown, 
  ChevronRight,
  Search,
  Moon,
  LayoutDashboard,
  Box,
  Key,
  Bot
} from "lucide-react";
import { usePathname } from "next/navigation";

type SidebarItem = {
    name: string;
    href?: string;
    icon: any;
    subItems?: { name: string; href: string }[];
};

export default function SuperAdminLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [openMenus, setOpenMenus] = useState<Record<string, boolean>>({
    "Dashboard": true,
    "IA Ops": true,
    "SaaS Management": true
  });

  const toggleMenu = (name: string) => {
    setOpenMenus(prev => ({ ...prev, [name]: !prev[name] }));
  };

const sections: { category: string; items: SidebarItem[] }[] = [
    {
        category: "Principal",
        items: [
            { name: "Dashboard NOC", href: "/superadmin", icon: LayoutDashboard },
        ]
    },
    {
        category: "Gestión SaaS",
        items: [
            { name: "Tenants HQ", href: "/superadmin/tenants", icon: Server },
            { name: "Planes y Billing", href: "/superadmin/billing", icon: Key },
            { name: "Staff del Sistema", href: "/superadmin/staff", icon: Users },
        ]
    },
    {
        category: "AI Control Room",
        items: [
            { name: "Modelos (Cerebros)", href: "/superadmin/models", icon: Cpu },
            { name: "Agentes Globales", href: "/superadmin/agents", icon: Bot },
        ]
    },
    {
        category: "Soporte & CX",
        items: [
            { name: "Tickets de Soporte", href: "/superadmin/tickets", icon: Ticket },
            { name: "Chat en Vivo", href: "/superadmin/chat", icon: MessageSquare },
        ]
    },
    {
        category: "Infraestructura",
        items: [
            { name: "Gateways (Evolution)", href: "/superadmin/gateways", icon: Database },
            { name: "Logs & Auditoría", href: "/superadmin/logs", icon: Activity },
            { name: "Terminal", href: "/superadmin/terminal", icon: Terminal },
        ]
    }
];

  return (
    <div className="flex h-screen bg-[#020617] text-slate-100 font-sans">
      {/* Sidebar Profesional */}
      <aside className="w-72 bg-[#020617] border-r border-slate-800/50 hidden md:flex flex-col">
        <div className="h-20 flex items-center px-8 border-b border-slate-800/50">
          <div className="bg-emerald-500/10 p-2 rounded-lg border border-emerald-500/20 mr-3">
            <ShieldAlert className="w-5 h-5 text-emerald-500" />
          </div>
          <div className="flex flex-col">
            <span className="font-black text-sm tracking-tighter uppercase italic leading-none">FluxAgent V2</span>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-[0.2em] mt-1">Super Admin NOC</span>
          </div>
        </div>

        <nav className="flex-1 px-4 py-8 space-y-8 overflow-y-auto scrollbar-hide">
          {sections.map((sec) => (
            <div key={sec.category}>
              <h3 className="px-4 text-[10px] font-black text-slate-600 uppercase tracking-[0.25em] mb-4">
                {sec.category}
              </h3>
              <div className="space-y-1">
                {sec.items.map((item) => {
                  const active = pathname === item.href;
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.name}
                      href={item.href || "#"}
                      className={`group flex items-center justify-between px-4 py-2.5 rounded-xl text-sm transition-all duration-200 ${
                        active
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-[0_0_15px_-5px_rgba(16,185,129,0.2)]"
                          : "text-slate-400 hover:text-slate-100 hover:bg-slate-900/50"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <Icon className={`w-4 h-4 transition-transform group-hover:scale-110 ${active ? 'text-emerald-400' : 'text-slate-500'}`} />
                        <span className="font-medium tracking-tight">{item.name}</span>
                      </div>
                      {active && <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]" />}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        <div className="p-6 border-t border-slate-800/50">
          <Link
            href="/login"
            className="flex items-center justify-center gap-3 w-full px-4 py-3 rounded-xl text-xs font-bold text-slate-400 bg-slate-900/50 hover:bg-red-500/10 hover:text-red-400 border border-slate-800 hover:border-red-500/20 transition-all"
          >
            <LogOut className="w-4 h-4" />
            Cerrar Sesión Segura
          </Link>
        </div>
      </aside>

      {/* Main Area con Header Superior */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden bg-gradient-to-br from-[#020617] to-[#0f172a]">
        {/* Header Superior estilo Glassmorphism */}
        <header className="h-20 border-b border-slate-800/50 backdrop-blur-md bg-[#020617]/50 px-8 flex items-center justify-between z-10">
          <div className="flex items-center gap-6 flex-1">
             <div className="relative w-96">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600" />
                <input 
                    type="text" 
                    placeholder="Búsqueda global (Tenants, Tickets, Logs...)"
                    className="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-2.5 pl-10 pr-4 text-sm text-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-500/30 transition-all"
                />
             </div>
          </div>

          <div className="flex items-center gap-4">
            <button className="p-2.5 rounded-xl hover:bg-slate-800 text-slate-400 transition-colors relative">
                <Bell className="w-4 h-4" />
                <div className="absolute top-2.5 right-2.5 w-1.5 h-1.5 bg-red-500 rounded-full border-2 border-[#020617]" />
            </button>
            <button className="p-2.5 rounded-xl hover:bg-slate-800 text-slate-400 transition-colors">
                <Moon className="w-4 h-4" />
            </button>
            <div className="h-8 w-px bg-slate-800 mx-2" />
            <div className="flex items-center gap-3 pl-2">
                <div className="flex flex-col text-right">
                    <span className="text-sm font-bold text-slate-200">Admin Flux</span>
                    <span className="text-[10px] text-emerald-500 font-bold uppercase tracking-tighter">Super Admin</span>
                </div>
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-blue-600 border border-white/10 shadow-lg flex items-center justify-center font-bold text-white">
                    AD
                </div>
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-8 relative">
          {/* Grid Background Decorativo */}
          <div className="absolute inset-0 pointer-events-none opacity-[0.03]" 
               style={{ backgroundImage: 'radial-gradient(circle, #4ade80 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
          
          <div className="relative z-10 max-w-7xl mx-auto">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}

function BotIcon(props: any) {
    return (
        <svg {...props} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 8V4H8" /><rect width="16" height="12" x="4" y="8" rx="2" /><path d="M2 14h2" /><path d="M20 14h2" /><path d="M15 13v2" /><path d="M9 13v2" />
        </svg>
    )
}
