# BharatStandards AI — Vercel Backend

This folder is a deployment copy of `backend/app`. The source of truth remains `backend/app`.
Run `npm run vercel:prepare` from the project root before every backend deployment.

## Deploy

```powershell
npm run vercel:prepare
cd vercel-backend
npm install -g vercel
vercel login
vercel
```

Add Production environment variables in Vercel, especially:

- `AI_PROVIDER=nvidia`
- `NVIDIA_API_KEY`
- `NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1`
- `NVIDIA_MODEL=meta/llama-3.3-70b-instruct`
- `DEMO_MODE=true` (until the verified REAL retrieval layer is connected)
- `FIREBASE_PROJECT_ID=bharatstandards-ai`
- `FIREBASE_SERVICE_ACCOUNT_JSON` (service-account JSON as one Vercel secret)
- `CORS_ORIGINS=https://bharatstandards-ai.web.app,https://bharatstandards-ai.firebaseapp.com`

Then:

```powershell
vercel --prod
```

Verify:

- `/api/health`
- `/api/ai/test`
- `/api/firestore/health`

LM Studio intentionally remains local-only. Vercel production forces/uses NVIDIA because `127.0.0.1:1234` on Vercel is not your development PC.
