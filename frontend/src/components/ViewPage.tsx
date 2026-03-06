"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { StreamsService, ViewsService } from "@/api";
import { LiveStreamCard } from "@/components/LiveStreamCard";
import { TwitchEmbed, type TwitchEmbedHandle } from "@/components/TwitchEmbed";
import { getErrorMessage } from "@/lib/errors";
import { currentMinuteIso } from "@/lib/time";
import { useSessionStore } from "@/state/sessionStore";

export function ViewPage() {
  const router = useRouter();
  const session = useSessionStore((state) => state.session);
  const hydrated = useSessionStore((state) => state.hydrated);
  const clearSession = useSessionStore((state) => state.clearSession);
  const [selectedChannelLogin, setSelectedChannelLogin] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [localPointsBalance, setLocalPointsBalance] = useState<number | null>(null);
  const lastReportKeyRef = useRef<string | null>(null);
  const embedRef = useRef<TwitchEmbedHandle>(null);

  useEffect(() => {
    if (hydrated && !session) {
      router.replace("/get-started");
    }
  }, [hydrated, router, session]);

  const liveStreamsQuery = useQuery({
    queryKey: ["view-live-streams", session?.channel_login],
    queryFn: () =>
      StreamsService.getLive({
        exclude_channel_login: session?.channel_login,
        limit: 12,
      }),
    enabled: Boolean(session),
    refetchInterval: 30_000,
  });
  const { data, error, isError, isLoading, refetch } = liveStreamsQuery;
  const streams = data?.items ?? [];
  const effectiveSelectedChannelLogin =
    streams.some((item) => item.channel_login === selectedChannelLogin)
      ? selectedChannelLogin
      : streams[0]?.channel_login ?? null;
  const selectedStream =
    streams.find((item) => item.channel_login === effectiveSelectedChannelLogin) ?? null;

  const goLiveMutation = useMutation({
    mutationFn: () => {
      if (!session) {
        throw new Error("Add your Twitch channel before going live.");
      }
      return StreamsService.goLive({ channel_login: session.channel_login });
    },
    onSuccess: async () => {
      setMessage("Your channel is now on the live board.");
      await refetch();
    },
    onError: (error) => {
      setMessage(getErrorMessage(error, "Unable to put your channel on the live board."));
    },
  });

  function handleEndSession() {
    clearSession();
    router.replace("/get-started");
  }

  useEffect(() => {
    if (!session || !selectedStream) {
      return;
    }

    const viewerChannelLogin = session.channel_login;
    const targetChannelLogin = selectedStream.channel_login;
    let cancelled = false;

    async function maybeReportView() {
      if (document.visibilityState !== "visible") {
        return;
      }
      if (embedRef.current?.isPaused() !== false) {
        return;
      }

      const viewedMinute = currentMinuteIso();
      const reportKey = `${targetChannelLogin}:${viewedMinute}`;
      if (lastReportKeyRef.current === reportKey) {
        return;
      }

      try {
        const result = await ViewsService.reportView({
          viewer_channel_login: viewerChannelLogin,
          target_channel_login: targetChannelLogin,
          viewed_minute: viewedMinute,
        });
        if (cancelled) {
          return;
        }
        lastReportKeyRef.current = reportKey;
        setLocalPointsBalance(result.viewer_points_balance);
        void refetch();
      } catch (error) {
        if (!cancelled) {
          setMessage(getErrorMessage(error, "Unable to report viewing time right now."));
        }
      }
    }

    void maybeReportView();
    const intervalId = window.setInterval(() => {
      void maybeReportView();
    }, 15_000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [refetch, selectedStream, session]);

  if (!hydrated || !session) {
    return <section className="panel"><p className="helper">Loading your session...</p></section>;
  }

  const viewerPointsBalance = localPointsBalance ?? data?.viewer_points_balance ?? 0;
  const viewerIsLive = data?.viewer_is_live ?? false;

  return (
    <div className="stack">
      <section className="panel stack">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Live View Board</p>
            <h1>Watch someone else, earn points, then flip your own channel live.</h1>
          </div>
          <div className="cta-row">
            <button
              className="button-primary"
              disabled={goLiveMutation.isPending || viewerIsLive}
              onClick={() => goLiveMutation.mutate()}
              type="button"
            >
              {viewerIsLive ? "You Are Live" : goLiveMutation.isPending ? "Checking Twitch..." : "Go Live"}
            </button>
            <button
              className="button-ghost"
              onClick={handleEndSession}
              type="button"
            >
              End Session
            </button>
          </div>
        </div>

        <div className="stat-grid">
          <article className="stat-card">
            <span className="stat-label">Viewer Session</span>
            <span className="stat-value">@{session.channel_login}</span>
          </article>
          <article className="stat-card">
            <span className="stat-label">Points</span>
            <span className="stat-value">{viewerPointsBalance}</span>
          </article>
          <article className="stat-card">
            <span className="stat-label">Live Status</span>
            <span className="stat-value">{viewerIsLive ? "On Board" : "Offline"}</span>
          </article>
        </div>

        {message ? <p className={goLiveMutation.isError ? "error-text" : "status-text"}>{message}</p> : null}
        {isError ? (
          <p className="error-text">{getErrorMessage(error, "Unable to load the live board.")}</p>
        ) : null}
      </section>

      <section className="panel stack">
        <div className="panel-header">
          <div>
            <h2>Selected Stream</h2>
            <p className="panel-subtitle">Stay active in chat while StreamForStream credits your viewing time.</p>
          </div>
          {selectedStream ? (
            <Link className="button-ghost" href={selectedStream.channel_url} rel="noreferrer" target="_blank">
              Open on Twitch
            </Link>
          ) : null}
        </div>

        {selectedStream ? (
          <>
            <TwitchEmbed ref={embedRef} channelLogin={selectedStream.channel_login} />
            <div className="pill-row">
              <span className="pill live">{selectedStream.viewer_count} viewers</span>
              <span className="pill">{selectedStream.game_name || "Just Chatting"}</span>
              <span className="pill">{selectedStream.stream_title || "Live now"}</span>
            </div>
          </>
        ) : (
          <div className="empty-card">
            <h3>No other streamers are live right now.</h3>
            <p className="helper">Keep this page open and the list will refresh automatically every 30 seconds.</p>
          </div>
        )}
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>Who to watch</h2>
            <p className="panel-subtitle">Sorted by current Twitch audience size.</p>
          </div>
        </div>

        {isLoading ? <p className="helper">Loading live streamers...</p> : null}
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
      </section>
    </div>
  );
}
