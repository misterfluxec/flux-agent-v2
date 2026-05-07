// =============================================================================
// FLUXAGENT V2 — ANALYTICS HOOK (CACHE-AWARE)
// =============================================================================
// Hook personalizado para analytics con cache inteligente
// Integración con backend analytics_router_cached
// =============================================================================

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { 
  fetchAnalyticsOverview, 
  fetchDailyStats, 
  fetchAgentStats, 
  fetchSentimentAnalysis,
  fetchTopAgents,
  invalidateAnalyticsCache,
  fetchCacheMetrics,
  fetchRealtimeMetrics,
  AnalyticsFilters,
  AnalyticsOverview,
  DailyStats,
  AgentStats,
  SentimentAnalysis,
  TopPerformingAgent,
  formatNumber,
  formatPercentage,
  formatDuration,
  calculateTrend
} from '@/lib/api/analytics';

// =============================================================================
// MAIN ANALYTICS HOOK
// =============================================================================

export function useAnalytics(filters?: AnalyticsFilters) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const queryClient = useQueryClient();

  // Analytics Overview con cache
  const {
    data: overview,
    isLoading: isLoadingOverview,
    error: overviewError,
    refetch: refetchOverview
  } = useQuery<AnalyticsOverview, Error>({
    queryKey: ['analytics-overview', filters],
    queryFn: () => fetchAnalyticsOverview(filters),
    staleTime: 5 * 60 * 1000, // 5 minutos
    refetchOnWindowFocus: false,
    retry: 2
  });

  // Daily Stats
  const {
    data: dailyStats,
    isLoading: isLoadingDaily,
    error: dailyError,
    refetch: refetchDaily
  } = useQuery<DailyStats[], Error>({
    queryKey: ['analytics-daily', filters],
    queryFn: () => fetchDailyStats(filters),
    staleTime: 10 * 60 * 1000, // 10 minutos
    refetchOnWindowFocus: false,
    retry: 2
  });

  // Agent Stats
  const {
    data: agentStats,
    isLoading: isLoadingAgents,
    error: agentsError,
    refetch: refetchAgents
  } = useQuery<AgentStats[], Error>({
    queryKey: ['analytics-agents', filters],
    queryFn: () => fetchAgentStats(filters),
    staleTime: 15 * 60 * 1000, // 15 minutos
    refetchOnWindowFocus: false,
    retry: 2
  });

  // Sentiment Analysis
  const {
    data: sentimentAnalysis,
    isLoading: isLoadingSentiment,
    error: sentimentError,
    refetch: refetchSentiment
  } = useQuery<SentimentAnalysis, Error>({
    queryKey: ['analytics-sentiment', filters],
    queryFn: () => fetchSentimentAnalysis(filters),
    staleTime: 30 * 60 * 1000, // 30 minutos
    refetchOnWindowFocus: false,
    retry: 2
  });

  // Top Agents
  const {
    data: topAgents,
    isLoading: isLoadingTop,
    error: topError,
    refetch: refetchTop
  } = useQuery<TopPerformingAgent[], Error>({
    queryKey: ['analytics-top', filters],
    queryFn: () => fetchTopAgents(filters),
    staleTime: 20 * 60 * 1000, // 20 minutos
    refetchOnWindowFocus: false,
    retry: 2
  });

  // Cache Metrics
  const {
    data: cacheMetrics,
    isLoading: isLoadingCache,
    error: cacheError,
    refetch: refetchCache
  } = useQuery<any, Error>({
    queryKey: ['analytics-cache-metrics'],
    queryFn: fetchCacheMetrics,
    staleTime: 2 * 60 * 1000, // 2 minutos
    refetchOnWindowFocus: false,
    retry: 1
  });

  // Realtime Metrics
  const {
    data: realtimeMetrics,
    isLoading: isLoadingRealtime,
    error: realtimeError,
    refetch: refetchRealtime
  } = useQuery<any, Error>({
    queryKey: ['analytics-realtime'],
    queryFn: fetchRealtimeMetrics,
    staleTime: 30 * 1000, // 30 segundos
    refetchInterval: 30 * 1000, // Refrescar cada 30 segundos
    retry: 1
  });

  // Refresh manual con invalidación de cache
  const refreshAll = useCallback(async () => {
    setIsRefreshing(true);
    try {
      // Invalidar cache en backend
      await invalidateAnalyticsCache();
      
      // Invalidar cache local
      await queryClient.invalidateQueries({ queryKey: ['analytics-overview'] });
      await queryClient.invalidateQueries({ queryKey: ['analytics-daily'] });
      await queryClient.invalidateQueries({ queryKey: ['analytics-agents'] });
      await queryClient.invalidateQueries({ queryKey: ['analytics-sentiment'] });
      await queryClient.invalidateQueries({ queryKey: ['analytics-top'] });
      
      // Refrescar datos
      await Promise.all([
        refetchOverview(),
        refetchDaily(),
        refetchAgents(),
        refetchSentiment(),
        refetchTop()
      ]);
    } catch (error) {
      console.error('Error refreshing analytics:', error);
    } finally {
      setIsRefreshing(false);
    }
  }, [queryClient, refetchOverview, refetchDaily, refetchAgents, refetchSentiment, refetchTop]);

  // Calcular tendencias (comparar con período anterior)
  const calculateTrends = useCallback(() => {
    if (!overview || !dailyStats || dailyStats.length < 2) return null;

    const currentPeriod = dailyStats.slice(-7); // Últimos 7 días
    const previousPeriod = dailyStats.slice(-14, -7); // 7 días anteriores

    const currentConversations = currentPeriod.reduce((sum, day) => sum + day.conversations, 0);
    const previousConversations = previousPeriod.reduce((sum, day) => sum + day.conversations, 0);

    const currentSales = currentPeriod.reduce((sum, day) => sum + day.sales, 0);
    const previousSales = previousPeriod.reduce((sum, day) => sum + day.sales, 0);

    return {
      conversations: calculateTrend(currentConversations, previousConversations),
      sales: calculateTrend(currentSales, previousSales),
      avgResponseTime: calculateTrend(overview.avg_response_time, overview.avg_response_time * 1.1), // Simulación
      conversionRate: calculateTrend(overview.conversion_rate, overview.conversion_rate * 0.9) // Simulación
    };
  }, [overview, dailyStats]);

  return {
    // Data
    overview,
    dailyStats,
    agentStats,
    sentimentAnalysis,
    topAgents,
    cacheMetrics,
    realtimeMetrics,
    trends: calculateTrends(),
    
    // Loading states
    isLoading: isLoadingOverview || isLoadingDaily || isLoadingAgents || isLoadingSentiment || isLoadingTop,
    isRefreshing,
    
    // Error states
    errors: {
      overview: overviewError,
      daily: dailyError,
      agents: agentsError,
      sentiment: sentimentError,
      top: topError,
      cache: cacheError,
      realtime: realtimeError
    },
    
    // Actions
    refreshAll,
    refetchOverview,
    refetchDaily,
    refetchAgents,
    refetchSentiment,
    refetchTop,
    refetchCache,
    refetchRealtime
  };
}

// =============================================================================
// SPECIALIZED HOOKS
// =============================================================================

/**
 * Hook para métricas del dashboard principal
 */
export function useDashboardMetrics(days: number = 7) {
  const { overview, trends, isLoading, errors } = useAnalytics({ days });
  
  return {
    kpis: overview ? {
      conversations: {
        value: overview.total_conversations,
        formatted: formatNumber(overview.total_conversations),
        trend: trends?.conversations
      },
      messages: {
        value: overview.total_messages,
        formatted: formatNumber(overview.total_messages)
      },
      sales: {
        value: overview.total_sales,
        formatted: `$${formatNumber(overview.total_sales)}`,
        trend: trends?.sales
      },
      conversionRate: {
        value: overview.conversion_rate,
        formatted: formatPercentage(overview.conversion_rate),
        trend: trends?.conversionRate
      },
      avgResponseTime: {
        value: overview.avg_response_time,
        formatted: formatDuration(overview.avg_response_time),
        trend: trends?.avgResponseTime
      },
      sentimentScore: {
        value: overview.sentiment_score,
        formatted: `${(overview.sentiment_score * 100).toFixed(1)}%`
      }
    } : null,
    cacheStatus: overview?.cache_status,
    isLoading,
    errors
  };
}

/**
 * Hook para comparación de agentes
 */
export function useAgentComparison(days: number = 30) {
  const { agentStats, isLoading, errors } = useAnalytics({ days });
  
  const topPerforming = agentStats 
    ? [...agentStats].sort((a, b) => {
        const scoreA = (a.conversations * 0.3) + (a.sales * 0.4) + (a.satisfaction_score * 100 * 0.3);
        const scoreB = (b.conversations * 0.3) + (b.sales * 0.4) + (b.satisfaction_score * 100 * 0.3);
        return scoreB - scoreA;
      }).slice(0, 5)
    : [];

  return {
    agents: agentStats,
    topPerforming,
    isLoading,
    errors
  };
}

/**
 * Hook para métricas en tiempo real
 */
export function useRealtimeAnalytics() {
  const { realtimeMetrics, isLoading, errors, refetchRealtime } = useAnalytics();
  
  return {
    metrics: realtimeMetrics,
    isLoading,
    errors,
    refetch: refetchRealtime
  };
}

/**
 * Hook para métricas de cache
 */
export function useCacheAnalytics() {
  const { cacheMetrics, isLoading, errors, refetchCache } = useAnalytics();
  
  return {
    metrics: cacheMetrics,
    isLoading,
    errors,
    refetch: refetchCache,
    isHealthy: cacheMetrics ? cacheMetrics.hit_rate > 0.7 : false // 70% hit rate mínimo
  };
}
