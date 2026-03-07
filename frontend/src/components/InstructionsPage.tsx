"use client";

import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { StreamsService } from "@/api";
import { getErrorMessage } from "@/lib/errors";
import { useSessionStore } from "@/state/sessionStore";

export function InstructionsPage() {
  const router = useRouter();
  const session = useSessionStore((state) => state.session);
  const hydrated = useSessionStore((state) => state.hydrated);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (hydrated && !session) {
      router.replace("/get-started");
    }
  }, [hydrated, router, session]);

  const goLiveMutation = useMutation({
    mutationFn: () => {
      if (!session) {
        throw new Error("A Twitch session is required before going live.");
      }
      return StreamsService.goLive({ channel_login: session.channel_login });
    },
    onSuccess: () => {
      setMessage("Your stream is now live on the board. Opening the viewing page...");
      router.push("/view");
    },
    onError: (error) => {
      setMessage(getErrorMessage(error, "Unable to mark your stream as live right now."));
    },
  });

  if (!hydrated || !session) {
    return <section className="panel"><p className="helper">Loading your session...</p></section>;
  }

  return (
    <div className="stack">
      <section className="panel stack">
        <div>
          <p className="eyebrow">Step 2</p>
          <h1>Work the loop</h1>
          <p className="lede">
            Your Twitch channel is saved as <strong>@{session.channel_login}</strong>. Watch other live creators,
            be active in their chat, and your points climb minute by minute.
          </p>
        </div>

        <div className="instruction-grid">
          <article className="instruction-card">
            <span className="instruction-index">1</span>
            <h3>Start Viewing</h3>
            <p className="helper">Open the live board, pick another streamer, and let the app report active minutes.</p>
          </article>
          <article className="instruction-card">
            <span className="instruction-index">2</span>
            <h3>Engage for points</h3>
            <p className="helper">Watch other streams and participate in chat. The current version tracks points but does not spend them yet.</p>
          </article>
          <article className="instruction-card">
            <span className="instruction-index">3</span>
            <h3>Go live</h3>
            <p className="helper">When Twitch says your channel is live, StreamBaton adds you to the ranked discovery board.</p>
          </article>
        </div>

        <div className="cta-row">
          <Link className="button-primary" href="/view">
            Start Viewing
          </Link>
          <button className="button-secondary" disabled={goLiveMutation.isPending} onClick={() => goLiveMutation.mutate()} type="button">
            {goLiveMutation.isPending ? "Checking Twitch..." : "Go Live Now"}
          </button>
        </div>

        {message ? <p className={goLiveMutation.isError ? "error-text" : "status-text"}>{message}</p> : null}
      </section>
    </div>
  );
}
