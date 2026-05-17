// @ts-nocheck
import { useState, useEffect } from 'react';
import { IngestionMetrics } from '../types';
import { api } from '@/lib/api'; // Using api directly instead of fetch to ensure proper token headers and interceptors

export function useIngestionStats() {
  const [data, setData] = useState<IngestionMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      // Using our configured API client that handles the auth token
      const res = await api.get('/stats/ingestion');
      setData(res.data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch stats');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Actualiza cada 30s
    return () => clearInterval(interval);
  }, []);

  return { data, isLoading, error, refetch: fetchStats };
}
