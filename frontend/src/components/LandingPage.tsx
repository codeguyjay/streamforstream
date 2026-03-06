"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { StreamsService } from "@/api";
import { LiveStreamCard } from "@/components/LiveStreamCard";
import { getErrorMessage } from "@/lib/errors";

export function LandingPage() {
  const liveStreamsQuery = useQuery({
    queryKey: ["landing-live-streams"],
    queryFn: () => StreamsService.getLive({ limit: 6 }),
    refetchInterval: 30_000,
  });

  return (
    <div className="stack">
      <section className="hero-card">
        <div className="hero-grid">
          <div>
            <p className="eyebrow">Organic Twitch Discovery</p>
            <h1>Trade live attention with streamers who are showing up right now.</h1>
            <p className="lede">
              Add your Twitch channel, spend time in other creators&apos; chats, build points minute by minute,
              and go live when you want StreamForStream to push your channel to the front.
            </p>
            <div className="cta-row">
              <Link className="button-primary" href="/get-started">
                Get Started
              </Link>
              <Link className="button-secondary" href="/view">
                Start Viewing
              </Link>
            </div>
          </div>
          <div className="panel">
            <p className="eyebrow">How It Works</p>
            <ol className="list">
              <li>Add your Twitch stream.</li>
              <li>Watch other creators and engage in their chat to earn points.</li>
              <li>When you are ready, go live and get promoted until you finish streaming.</li>
            </ol>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>Streaming Right Now</h2>
            <p className="panel-subtitle">Live channels are ranked by current Twitch viewer count.</p>
          </div>
        </div>

        {liveStreamsQuery.isLoading ? <p className="helper">Loading the live stream board...</p> : null}
        {liveStreamsQuery.isError ? (
          <p className="error-text">{getErrorMessage(liveStreamsQuery.error, "Unable to load live streams.")}</p>
        ) : null}
        {liveStreamsQuery.data && liveStreamsQuery.data.items.length > 0 ? (
          <div className="live-grid">
            {liveStreamsQuery.data.items.map((stream) => (
              <LiveStreamCard key={stream.channel_login} stream={stream} />
            ))}
          </div>
        ) : null}
        {liveStreamsQuery.data && liveStreamsQuery.data.items.length === 0 ? (
          <div className="empty-card">
            <h3>No one is live yet.</h3>
            <p className="helper">Be the first streamer on the board today.</p>
          </div>
        ) : null}
      </section>
    </div>
  );
}
