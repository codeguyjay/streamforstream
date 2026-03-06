"use client";

import { useEffect, useState } from "react";

interface TwitchEmbedProps {
  channelLogin: string;
}

export function TwitchEmbed({ channelLogin }: TwitchEmbedProps) {
  const [parent, setParent] = useState("localhost");

  useEffect(() => {
    if (typeof window !== "undefined" && window.location.hostname) {
      setParent(window.location.hostname);
    }
  }, []);

  return (
    <iframe
      allowFullScreen
      className="twitch-frame"
      src={`https://player.twitch.tv/?channel=${encodeURIComponent(channelLogin)}&parent=${encodeURIComponent(parent)}`}
      title={`Twitch player for ${channelLogin}`}
    />
  );
}
