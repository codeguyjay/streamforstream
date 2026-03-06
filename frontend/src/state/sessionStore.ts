import { create } from "zustand";

import { clearSessionCookie, setSessionCookie } from "@/lib/session-cookies";
import type { StreamerSession } from "@/lib/session";

interface SessionState {
  session: StreamerSession | null;
  hydrated: boolean;
  setSession: (session: StreamerSession) => void;
  clearSession: () => void;
  setHydrated: (hydrated: boolean) => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  session: null,
  hydrated: false,
  setSession: (session) => {
    setSessionCookie(session);
    set({ session });
  },
  clearSession: () => {
    clearSessionCookie();
    set({ session: null });
  },
  setHydrated: (hydrated) => {
    set({ hydrated });
  },
}));
