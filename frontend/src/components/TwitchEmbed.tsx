"use client";

import { useSyncExternalStore } from "react";

interface TwitchEmbedProps {
  channelLogin: string;
}

function subscribe(): () => void {
  return () => {};
}

function getSnapshot(): string {
  return window.location.hostname || "localhost";
}

function getServerSnapshot(): string {
  return "localhost";
}

export function TwitchEmbed({ channelLogin }: TwitchEmbedProps) {
  const parent = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  return (
    <iframe
      allowFullScreen
      className="twitch-frame"
      src={`https://player.twitch.tv/?channel=${encodeURIComponent(channelLogin)}&parent=${encodeURIComponent(parent)}`}
      title={`Twitch player for ${channelLogin}`}
    />
  );
}
