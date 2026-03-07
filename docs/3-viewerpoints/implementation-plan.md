# Plan: Viewer-Only Support Link Flow

## Summary

Build a second frontend flow on top of the latest backend changes, while splitting view reporting by flow instead of routing everything through one API.

The app will support two distinct session modes:

- **Streamer session**: the existing cookie-backed flow for a Twitch channel owner using `/get-started`, `/instructions`, and `/view`
- **Viewer support session**: a new viewer-only flow at `/support/[channelLogin]` where the shared URL fixes the hosted/earning channel, the visitor picks another live stream to watch, and credits are earned for the hosted channel

This iteration should add structured request logging on the view-report APIs and around DynamoDB writes. It should not add a separate metrics pipeline yet.

## Key Changes

### Product and terminology

- Standardize the model around three roles:
  - **Hosted/Earning channel**: the streamer being promoted by the shared link
  - **Unregistered viewer**: the browser visitor, identified by the current IP-based backend logic
  - **Viewed channel**: the live stream currently being watched
- Keep two reporting identity models, one per flow:
  - the existing streamer flow can continue using the current IP-based `unregistered_viewer` behavior
  - the new channel-link flow should resolve the hosted channel to `channel_id`, use that `channel_id` as the canonical table key for writes, and report with a distinct `viewer_type` such as `unverified_channel`
- Treat `unverified_channel` as the default name in the plan unless implementation finds an enum naming conflict
- Do not use the promo flow to create or modify the main `streambaton_session` cookie

### New support route

- Add a new route: `/support/[channelLogin]`
- On page load:
  - Resolve `channelLogin` through the existing Twitch resolve endpoint
  - If invalid, show a clear invalid-channel state and do not start reporting
  - If valid, treat that resolved channel as the hosted/earning channel for the entire page session
- Page behavior:
  - Show hosted-channel context and copy such as `Watch live creators to support @hostedChannel`
  - Reuse the live-stream discovery board, excluding the hosted channel from the selectable list
  - Let the visitor choose another live stream to watch
  - Reuse the existing minute-based reporting loop shape, but send support-page reports through the dedicated channel-link reporting API
  - Never show `Go Live`
  - Never show the hosted channel's total points
  - Never show the hosted channel's live/offline status
- If there are no other live streams, show an empty state instead of falling back to the hosted channel

### Viewer-only session state

- Add a separate frontend-only support session model, stored in `sessionStorage`, not cookies
- The support session should contain:
  - hosted channel identity, including resolved `channel_id`
  - local viewer session points
  - optional started-at timestamp for display or reset behavior
- Session storage key should be namespaced by hosted channel ID, e.g. `streambaton_support_session:<channel_id>`
- The support session should:
  - survive refresh within the same browser session
  - end naturally when the browser session ends
  - remain isolated from the existing cookie-backed streamer session
- The support page should display **viewer session points**, not channel totals

### Share-link entry points

- Surface the hosted-channel share link in both:
  - `/instructions`
  - `/view`
- Share URL format: `/support/<channel_login>`
- Provide a copy-to-clipboard CTA using the current origin plus the streamer's canonical session channel login
- Copy and labels should make the distinction explicit:
  - this link is for supporters/viewers
  - it helps the hosted channel earn credits
  - it is not the streamer's own viewing dashboard

## Public APIs / Interfaces

- Reuse these existing backend APIs:
  - `POST /api/twitch/resolve-channel`
  - `GET /api/streams/live?exclude_channel_login=<hosted>`
- Split the current view reporting into two dedicated APIs:
  - one for the existing streamer/dashboard flow
  - one for the new channel-link support flow
- The new channel-link reporting API should treat the hosted `channel_id` as canonical for writes and set `viewer_type=unverified_channel`
- Add one backend response field to the view-report APIs:
  - `awarded_points: number`
  - value should be `POINTS_PER_VIEW` when credited, otherwise `0`
- Keep the existing streamer-flow request fields compatible with the current implementation where possible
- For the channel-link API, include or resolve:
  - hosted channel login from the URL
  - hosted `channel_id` as the canonical identity used for the write path
  - `viewed_channel_login`
  - `viewed_minute`
- Keep `viewer_total_points` in the streamer-flow response for backward compatibility, but the new support page should ignore it
- Add a frontend-only type for the support session, separate from the current `StreamerSession`

## Logging Requirements

- Add structured request logging on both view-report APIs
- Log each incoming report with enough context to debug behavior later:
  - route / flow name
  - `viewer_type`
  - hosted channel login
  - hosted `channel_id` when available
  - viewed channel login
  - viewed minute
- Add logging around DynamoDB persistence:
  - before attempting the write
  - after a successful write
  - after a failed write
- Failure logs should include the relevant request context and exception details, but should not log secrets, access tokens, or other sensitive payloads
- Do not build a separate analytics or metrics system in this iteration; logs are the source of truth for debugging and later analysis

## Test Plan

- Visiting `/support/<valid_channel>` works without any existing streamer cookie
- Visiting `/support/<invalid_channel>` shows a clear error state and does not report views
- The support page excludes the hosted channel from the live-stream list
- The support page never renders `Go Live`, hosted total points, or hosted live status
- Watching a selected stream from the support page sends the hosted channel through the channel-link reporting API and records it under the resolved hosted `channel_id`
- Local viewer session points increase only when the report API returns a credited result
- Refreshing the support page preserves viewer session points during the same browser session
- Closing the browser session clears the support session naturally
- The share-link CTA on `/instructions` and `/view` copies the correct `/support/<channel_login>` URL
- Existing `/view` behavior for streamer sessions remains unchanged
- Both view-report APIs emit request logs for each report attempt
- Successful DynamoDB writes emit a success log
- Failed DynamoDB writes emit an error log with request context

## Assumptions and Defaults

- The existing IP-based `unregistered_viewer` model stays in place for the current streamer flow
- The new channel-link flow uses hosted `channel_id` as the canonical write identity and `viewer_type=unverified_channel`
- The support flow is **hosted earns, viewer picks**
- Viewer session state is **session-only storage**
- Shared URLs use a **path route**
- Share-link CTA appears on **both Instructions and View**
- The hosted channel is resolved/validated from the URL on every support-page entry
- The support-page local tally is a client-side convenience view, not a source of truth for the hosted channel's total stored points
- There is no dedicated metrics pipeline in this iteration; debugging and later analysis rely on request/write logs
