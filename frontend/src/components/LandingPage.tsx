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
          <div className="panel stack hero-media-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Live Preview</p>
                <h2>{selectedStream ? selectedStream.channel_display_name : "Select a live streamer"}</h2>
                <p className="panel-subtitle">
                  {selectedStream
                    ? "The player autoplays muted when Twitch allows it."
                    : "Pick a live card below and the player will switch instantly."}
                </p>
              </div>
              {selectedStream ? (
                <Link className="button-ghost" href={selectedStream.channel_url} rel="noreferrer" target="_blank">
                  Open on Twitch
                </Link>
              ) : null}
            </div>

            {liveStreamsQuery.isLoading && !selectedStream ? (
              <p className="helper">Loading a live stream preview...</p>
            ) : null}
            {liveStreamsQuery.isError && !selectedStream ? (
              <p className="error-text">{getErrorMessage(liveStreamsQuery.error, "Unable to load live streams.")}</p>
            ) : null}
            {selectedStream ? (
              <>
                <TwitchEmbed autoplay channelLogin={selectedStream.channel_login} muted showChat={false} />
                <div className="pill-row">
                  <span className="pill live">{selectedStream.viewer_count} viewers</span>
                  <span className="pill">{selectedStream.game_name || "Just Chatting"}</span>
                  <span className="pill">{selectedStream.stream_title || "Live now"}</span>
                </div>
              </>
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
            <p className="panel-subtitle">Live channels are ranked by viewer count. Click any card to switch the player above.</p>
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
