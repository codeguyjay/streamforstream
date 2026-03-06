# Backend

FastAPI backend for the initial StreamForStream flow.

## Responsibilities

- Resolve Twitch channels into canonical channel metadata.
- Add and remove live streamers from the in-memory live board.
- Refresh live streams every 5 minutes against Twitch to keep viewer counts and live status current.
- Credit one point per reported viewing minute, while rejecting self-views and duplicate minute reports.

## Required Environment

Copy `.env.example` to `.env` and set:

- `TWITCH_CLIENT_ID`
- `TWITCH_CLIENT_SECRET`
- `TWITCH_SWEEPER_INTERVAL_SECONDS` (optional, defaults to `300`)
- `FRONTEND_ORIGIN` (optional, defaults to `http://localhost:3000`)

## Install

```powershell
python -m pip install -r requirements.txt
```

## Run

```powershell
uvicorn app.main:app --reload --port 8000
```

## OpenAPI

The frontend expects the backend schema at `http://localhost:8000/openapi.json`.

## Notes

- Storage is in memory only for this phase.
- No automated unit tests are included by request.
