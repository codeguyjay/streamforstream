# Backend

FastAPI backend for the initial StreamBaton flow.

## Responsibilities

- Resolve Twitch channels into canonical channel metadata.
- Add and remove live streamers from the live board.
- Refresh live streams every 5 minutes against Twitch to keep viewer counts and live status current.
- Credit one point per reported viewing minute, while rejecting self-views and duplicate minute reports.
- Support either in-memory storage or DynamoDB-backed point and ranking state.

## Prerequisites

- Docker Desktop

## Environment Variables

For local development, copy the example env file and fill in the values you need:

```powershell
Copy-Item .env.example .env.local
```

Set at least:

- `TWITCH_CLIENT_ID`
- `TWITCH_CLIENT_SECRET`

Optional:

- `TWITCH_SWEEPER_INTERVAL_SECONDS` (defaults to `300`)
- `FRONTEND_ORIGIN` (defaults to `http://localhost:3000`)
- `FRONTEND_ORIGINS` (comma-separated override when the backend should allow multiple frontend domains)
- `STREAMING_STORE_BACKEND` (`in_memory` by default, or `dynamodb`)
- `AWS_REGION` / `AWS_DEFAULT_REGION`
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` (`AWS_SESSION_TOKEN` too when using temporary creds locally)
- `DDB_ENDPOINT_URL`
- `DDB_STREAMER_STATE_TABLE_NAME`
- `DDB_VIEW_REPORTS_TABLE_NAME`

If you run DynamoDB mode with Docker locally, pass standard AWS SDK credentials in the env file or mount a shared AWS config into the container. Do not wrap env values in quotes when using `docker run --env-file`.

## Build And Run With Docker

```powershell
docker build -t streambaton-backend .
docker run --rm -p 8080:8080 --env-file .env.local streambaton-backend
```

The backend will be available at:

- API Base URL: `http://localhost:8080`
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`
- Health Check: `http://localhost:8080/health`

## OpenAPI

The frontend expects the backend schema at `http://localhost:8080/openapi.json`.

## Direct Docker Commands

```powershell
docker build -t streambaton-backend .
docker run --rm -p 8080:8080 --env-file .env.local streambaton-backend
```

## Notes

- The image does not include your `.env.local` file. You must provide env vars at runtime.
- `STREAMING_STORE_BACKEND=in_memory` is still the default local fallback.
- DynamoDB mode expects an existing `streamer_state` table with `live_viewers` and `live_engagement` GSIs, plus a `view_reports` table keyed by `viewer_id` / `viewed_minute`.
- Production AWS deploys can set `FRONTEND_ORIGINS=https://streambaton.tv,https://www.streambaton.tv` so both custom domains pass CORS.
- No automated unit tests are included by request.
