import { useState, useEffect } from 'react';

export interface UsageSummary {
  tokens: {
    limit: number;
    consumed: number;
    percentage: number;
  };
  workflows: {
    consumed: number;
  };
}

export function useTenantGovernance() {
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchUsage() {
      try {
        const res = await fetch('/api/v1/governance/usage/summary');
        if (res.ok) {
          const data = await res.json();
          setUsage(data);
        }
      } catch (error) {
        console.error('Failed to fetch governance usage:', error);
      } finally {
        setIsLoading(false);
      }
    }

    fetchUsage();
    
    // Refresh usage every minute
    const interval = setInterval(fetchUsage, 60000);
    return () => clearInterval(interval);
  }, []);

  return { usage, isLoading };
}
