# StreamBaton AWS Infrastructure

This CDK app follows the same overall AWS shape as `workspace/gamenight`, adapted for StreamBaton:

- `DdbStorageStack`: DynamoDB tables for persistent streamer state and deduplicated viewing minute reports
- `BackendStack`: ECS Fargate service behind an HTTPS Application Load Balancer at `api.streambaton.tv`
- `FrontendStack`: Amplify Hosting for the Next.js app at `streambaton.tv` and `www.streambaton.tv`

The current app does not use Cognito, so there is no auth stack yet.

## Regions

- `us-west-2`: all deployed stacks, matching the current `gamenight` CDK app configuration

## Prerequisites

- AWS account access to the same account used for `gamenight`
- Route53 hosted zone for `streambaton.tv`
- Existing Secrets Manager secret `twitch/api` in `us-west-2`
  - JSON keys: `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`
  - This repo reuses the same Twitch secret name as `gamenight`
- Secrets Manager secret `streambaton/github-token` in `us-west-2`
  - Plain string value containing a GitHub PAT with access to `codeguyjay/streamforstream`

Create the GitHub token secret if needed:

```powershell
aws secretsmanager create-secret `
  --name streambaton/github-token `
  --secret-string "YOUR_GITHUB_PAT" `
  --region us-west-2
```

## Install

```powershell
cd infra
npm.cmd ci
```

## Bootstrap

```powershell
cd infra
npx cdk bootstrap aws://585890465879/us-west-2
```

## Deploy

Deploy in this order:

```powershell
cd infra
npx cdk deploy DdbStorageStack
npx cdk deploy BackendStack
npx cdk deploy FrontendStack
```

## Stack Behavior

- `BackendStack` builds the Docker image from `backend/`
- the ECS task reads Twitch credentials from `twitch/api`
- the backend is configured for DynamoDB mode automatically
- the backend allows both `https://streambaton.tv` and `https://www.streambaton.tv` for CORS
- `FrontendStack` points Amplify at the `frontend/` app in the `codeguyjay/streamforstream` repo, branch `main`
- Amplify receives `NEXT_PUBLIC_API_BASE_URL` from the backend stack output automatically

## Useful Commands

```powershell
cd infra
npm.cmd run build
npx cdk synth
npx cdk diff
```
