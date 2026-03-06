"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { getSessionFromCookies } from "@/lib/session-cookies";
import { useSessionStore } from "@/state/sessionStore";

function SessionHydrator() {
  const setSession = useSessionStore((state) => state.setSession);
  const clearSession = useSessionStore((state) => state.clearSession);
  const hydrated = useSessionStore((state) => state.hydrated);
  const setHydrated = useSessionStore((state) => state.setHydrated);

  useEffect(() => {
    if (hydrated) {
      return;
    }

    const persisted = getSessionFromCookies();
    if (persisted) {
      setSession(persisted);
    } else {
      clearSession();
    }
    setHydrated(true);
  }, [clearSession, hydrated, setHydrated, setSession]);

  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            refetchOnWindowFocus: false,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <SessionHydrator />
      {children}
    </QueryClientProvider>
  );
}
