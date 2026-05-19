import { FeatureFlag } from './featureRegistry';
import {
  LayoutDashboard,
  MessageSquare,
  ShoppingCart,
  FileText,
  Package,
  Archive,
  Tag,
  Users2,
  UserCircle,
  Activity,
  BarChart3,
  Lightbulb,
  BrainCircuit,
  Bot,
  Plug,
  Zap,
  BookOpen,
  Shield,
  CreditCard
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
      { label: 'Catálogo', href: '/dashboard/inventory', icon: ShoppingCart, feature: 'view_catalog', badge: { label: 'NUEVO', variant: 'default' } },
      { label: 'Cotizaciones', href: '/dashboard/quotes', icon: FileText, feature: 'view_quotes', badge: { label: 'NUEVO', variant: 'default' } },
      { label: 'Órdenes', href: '/dashboard/orders', icon: Package, feature: 'view_orders', badge: { label: 'NUEVO', variant: 'default' } },
      { label: 'Inventario', href: '/dashboard/stock', icon: Archive, feature: 'view_catalog', badge: { label: 'NUEVO', variant: 'default' } },
      { label: 'Promociones', href: '/dashboard/promotions', icon: Tag, feature: 'view_catalog', badge: { label: 'NUEVO', variant: 'default' } },
    ]
  },
  {
    title: 'CRM',
    items: [
      { label: 'Pipeline', href: '/dashboard/crm', icon: Users2, feature: 'view_crm', badge: { label: 'NUEVO', variant: 'default' } },
      { label: 'Clientes', href: '/dashboard/customers', icon: UserCircle, feature: 'view_crm', badge: { label: 'NUEVO', variant: 'default' } },
      { label: 'Seguimientos', href: '/dashboard/followups', icon: Activity, feature: 'view_crm', badge: { label: 'NUEVO', variant: 'default' } },
    ]
  },
  {
    title: 'INTELIGENCIA',
    items: [
      { label: 'Analytics', href: '/dashboard/analytics', icon: BarChart3, feature: 'view_analytics', badge: { label: 'NUEVO', variant: 'default' } },
      { label: 'Insights', href: '/dashboard/insights', icon: Lightbulb, feature: 'view_analytics', badge: { label: 'NUEVO', variant: 'default' } },
      { label: 'AI Copilot', href: '/dashboard/copilot', icon: BrainCircuit, feature: 'view_analytics', badge: { label: 'NUEVO', variant: 'default' } },
    ]
  },
  {
    title: 'CONFIGURAR',
    items: [
      { label: 'Agentes', href: '/dashboard/agents', icon: Bot, feature: 'manage_agents', badge: { label: 'NUEVO', variant: 'default' } },
      { label: 'Canales', href: '/dashboard/channels', icon: Plug, feature: 'manage_channels', badge: { label: 'NUEVO', variant: 'default' } },
      { label: 'Flujos', href: '/dashboard/flows', icon: Zap, feature: 'manage_flows', badge: { label: 'NUEVO', variant: 'default' } },
      { label: 'Conocimiento', href: '/dashboard/knowledge', icon: BookOpen, feature: 'manage_agents', badge: { label: 'NUEVO', variant: 'default' } },
      { label: 'Gobernanza', href: '/dashboard/governance', icon: Shield, feature: 'manage_agents', badge: { label: 'NUEVO', variant: 'default' } },
    ]
  },
  {
    title: 'FACTURACIÓN',
    items: [
      { label: 'Planes', href: '/dashboard/billing', icon: CreditCard, feature: 'view_dashboard', badge: { label: 'NUEVO', variant: 'default' } },
    ]
  }
];
