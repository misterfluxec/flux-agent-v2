import { FeatureFlag } from './featureRegistry';
import {
  LayoutDashboard,
  MessageSquare,
  ShoppingCart,
  FileText,
  Package,
  Users2,
  Database,
  BarChart3,
  Bot,
  Plug,
  Zap,
  UserCircle
} from "lucide-react";

export interface MenuItem {
  id?: string;
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
  badge?: {
    label: string;
    variant?: "default" | "secondary" | "destructive" | "outline";
  };
  children?: Array<{
    label: string;
    href: string;
    description?: string;
  }>;
  feature: FeatureFlag;
}

export interface MenuSection {
  id?: string;
  title: string;
  items: MenuItem[];
}

export const MENU_REGISTRY: MenuSection[] = [
  {
    title: 'OPERAR',
    items: [
      { label: 'Control', href: '/dashboard', icon: LayoutDashboard, feature: 'view_dashboard' },
      { label: 'Conversaciones', href: '/dashboard/operations', icon: MessageSquare, feature: 'view_operations' },
    ]
  },
  {
    title: 'COMERCIO',
    items: [
      { label: 'Catálogo', href: '/dashboard/inventory', icon: ShoppingCart, feature: 'view_catalog' },
      { label: 'Cotizaciones', href: '/dashboard/quotes', icon: FileText, feature: 'view_quotes' },
      { label: 'Órdenes', href: '/dashboard/orders', icon: Package, feature: 'view_orders' },
    ]
  },
  {
    title: 'CRM',
    items: [
      { label: 'Pipeline de Leads', href: '/dashboard/crm', icon: Users2, feature: 'view_crm' },
      { label: 'Clientes (360)', href: '/dashboard/customers', icon: UserCircle, feature: 'view_crm' },
    ]
  },
  {
    title: 'INTELIGENCIA',
    items: [
      { label: 'Conexiones ETL', href: '/dashboard/intelligence', icon: Database, feature: 'manage_connections' },
      { label: 'Analytics', href: '/dashboard/analytics', icon: BarChart3, feature: 'view_analytics' },
    ]
  },
  {
    title: 'CONFIGURAR',
    items: [
      { label: 'Agentes', href: '/dashboard/agents', icon: Bot, feature: 'manage_agents' },
      { label: 'Canales', href: '/dashboard/channels', icon: Plug, feature: 'manage_channels' },
      { label: 'Flujos', href: '/dashboard/flows', icon: Zap, feature: 'manage_flows' },
    ]
  }
];
