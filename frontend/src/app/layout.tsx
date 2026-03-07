import type { Metadata } from "next";
import Link from "next/link";

import { Providers } from "@/app/providers";
import "@/app/globals.css";

export const metadata: Metadata = {
  title: "StreamBaton",
  description: "Pass support forward with anonymous stream discovery and minute-based point tracking for Twitch streamers.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <div className="page-shell">
            <header className="site-header">
              <Link className="brand-lockup" href="/">
                <span className="brand-mark">SB</span>
                <span>
                  <strong>StreamBaton</strong>
                  <span className="brand-subtitle">Pass the support forward. Never stream alone.</span>
                </span>
              </Link>
            </header>
            <main className="site-main">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
