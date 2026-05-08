"use client";

import { ThemeProvider as NextThemesProvider, type ThemeProviderProps } from "next-themes";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { EventBusProvider } from "@/providers/EventBusProvider";
import { Toaster } from "@/components/ui/sonner";
import { TenantProvider } from "@/context/TenantContext";

export function Providers({ children, ...props }: ThemeProviderProps) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,
      },
    },
  }));

  return (
    <QueryClientProvider client={queryClient}>
      <NextThemesProvider attribute="class" defaultTheme="system" enableSystem {...props}>
        <TooltipProvider delayDuration={300}>
          <TenantProvider>
            <EventBusProvider tenantId="demo-tenant-1">
              {children}
            </EventBusProvider>
          </TenantProvider>
        </TooltipProvider>
      </NextThemesProvider>
      <Toaster />
    </QueryClientProvider>
  );
}
