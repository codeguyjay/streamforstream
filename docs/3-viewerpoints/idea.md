
Plan

Plan: Viewer-Only Support Link Flow
Summary
Build a second frontend flow on top of the latest IP-based viewer_id model instead of redesigning storage again.

The app will support two distinct session modes:

Streamer session: the existing cookie-backed flow for a Twitch channel owner using /get-started, /instructions, and /view
Viewer support session: a new viewer-only flow at /support/[channelLogin] where the shared URL fixes the hosted/earning channel, the visitor picks another live stream to watch, and credits are earned for the hosted channel
This plan should be written to docs/3-viewerpoints/implementation-plan.md once approved, leaving docs/3-viewerpoints/idea.md as ideation.

Key Changes
Product and terminology
Standardize the model around three roles:
Hosted/Earning channel: the streamer being promoted by the shared link
Unregistered viewer: the browser visitor, identified by the current IP-based backend logic
Viewed channel: the live stream currently being watched
Keep the current latest-commit backend identity model in place:
earning_channel_login remains the promoted channel
viewer_type remains unregistered_viewer
IP-based viewer_id generation remains server-side for now
Do not use the promo flow to create or modify the main streambaton_session cookie
New support route
Add a new route: /support/[channelLogin]
On page load:
Resolve channelLogin through the existing Twitch resolve endpoint
If invalid, show a clear invalid-channel state and do not start reporting
If valid, treat that resolved channel as the hosted/earning channel for the entire page session
Page behavior:
Show hosted-channel context and copy such as “Watch live creators to support @hostedChannel”
Reuse the live-stream discovery board, excluding the hosted channel from the selectable list
Let the visitor choose another live stream to watch
Reuse the existing minute-based reporting loop against POST /api/views/report
Never show Go Live
Never show the hosted channel’s total points
Never show the hosted channel’s live/offline status
If there are no other live streams, show an empty state instead of falling back to the hosted channel
Viewer-only session state
Add a separate frontend-only support session model, stored in sessionStorage, not cookies
The support session should contain:
hosted channel identity
local viewer session points
optional started-at timestamp for display or reset behavior
Session storage key should be namespaced by hosted channel, e.g. streambaton_support_session:<channel_login>
The support session should:
survive refresh within the same browser session
end naturally when the browser session ends
remain isolated from the existing cookie-backed streamer session
The support page should display viewer session points, not channel totals
Share-link entry points
Surface the hosted-channel share link in both:
/instructions
/view
Share URL format: /support/<channel_login>
Provide a copy-to-clipboard CTA using the current origin plus the streamer’s canonical session channel login
Copy and labels should make the distinction explicit:
this link is for supporters/viewers
it helps the hosted channel earn credits
it is not the streamer’s own viewing dashboard
Public APIs / Interfaces
Reuse these existing backend APIs:
POST /api/twitch/resolve-channel
GET /api/streams/live?exclude_channel_login=<hosted>
POST /api/views/report
Add one backend response field to POST /api/views/report:
awarded_points: number
value should be POINTS_PER_VIEW when credited, otherwise 0
Keep existing request fields:
earning_channel_login
viewed_channel_login
viewed_minute
Keep viewer_total_points in the response for backward compatibility with the existing streamer flow, but the new support page should ignore it
Add a frontend-only type for the support session, separate from the current StreamerSession
Test Plan
Visiting /support/<valid_channel> works without any existing streamer cookie
Visiting /support/<invalid_channel> shows a clear error state and does not report views
The support page excludes the hosted channel from the live-stream list
The support page never renders Go Live, hosted total points, or hosted live status
Watching a selected stream from the support page sends earning_channel_login=<hosted> and viewed_channel_login=<selected>
Local viewer session points increase only when the report API returns a credited result
Refreshing the support page preserves viewer session points during the same browser session
Closing the browser session clears the support session naturally
The share-link CTA on /instructions and /view copies the correct /support/<channel_login> URL
Existing /view behavior for streamer sessions remains unchanged
Assumptions and Defaults
The latest IP-based unregistered-viewer model stays in place for this iteration; this plan does not undo it
The support flow is hosted earns, viewer picks
Viewer session state is session-only storage
Shared URLs use a path route
Share-link CTA appears on both Instructions and View
The hosted channel is resolved/validated from the URL on every support-page entry
The support-page local tally is a client-side convenience view, not a source of truth for the hosted channel’s total stored points
