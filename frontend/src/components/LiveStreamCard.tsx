"use client";

import type { LiveStreamerResponse } from "@/api/models/LiveStreamerResponse";

interface LiveStreamCardProps {
  stream: LiveStreamerResponse;
  selected?: boolean;
  onSelect?: () => void;
}

export function LiveStreamCard({ stream, selected = false, onSelect }: LiveStreamCardProps) {
  const className = `stream-card${onSelect ? " is-interactive" : ""}${selected ? " is-selected" : ""}`;

  const content = (
    <>
      <div className="stream-meta">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          alt={`${stream.channel_display_name} avatar`}
          className="stream-avatar"
          src={stream.profile_image_url || "https://static-cdn.jtvnw.net/jtv_user_pictures/xarth/404_user_70x70.png"}
        />
        <div>
          <h3>{stream.channel_display_name}</h3>
          <p>@{stream.channel_login}</p>
        </div>
      </div>
      <p>{stream.stream_title || "Live on Twitch now."}</p>
      <div className="pill-row">
        <span className="pill live">{stream.viewer_count} viewers</span>
        <span className="pill">{stream.game_name || "Just Chatting"}</span>
        <span className="pill">{stream.points_balance} pts</span>
      </div>
    </>
  );

  if (onSelect) {
    return (
      <button className={className} onClick={onSelect} type="button">
        {content}
      </button>
    );
  }

  return <article className={className}>{content}</article>;
}
