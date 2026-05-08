// =============================================================================
// FLUXAGENT V2 — KPI CARD COMPONENT
// =============================================================================
// Componente reutilizable para KPIs con skeletons y trends
// Integración con analytics reales y cache
// =============================================================================

import { LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';

// =============================================================================
// TYPES
// =============================================================================

interface KPICardProps {
  label: string;
  value: string | number;
  trend?: string;
  isLoading?: boolean;
  isPercentage?: boolean;
  icon?: LucideIcon;
  color?: string;
  description?: string;
}

// =============================================================================
// COMPONENT
// =============================================================================

export function KPICard({ 
  label, 
  value, 
  trend, 
  isLoading = false, 
  isPercentage = false,
  icon: Icon,
  color = 'primary',
  description
}: KPICardProps) {
  // Determinar color de trend
  const getTrendColor = (trendValue?: string) => {
    if (!trendValue) return 'text-muted-foreground';
    if (trendValue.startsWith('+')) return 'text-green-500';
    if (trendValue.startsWith('-')) return 'text-red-500';
    return 'text-muted-foreground';
  };

  // Determinar icon de trend
  const getTrendIcon = (trendValue?: string) => {
    if (!trendValue) return Minus;
    if (trendValue.startsWith('+')) return TrendingUp;
    if (trendValue.startsWith('-')) return TrendingDown;
    return Minus;
  };

  // Formatear valor
  const formatValue = (val: string | number) => {
    if (typeof val === 'number') {
      return isPercentage ? `${val.toFixed(1)}%` : val.toLocaleString();
    }
    return val;
  };

  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm hover:shadow-md transition-shadow group relative overflow-hidden">
      {/* Icono de fondo */}
      {Icon && (
        <div className="absolute right-4 top-4 text-primary/10 group-hover:text-primary/20 transition-colors">
          <Icon className="w-12 h-12" />
        </div>
      )}

      {/* Contenido principal */}
      <div className="space-y-2">
        {/* Label */}
        <div className="flex items-center gap-2">
          {Icon && (
            <Icon className={cn(
              "w-4 h-4",
              color === 'primary' && "text-primary",
              color === 'secondary' && "text-secondary",
              color === 'success' && "text-green-500",
              color === 'warning' && "text-yellow-500",
              color === 'error' && "text-red-500"
            )} />
          )}
          <h3 className="text-sm font-medium text-muted-foreground">
            {label}
          </h3>
        </div>

        {/* Valor */}
        <div className="text-3xl font-bold">
          {isLoading ? (
            <div className="h-8 bg-muted rounded w-3/4 animate-pulse" />
          ) : (
            formatValue(value)
          )}
        </div>

        {/* Trend y descripción */}
        <div className="flex items-center justify-between">
          {trend && !isLoading && (
            <p className={cn(
              "text-xs font-medium flex items-center gap-1",
              getTrendColor(trend)
            )}>
              {getTrendIcon(trend) && (
                <span className="w-3 h-3">
                  {getTrendIcon(trend)({ className: "w-3 h-3" })}
                </span>
              )}
              {trend}
            </p>
          )}

          {description && !isLoading && (
            <p className="text-xs text-muted-foreground">
              {description}
            </p>
          )}

          {isLoading && (
            <div className="h-4 bg-muted rounded w-20 animate-pulse" />
          )}
        </div>
      </div>

      {/* Indicador de cache si está disponible */}
      {/* Esto se puede agregar cuando se conecte con analytics reales */}
    </div>
  );
}

// =============================================================================
// SKELETON COMPONENT
// =============================================================================

export function KPICardSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm h-[120px] animate-pulse flex flex-col justify-center gap-3">
      <div className="h-4 bg-muted rounded w-1/2" />
      <div className="h-8 bg-muted rounded w-3/4" />
      <div className="h-4 bg-muted rounded w-20" />
    </div>
  );
}

// =============================================================================
// SPECIALIZED KPI COMPONENTS
// =============================================================================

export function ConversationsKPI({ 
  value, 
  trend, 
  isLoading 
}: { 
  value?: number; 
  trend?: string; 
  isLoading?: boolean;
}) {
  return (
    <KPICard
      label="Conversaciones"
      value={value ?? 0}
      trend={trend}
      isLoading={isLoading}
      icon={MessageSquare}
      color="primary"
    />
  );
}

export function LeadsKPI({ 
  value, 
  trend, 
  isLoading 
}: { 
  value?: number; 
  trend?: string; 
  isLoading?: boolean;
}) {
  return (
    <KPICard
      label="Leads Capturados"
      value={value ?? 0}
      trend={trend}
      isLoading={isLoading}
      icon={Users}
      color="success"
    />
  );
}

export function ConversionRateKPI({ 
  value, 
  trend, 
  isLoading 
}: { 
  value?: number; 
  trend?: string; 
  isLoading?: boolean;
}) {
  return (
    <KPICard
      label="Tasa de Conversión"
      value={value ? `${value.toFixed(1)}%` : '0%'}
      trend={trend}
      isLoading={isLoading}
      isPercentage={true}
      icon={Target}
      color="warning"
    />
  );
}

export function SentimentKPI({ 
  value, 
  trend, 
  isLoading 
}: { 
  value?: number; 
  trend?: string; 
  isLoading?: boolean;
}) {
  const getSentimentIcon = (score?: number) => {
    if (!score) return 'N/A';
    if (score > 0.7) return '😊';
    if (score > 0.3) return '😐';
    return '😔';
  };

  const getSentimentColor = (score?: number) => {
    if (!score) return 'muted-foreground';
    if (score > 0.7) return 'text-green-500';
    if (score > 0.3) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <KPICard
      label="Sentimiento Promedio"
      value={value ? `${(value * 100).toFixed(0)}%` : 'N/A'}
      trend={trend}
      isLoading={isLoading}
      description={value ? getSentimentIcon(value) : 'N/A'}
      color={getSentimentColor(value) as any}
    />
  );
}

export function ResponseTimeKPI({ 
  value, 
  trend, 
  isLoading 
}: { 
  value?: number; 
  trend?: string; 
  isLoading?: boolean;
}) {
  const formatResponseTime = (seconds?: number) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    } else if (seconds < 3600) {
      return `${(seconds / 60).toFixed(1)}m`;
    } else {
      return `${(seconds / 3600).toFixed(1)}h`;
    }
  };

  return (
    <KPICard
      label="Tiempo de Respuesta"
      value={formatResponseTime(value)}
      trend={trend}
      isLoading={isLoading}
      icon={Clock}
      color="secondary"
    />
  );
}

// Importar iconos necesarios
import { MessageSquare, Users, Target, Clock } from 'lucide-react';
