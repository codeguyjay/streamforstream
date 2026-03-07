# Frontend

Next.js application for the StreamBaton landing page and anonymous streamer workflow.

## Responsibilities

- Show the live discovery board on the landing page.
- Capture and persist the streamer session in a browser-session cookie.
- Guide the user through setup instructions.
- Let the user start viewing, go live, stop streaming, and report viewed minutes.

## Required Environment

Copy `.env.example` to `.env.local` and set:

- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8080`

## Install

```powershell
npm.cmd install
```

## Run

```powershell
npm.cmd run dev
```

Before starting the frontend, make sure the backend is running from the repo root with:

```powershell
cd ..\backend
docker build -t streambaton-backend .
docker run --rm -p 8080:8080 --env-file .env.local streambaton-backend
```

## Build / Lint

```powershell
npm.cmd run lint
npm.cmd run build
```

## OpenAPI Client

The checked-in client lives under `src/api`.

To regenerate it after backend API changes:

1. Save `http://localhost:8080/openapi.json` to `frontend/openapi.json`.
2. Run `npx openapi-typescript-codegen --input ./openapi.json --output ./src/api`.
