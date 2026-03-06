"use client";

import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { TwitchService } from "@/api";
import { getErrorMessage } from "@/lib/errors";
import { useSessionStore } from "@/state/sessionStore";

export function GetStartedPage() {
  const router = useRouter();
  const session = useSessionStore((state) => state.session);
  const hydrated = useSessionStore((state) => state.hydrated);
  const setSession = useSessionStore((state) => state.setSession);
  const [channelInput, setChannelInput] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (hydrated && session) {
      router.replace("/instructions");
    }
  }, [hydrated, router, session]);

  const resolveChannelMutation = useMutation({
    mutationFn: () => TwitchService.resolveChannel({ channel_input: channelInput }),
    onSuccess: (resolved) => {
      setSession(resolved);
      setMessage("Twitch channel connected. Redirecting to setup instructions...");
      router.push("/instructions");
    },
    onError: (error) => {
      setMessage(getErrorMessage(error, "Unable to validate that Twitch channel."));
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    resolveChannelMutation.mutate();
  }

  if (!hydrated) {
    return <section className="panel"><p className="helper">Loading your session...</p></section>;
  }

  return (
    <section className="panel stack">
      <div>
        <p className="eyebrow">Step 1</p>
        <h1>Add your Twitch channel</h1>
        <p className="lede">Start viewing with as little friction as possible.</p>
      </div>

      <form className="input-row" onSubmit={handleSubmit}>
        <label className="helper" htmlFor="channel">
          Twitch handle or full channel URL
        </label>
        <input
          className="text-input"
          id="channel"
          onChange={(event) => setChannelInput(event.target.value)}
          placeholder="example: shroud or https://www.twitch.tv/shroud"
          value={channelInput}
        />
        <div className="cta-row">
          <button className="button-primary" disabled={resolveChannelMutation.isPending || !channelInput.trim()} type="submit">
            {resolveChannelMutation.isPending ? "Validating..." : "Save My Channel"}
          </button>
          <Link className="button-secondary" href="/">
            Back Home
          </Link>
        </div>
      </form>

      {message ? <p className={resolveChannelMutation.isError ? "error-text" : "status-text"}>{message}</p> : null}
    </section>
  );
}
