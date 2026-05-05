'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTranslations, useLocale } from 'next-intl';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LayoutDashboard, Bot, MessageSquare, Plug, BarChart3, Settings, 
  LogOut, Database, Contact2, Package, TestTube2,
  FileCode2, MessageCircle, FileBarChart, Loader2, ChevronDown
} from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const mainItems = [
  { href: '/dashboard', icon: LayoutDashboard, labelKey: 'dashboard' },
  { href: '/dashboard/agent', icon: Bot, labelKey: 'my_agent' },
  { href: '/dashboard/conversations', icon: MessageSquare, labelKey: 'conversations' },
  { href: '/dashboard/analytics', icon: BarChart3, labelKey: 'analytics' },
];

const integrationItems = [
  { href: '/dashboard/connectors', icon: Plug, labelKey: 'connectors' },
  { href: '/dashboard/data-ingestion', icon: Database, labelKey: 'data_center', hasDesc: true },
  { href: '/dashboard/script-editor', icon: FileCode2, labelKey: 'scripts', hasDesc: true },
];

const toolItems = [
  { href: '/dashboard/crm', icon: Contact2, labelKey: 'crm', isNew: true, hasDesc: true },
  { href: '/dashboard/inventory', icon: Package, labelKey: 'inventory', isNew: true, hasDesc: true },
  { href: '/dashboard/testing', icon: TestTube2, labelKey: 'testing', hasDesc: true },
  { href: '/dashboard/chat-playground', icon: MessageCircle, labelKey: 'chat_playground', hasDesc: true },
  { href: '/dashboard/reports', icon: FileBarChart, labelKey: 'reports', hasDesc: true },
];

const adminItems = [
  { 
    href: '/dashboard/settings', 
    icon: Settings, 
    labelKey: 'settings',
    children: [
      { labelKey: 'settings_general', href: '/dashboard/settings' },
      { labelKey: 'settings_team', href: '/dashboard/settings/team' },
      { labelKey: 'settings_billing', href: '/dashboard/settings/billing' }
    ]
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const locale = useLocale();
  const t = useTranslations('nav');
  const [isSettingsOpen, setIsSettingsOpen] = useState(pathname.includes('/settings'));
  const [navigatingHref, setNavigatingHref] = useState<string | null>(null);

  // Reset loading state when pathname changes
  useEffect(() => {
    setNavigatingHref(null);
  }, [pathname]);

  const renderLinks = (items: any[], isChild = false) => items.map((item) => {
    const isActive = item.href === '/dashboard' 
        ? pathname === '/dashboard' || pathname === `/${locale}/dashboard`
        : pathname.endsWith(item.href);
    
    const hasChildren = item.children && item.children.length > 0;
    const isNavigating = navigatingHref === item.href;

    const linkContent = (
      <Link
        href={item.href.startsWith('/') ? `/${locale}${item.href}` : item.href}
        onClick={() => {
          if (hasChildren) {
            setIsSettingsOpen(!isSettingsOpen);
          } else {
            setNavigatingHref(item.href);
          }
        }}
        className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
          isActive && !isChild
            ? 'bg-primary/10 text-primary' 
            : isChild && isActive
            ? 'text-primary font-bold'
            : 'text-muted-foreground hover:bg-accent hover:text-foreground'
        } ${isChild ? 'ml-9 pl-4 py-1.5 text-xs border-l-2' : ''} ${
          isChild && isActive ? 'border-primary' : isChild ? 'border-transparent' : ''
        } ${isNavigating ? 'opacity-70 grayscale-[0.5]' : ''}`}
      >
        {!isChild && <item.icon className={`w-4 h-4 ${isActive ? 'text-primary' : ''}`} />}
        <span className="flex-1">{t(item.labelKey)}</span>
        
        {isNavigating && <Loader2 className="w-3 h-3 animate-spin text-primary" />}
        
        {item.isNew && (
          <span className="px-1.5 py-0.5 text-[8px] font-black bg-primary text-primary-foreground rounded-full animate-pulse">
            NEW
          </span>
        )}

        {hasChildren && (
          <ChevronDown className={`w-3 h-3 transition-transform duration-200 ${isSettingsOpen ? 'rotate-180' : ''}`} />
        )}
      </Link>
    );

    return (
      <div key={item.href} className="space-y-1">
        {item.hasDesc ? (
          <Tooltip>
            <TooltipTrigger asChild>
              {linkContent}
            </TooltipTrigger>
            <TooltipContent side="right" className="bg-popover text-popover-foreground border-border shadow-xl">
              <p className="text-xs font-medium">{t(`${item.labelKey}_desc` as any)}</p>
            </TooltipContent>
          </Tooltip>
        ) : (
          linkContent
        )}

        {hasChildren && (
          <AnimatePresence>
            {isSettingsOpen && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2, ease: "easeInOut" }}
                className="overflow-hidden"
              >
                <div className="space-y-1 pb-1">
                  {renderLinks(item.children, true)}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        )}
      </div>
    );
  });

  return (
    <div className="flex flex-col h-full bg-card border-r border-border shadow-sm">
      {/* Logo Area */}
      <div className="h-16 flex items-center px-6 border-b border-border shrink-0">
        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center mr-3 shadow-lg shadow-primary/20">
          <Bot className="w-5 h-5 text-primary-foreground" />
        </div>
        <span className="text-xl font-black tracking-tight bg-gradient-to-r from-primary to-blue-500 bg-clip-text text-transparent">
          FluxAgent
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-6 px-3 space-y-8 custom-scrollbar">
        <div>
          <p className="px-3 mb-3 text-[10px] font-black tracking-[0.2em] text-muted-foreground/60 uppercase">General</p>
          <div className="space-y-1">
            {renderLinks(mainItems)}
          </div>
        </div>

        <div>
          <p className="px-3 mb-3 text-[10px] font-black tracking-[0.2em] text-muted-foreground/60 uppercase">Conocimiento</p>
          <div className="space-y-1">
            {renderLinks(integrationItems)}
          </div>
        </div>

        <div>
          <p className="px-3 mb-3 text-[10px] font-black tracking-[0.2em] text-muted-foreground/60 uppercase">Herramientas</p>
          <div className="space-y-1">
            {renderLinks(toolItems)}
          </div>
        </div>
      </nav>

      {/* Footer Admin */}
      <div className="p-3 border-t border-border space-y-1 bg-muted/30 shrink-0">
        <p className="px-3 mb-3 text-[10px] font-black tracking-[0.2em] text-muted-foreground/60 uppercase mt-2">Configuración</p>
        {renderLinks(adminItems)}
        
        <button className="w-full flex items-center gap-3 px-3 py-2 mt-4 text-sm text-red-500 font-bold hover:bg-red-500/10 rounded-md transition-all group">
          <div className="p-1.5 rounded-md bg-red-500/10 group-hover:bg-red-500/20 transition-colors">
            <LogOut className="w-3.5 h-3.5" />
          </div>
          Cerrar Sesión
        </button>
      </div>
    </div>
  );
}
