import type { Metadata } from "next";
import Link from "next/link";

import { Providers } from "@/app/providers";
import "@/app/globals.css";

export const metadata: Metadata = {
  title: "StreamForStream",
  description: "Anonymous stream discovery and minute-based point tracking for Twitch streamers.",
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
                <span className="brand-mark">SFS</span>
                <span>
                  <strong>StreamForStream</strong>
                  <span className="brand-subtitle">Twitch viewers trading time, not gimmicks.</span>
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
