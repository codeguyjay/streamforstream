# StreamBaton

Anonymous Twitch streamer discovery for creators who want to trade real viewing time and chat engagement.

## Repo Layout

- `frontend`: Next.js app for the landing page, anonymous session flow, instructions, and view board.
- `backend`: FastAPI app with Twitch integration, live-stream storage, and point tracking.
- `docs`: Product and implementation notes.
- `infra`: AWS CDK app for the Route53, Amplify, ECS/Fargate, and DynamoDB deployment.

## Prerequisites

- Docker Desktop
- Node.js 20+ with `npm`
- A Twitch developer application with a `Client ID` and `Client Secret`

## One-Time Setup

### 1. Create Twitch API credentials

- Create or use an existing Twitch developer application.
- Copy the Twitch `Client ID`.
- Copy the Twitch `Client Secret`.
- Keep both values ready for the backend `.env.local` file.

### 2. Set up the backend

From the repo root:

```powershell
cd backend
Copy-Item .env.example .env.local
```

Then edit `backend/.env.local` and set:

```env
TWITCH_CLIENT_ID=your-twitch-client-id
TWITCH_CLIENT_SECRET=your-twitch-client-secret
TWITCH_SWEEPER_INTERVAL_SECONDS=300
FRONTEND_ORIGIN=http://localhost:3000
FRONTEND_ORIGINS=
STREAMING_STORE_BACKEND=in_memory
```

Optional DynamoDB mode:

```env
STREAMING_STORE_BACKEND=dynamodb
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_SESSION_TOKEN=
DDB_ENDPOINT_URL=
DDB_STREAMER_STATE_TABLE_NAME=your-streamer-state-table
DDB_VIEW_REPORTS_TABLE_NAME=your-view-reports-table
```

When using `docker run --env-file .env.local`, do not wrap values in quotes. Docker passes those quotes through literally.

### 3. Set up the frontend

Open a second terminal and run:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm.cmd install
```

Then confirm `frontend/.env.local` contains:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8080
```

Note for PowerShell: use `npm.cmd` instead of `npm` if your machine blocks `npm.ps1` scripts.

## Running The App

### Terminal 1: backend

```powershell
cd c:\Users\toonm\workspace\streamforstream\backend
docker build -t streambaton-backend .
docker run --rm -p 8080:8080 --env-file .env.local streambaton-backend
```

Expected URLs:

- API root: `http://localhost:8080/`
- API docs: `http://localhost:8080/docs`
- OpenAPI schema: `http://localhost:8080/openapi.json`

### Terminal 2: frontend

```powershell
cd frontend
npm.cmd run dev
```

Expected URL:

- App: `http://localhost:3000`

## First Run Checklist

1. Open `http://localhost:3000`.
2. Confirm the landing page loads.
3. Click `Get Started`.
4. Enter a Twitch handle or channel URL.
5. After validation, confirm you are redirected to `/instructions`.
6. Click `Start Viewing` to open the live board.
7. If your Twitch channel is currently live, click `Go Live` and confirm it appears on the board.

## What The Current Version Does

- Stores the Twitch profile in a browser-session cookie called `streambaton_session`
- Validates channels against the real Twitch API
- Tracks live streamers in either backend memory or DynamoDB
- Re-checks live streamers against Twitch on a background interval
- Awards one point per reported viewing minute while debiting the watched streamer balance
- Resets live streams and point totals when the backend restarts in `in_memory` mode

## Useful Commands

### Backend

```powershell
cd c:\Users\toonm\workspace\streamforstream\backend
docker build -t streambaton-backend .
docker run --rm -p 8080:8080 --env-file .env.local streambaton-backend
```

### Frontend

```powershell
cd frontend
npm.cmd run dev
npm.cmd run lint
npm.cmd run build
```

### Regenerate the frontend OpenAPI client

From the repo root after the backend is running:

```powershell
Invoke-WebRequest -Uri "http://localhost:8080/openapi.json" -OutFile "./frontend/openapi.json" -UseBasicParsing
cd frontend
npx openapi-typescript-codegen --input ./openapi.json --output ./src/api
```

## AWS Deployment

The AWS infrastructure now lives in `infra/` and mirrors the `gamenight` workspace pattern:

- DynamoDB in `us-west-2` for persistent streamer state and view reports
- ECS Fargate + ALB for the FastAPI backend at `https://api.streambaton.tv`
- Amplify Hosting for the Next.js frontend at `https://streambaton.tv` and `https://www.streambaton.tv`

See `infra/README.md` for the exact secret names, Route53 prerequisites, and CDK deploy order.

## Troubleshooting

- `This Twitch channel is not currently live.`: the backend successfully resolved the channel, but Twitch says it is offline.
- `TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET must be configured.`: your backend `.env.local` file is missing required values.
- Docker cannot start the backend: make sure Docker Desktop is running and `backend/.env.local` exists.
- Landing page loads but no streams appear: that is expected until at least one streamer goes live through the app.
- Points or live status disappear after restarting the backend: you are running with `STREAMING_STORE_BACKEND=in_memory`.

## Current Scope

- No user accounts yet. The frontend stores the canonical Twitch profile in a browser-session cookie.
- The backend can run with in-memory storage for local/dev or DynamoDB for persistent ranking and points.
- Twitch credentials are required for the backend because live validation and viewer counts use the real Twitch API.
