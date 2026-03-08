"use client";

import { useEffect, useImperativeHandle, useRef } from "react";
import { useSyncExternalStore } from "react";

export interface TwitchEmbedHandle {
  isPaused(): boolean;
}

interface TwitchEmbedProps {
  channelLogin: string;
  autoplay?: boolean;
  muted?: boolean;
  showChat?: boolean;
  ref?: React.Ref<TwitchEmbedHandle>;
}

interface TwitchPlayer {
  play(): void;
  setMuted(muted: boolean): void;
  isPaused(): boolean;
}

interface TwitchEmbedInstance {
  addEventListener(event: string, callback: () => void): void;
  getPlayer(): TwitchPlayer;
}

interface TwitchEmbedConstructor {
  new (
    element: HTMLElement,
    options: {
      width: string | number;
      height: string | number;
      channel: string;
      parent: string[];
      layout?: "video" | "video-with-chat";
      autoplay: boolean;
      muted: boolean;
    },
  ): TwitchEmbedInstance;
  VIDEO_READY: string;
  VIDEO_PLAY: string;
}

declare global {
  interface Window {
    Twitch?: { Embed: TwitchEmbedConstructor };
  }
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

function loadTwitchScript(): Promise<void> {
  return new Promise((resolve) => {
    if (window.Twitch?.Embed) {
      resolve();
      return;
    }
    const existing = document.getElementById("twitch-embed-script");
    const script = existing ?? document.createElement("script");
    script.addEventListener("load", () => resolve(), { once: true });
    if (!existing) {
      script.id = "twitch-embed-script";
      (script as HTMLScriptElement).src = "https://embed.twitch.tv/embed/v1.js";
      document.head.appendChild(script);
    }
  });
}

export function TwitchEmbed({
  channelLogin,
  autoplay = false,
  muted = true,
  showChat = true,
  ref,
}: TwitchEmbedProps) {
  const parent = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const containerRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<TwitchPlayer | null>(null);
  const playbackStartedRef = useRef(false);

  useImperativeHandle(ref, () => ({
    isPaused: () => {
      if (!playbackStartedRef.current) return true;
      return playerRef.current?.isPaused() ?? true;
    },
  }));

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let cancelled = false;
    playerRef.current = null;
    playbackStartedRef.current = false;

    void loadTwitchScript().then(() => {
      if (cancelled || !container || !window.Twitch?.Embed) return;

      container.innerHTML = "";

      const embed = new window.Twitch.Embed(container, {
        width: "100%",
        height: "100%",
        channel: channelLogin,
        parent: [parent],
        layout: showChat ? "video-with-chat" : "video",
        autoplay,
        muted,
      });

      embed.addEventListener(window.Twitch.Embed.VIDEO_READY, () => {
        if (cancelled) return;
        playerRef.current = embed.getPlayer();
      });

      embed.addEventListener(window.Twitch.Embed.VIDEO_PLAY, () => {
        if (cancelled) return;
        playbackStartedRef.current = true;
      });
    });

    return () => {
      cancelled = true;
      playerRef.current = null;
      playbackStartedRef.current = false;
      container.innerHTML = "";
    };
  }, [autoplay, channelLogin, muted, parent, showChat]);

  return <div className="twitch-frame" ref={containerRef} />;
}
