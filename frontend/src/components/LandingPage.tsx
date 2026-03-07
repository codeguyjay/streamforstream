"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { StreamsService } from "@/api";
import { LiveStreamCard } from "@/components/LiveStreamCard";
import { TwitchEmbed } from "@/components/TwitchEmbed";
import { getErrorMessage } from "@/lib/errors";

export function LandingPage() {
  const [selectedChannelLogin, setSelectedChannelLogin] = useState<string | null>(null);
  const liveStreamsQuery = useQuery({
    queryKey: ["landing-live-streams"],
    queryFn: () => StreamsService.getLive({ limit: 6 }),
    refetchInterval: 30_000,
  });
  const streams = liveStreamsQuery.data?.items ?? [];
  const effectiveSelectedChannelLogin =
    streams.some((item) => item.channel_login === selectedChannelLogin)
      ? selectedChannelLogin
      : streams[0]?.channel_login ?? null;
  const selectedStream =
    streams.find((item) => item.channel_login === effectiveSelectedChannelLogin) ?? null;

  return (
    <div className="stack">
      <section className="hero-card">
        <div className="hero-grid">
          <div className="landing-hero-copy">
            <p className="eyebrow">Organic Twitch Discovery</p>
            <h1>Earn views by spending time in other channels.</h1>
            <p className="lede">
            No logins or purchasing needed.
            </p>
            <p className="hero-steps-label">Steps</p>
            <ol className="list">
              <li>Add your Twitch channel.</li>
              <li>Start viewing peer streams to earn points.</li>
              <li>Click Go Live when you are streaming and we&apos;ll monitor and promote your stream.</li>
            </ol>
            <div className="cta-row">
              <Link className="button-primary" href="/get-started">
                Get Started
              </Link>
            </div>
          </div>
          <div className="panel stack hero-media-panel">
            <h2>{selectedStream ? `Live Preview - ${selectedStream.channel_display_name}` : "Live Preview"}</h2>

            {liveStreamsQuery.isLoading && !selectedStream ? (
              <p className="helper">Loading a live stream preview...</p>
            ) : null}
            {liveStreamsQuery.isError && !selectedStream ? (
              <p className="error-text">{getErrorMessage(liveStreamsQuery.error, "Unable to load live streams.")}</p>
            ) : null}
            {selectedStream ? (
              <TwitchEmbed autoplay channelLogin={selectedStream.channel_login} muted showChat={false} />
            ) : null}
            {!liveStreamsQuery.isLoading && !liveStreamsQuery.isError && !selectedStream ? (
              <div className="empty-card">
                <h3>No one is live yet.</h3>
                <p className="helper">Be the first streamer on the board today.</p>
              </div>
            ) : null}
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>Streaming Right Now</h2>
          </div>
        </div>

        {liveStreamsQuery.isLoading ? <p className="helper">Loading the live stream board...</p> : null}
        {liveStreamsQuery.isError ? (
          <p className="error-text">{getErrorMessage(liveStreamsQuery.error, "Unable to load live streams.")}</p>
        ) : null}
        {streams.length > 0 ? (
          <div className="live-grid">
            {streams.map((stream) => (
              <LiveStreamCard
                key={stream.channel_login}
                onSelect={() => setSelectedChannelLogin(stream.channel_login)}
                selected={effectiveSelectedChannelLogin === stream.channel_login}
                stream={stream}
              />
            ))}
          </div>
        ) : null}
        {liveStreamsQuery.data && streams.length === 0 ? (
          <div className="empty-card">
            <h3>No one is live yet.</h3>
            <p className="helper">Be the first streamer on the board today.</p>
          </div>
        ) : null}
      </section>
    </div>
  );
}
