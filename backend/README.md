# Backend

FastAPI backend for the initial StreamForStream flow.

## Responsibilities

- Resolve Twitch channels into canonical channel metadata.
- Add and remove live streamers from the in-memory live board.
- Refresh live streams every 5 minutes against Twitch to keep viewer counts and live status current.
- Credit one point per reported viewing minute, while rejecting self-views and duplicate minute reports.

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

## Build And Run With Docker

```powershell
docker build -t streamforstream-backend .
docker run --rm -p 8080:8080 --env-file .env.local streamforstream-backend
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
docker build -t streamforstream-backend .
docker run --rm -p 8080:8080 --env-file .env.local streamforstream-backend
```

## Notes

- The image does not include your `.env.local` file. You must provide env vars at runtime.
- Storage is in memory only for this phase.
- No automated unit tests are included by request.
