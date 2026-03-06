import Cookies from "js-cookie";

import type { StreamerSession } from "@/lib/session";

const SESSION_KEY = "streamforstream_session";

export function getSessionFromCookies(): StreamerSession | null {
  const raw = Cookies.get(SESSION_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as StreamerSession;
  } catch {
    Cookies.remove(SESSION_KEY);
    return null;
  }
}

export function setSessionCookie(session: StreamerSession): void {
  Cookies.set(SESSION_KEY, JSON.stringify(session), {
    sameSite: "lax",
  });
}

export function clearSessionCookie(): void {
  Cookies.remove(SESSION_KEY);
}
