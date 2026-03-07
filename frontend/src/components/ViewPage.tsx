"use client";

import { useInfiniteQuery, useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { StreamsService, ViewsService } from "@/api";
import { LiveStreamCard } from "@/components/LiveStreamCard";
import { TwitchEmbed, type TwitchEmbedHandle } from "@/components/TwitchEmbed";
import { getErrorMessage } from "@/lib/errors";
import { currentMinuteIso } from "@/lib/time";
import { useSessionStore } from "@/state/sessionStore";

const PAGE_SIZE = 12;

export function ViewPage() {
  const router = useRouter();
  const session = useSessionStore((state) => state.session);
  const hydrated = useSessionStore((state) => state.hydrated);
  const clearSession = useSessionStore((state) => state.clearSession);
  const [selectedChannelLogin, setSelectedChannelLogin] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [localTotalPoints, setLocalTotalPoints] = useState<number | null>(null);
  const [localTotalPointsChannelLogin, setLocalTotalPointsChannelLogin] = useState<string | null>(null);
  const lastReportedMinuteRef = useRef<string | null>(null);
  const embedRef = useRef<TwitchEmbedHandle>(null);

  useEffect(() => {
    if (hydrated && !session) {
      router.replace("/get-started");
    }
  }, [hydrated, router, session]);

  const liveStreamsQuery = useInfiniteQuery({
    queryKey: ["view-live-streams", session?.channel_login],
    queryFn: ({ pageParam }) =>
      StreamsService.getLive({
        exclude_channel_login: session?.channel_login,
        limit: PAGE_SIZE,
        cursor: pageParam,
        sort_mode: "engagement_priority",
      }),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    enabled: Boolean(session),
  });
  const { data, error, fetchNextPage, hasNextPage, isError, isFetching, isFetchingNextPage, isLoading, refetch } =
    liveStreamsQuery;
  const streams = data?.pages.flatMap((page) => page.items) ?? [];
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
    onSuccess: () => {
      setMessage("Your channel is now on the live board.");
      void refetch();
    },
    onError: (mutationError) => {
      setMessage(getErrorMessage(mutationError, "Unable to put your channel on the live board."));
    },
  });

  function handleEndSession() {
    clearSession();
    router.replace("/get-started");
  }

  function handleLoadMore() {
    if (!hasNextPage || isFetchingNextPage) {
      return;
    }
    void fetchNextPage();
  }

  function handleRefreshSuggestions() {
    if (isFetching) {
      return;
    }
    void refetch();
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
      if (lastReportedMinuteRef.current === viewedMinute) {
        return;
      }

      try {
        const result = await ViewsService.reportView({
          earning_channel_login: viewerChannelLogin,
          viewed_channel_login: targetChannelLogin,
          viewed_minute: viewedMinute,
        });
        if (cancelled) {
          return;
        }
        lastReportedMinuteRef.current = viewedMinute;
        setLocalTotalPoints(result.viewer_total_points);
        setLocalTotalPointsChannelLogin(viewerChannelLogin);
      } catch (reportError) {
        if (!cancelled) {
          setMessage(getErrorMessage(reportError, "Unable to report viewing time right now."));
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
  }, [selectedStream, session]);

  if (!hydrated || !session) {
    return <section className="panel"><p className="helper">Loading your session...</p></section>;
  }

  const queryViewerTotalPoints = data?.pages[0]?.viewer_total_points;
  const localPointsValid = localTotalPointsChannelLogin === session.channel_login && localTotalPoints !== null;
  const viewerTotalPoints = localPointsValid ? localTotalPoints : (queryViewerTotalPoints ?? 0);
  const viewerIsLive = data?.pages[0]?.viewer_is_live ?? false;

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
            <span className="stat-label">Total Points</span>
            <span className="stat-value">{viewerTotalPoints}</span>
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
            <p className="panel-subtitle">
              Make sure stream is playing to start earning points. Engage in chat to start building connections!
            </p>
          </div>
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
            <p className="helper">Use Refresh Suggestions to check again without interrupting your current stream.</p>
          </div>
        )}
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>Select a streamer</h2>
            <p className="panel-subtitle">
              We recommend lower viewer streamers with higher points first to help make sure everyone has someone to
              engage with!
            </p>
          </div>
          <button
            className="button-secondary"
            disabled={isFetching}
            onClick={handleRefreshSuggestions}
            type="button"
          >
            {isFetching && !isFetchingNextPage ? "Refreshing..." : "Refresh Suggestions"}
          </button>
        </div>

        {isLoading && streams.length === 0 ? <p className="helper">Loading live streamers...</p> : null}
        {streams.length > 0 ? (
          <>
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
            {hasNextPage ? (
              <div className="cta-row">
                <button
                  className="button-secondary"
                  disabled={isFetchingNextPage}
                  onClick={handleLoadMore}
                  type="button"
                >
                  {isFetchingNextPage ? "Loading..." : "Load More"}
                </button>
              </div>
            ) : null}
            {isFetching && !isFetchingNextPage && streams.length > 0 ? (
              <p className="helper">Refreshing the live board...</p>
            ) : null}
          </>
        ) : null}
        {!isLoading && streams.length === 0 ? (
          <div className="empty-card">
            <h3>No other streamers are live right now.</h3>
            <p className="helper">Use Refresh Suggestions to check again without interrupting your current stream.</p>
          </div>
        ) : null}
      </section>
    </div>
  );
}
