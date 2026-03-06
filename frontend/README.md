# Frontend

Next.js application for the StreamForStream landing page and anonymous streamer workflow.

## Responsibilities

- Show the live discovery board on the landing page.
- Capture and persist the streamer session in a browser-session cookie.
- Guide the user through setup instructions.
- Let the user start viewing, go live, stop streaming, and report viewed minutes.

## Required Environment

Copy `.env.example` to `.env.local` and set:

- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`

## Install

```powershell
npm.cmd install
```

## Run

```powershell
npm.cmd run dev
```

## Build / Lint

```powershell
npm.cmd run lint
npm.cmd run build
```

## OpenAPI Client

The checked-in client lives under `src/api`.

To regenerate it after backend API changes:

1. Save `http://localhost:8000/openapi.json` to `frontend/openapi.json`.
2. Run `npx openapi-typescript-codegen --input ./openapi.json --output ./src/api`.
