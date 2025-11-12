"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState, type ReactNode } from "react";

/**
 * QueryProvider - Setup TanStack Query per gestire server state
 *
 * Configurazione:
 * - staleTime: 30s - cache resta "fresh" per 30 secondi
 * - cacheTime: 5min - dati restano in cache per 5 minuti dopo l'ultimo uso
 * - retry: 1 - riprova una volta in caso di errore
 * - refetchOnWindowFocus: false - non refetch automatico quando la finestra torna in focus
 */
export function QueryProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30 * 1000, // 30 secondi
            gcTime: 5 * 60 * 1000, // 5 minuti (era cacheTime in v4)
            retry: 1,
            refetchOnWindowFocus: false,
          },
          mutations: {
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {/* DevTools solo in development */}
      {process.env.NODE_ENV === "development" && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
}
