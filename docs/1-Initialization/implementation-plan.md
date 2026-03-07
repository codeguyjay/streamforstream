# StreamBaton Initialization Implementation Plan

## Summary

- Bootstrap the monorepo into a runnable v1 with a `frontend` Next.js app, a `backend` FastAPI app, and updated docs for local development.
- Deliver the initial anonymous user flow end to end: landing page, get-started page, instructions page, view page, live-stream promotion, and minute-based point tracking.
- Use a browser session cookie as the canonical anonymous identity store for the current Twitch channel.
- Require real Twitch API integration from the start for channel validation, live verification, and viewer-count-based ranking.
- Keep all runtime data in memory for this phase; restart resets live sessions and points.

## Implementation Changes

- Create the `frontend` app with Next.js App Router, TypeScript, ESLint, `zustand`, `js-cookie`, `@tanstack/react-query`, and a checked-in API client under `src/api`.
- Create the `backend` app following the `gamenight` backend shape: `app/main.py`, `app/api`, `app/api/models`, `app/domain`, `app/storage`, and `app/twitch`.
- Add backend env/config handling for Twitch credentials, local CORS, and a startup background task that re-checks live streamers every 5 minutes.
- Implement a Twitch client/service layer that resolves a channel to canonical Twitch metadata and checks whether a channel is currently live, including `viewer_count`, `stream_title`, and `game_name`.
- Implement in-memory storage for canonical streamer profiles, active live sessions, per-viewer point totals, and per-minute view-report dedupe keys.
- Keep live ranking server-side as `viewer_count desc`, then `went_live_at asc`, and support excluding the current viewer's own channel from discovery.
- Build `/` to show the logo, ranked live streamers in the center, short getting-started instructions, and a `Get Started` CTA.
- Build `/get-started` to collect a Twitch channel, validate it through the backend, write the session cookie, and redirect to `/instructions`.
- Build `/instructions` to explain the flow and expose `Start Viewing` and `Go Live` actions.
- Build `/view` to show the live list, selected Twitch embed, current point balance, `Go Live` / `Stop Streaming` controls, and automatic minute-based view reporting while another streamer is selected and the page is visible.
- Update the root, `frontend`, and `backend` READMEs with setup steps, required env vars, run commands, and OpenAPI generation steps.

## Public APIs / Interfaces

- `POST /api/twitch/resolve-channel` accepts `{ channel_input: string }` and returns canonical Twitch channel metadata for session creation.
- `GET /api/streams/live?exclude_channel_login=<login>&limit=<n>` returns ranked live streamers plus the current viewer's point balance and live status.
- `POST /api/streams/go-live` accepts `{ channel_login: string }`, verifies the channel is live on Twitch, and upserts the live-session record.
- `POST /api/streams/go-offline` accepts `{ channel_login: string }` and removes the streamer from the in-memory live list immediately.
- `POST /api/views/report` accepts `{ viewer_channel_login: string, target_channel_login: string, viewed_minute: string }` and credits one point per unique viewer/target/minute key.

## Assumptions / Defaults

- Points are tracked and displayed in v1 but do not gate or charge `go-live` yet.
- Twitch integration is strict for this slice: local/dev and deployed environments must provide valid Twitch credentials.
- Anonymous feedback, real account/auth flows, DynamoDB persistence, and CDK/infra implementation remain out of scope for this initialization phase.
