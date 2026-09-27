# BharatStandards AI

Government-grade prototype for Indian Standards recommendation and procurement intelligence.

## What this build includes

- Login-first protected React/Vite SPA
- Firebase Authentication: Email/Password, Google, sign-up, password reset, sign-out
- Firebase Hosting SPA routing (`dist/` + `index.html` rewrite)
- Local DEMO data mode with a visible warning banner
- Optional Firestore DEMO seed under `datasets/demo/...`
- Evaluation by Domain grouped bar chart
- Tender upload UI connected to a FastAPI document parser
- Lightweight parsing: PyMuPDF (PDF), python-docx, openpyxl, python-pptx, and native text/CSV/HTML parsing
- deterministic CSV/TXT/Markdown parsing
- backend-only NVIDIA/Gemma configuration (`google/gemma-4-31b-it`)
- explicit separation between document parsing, AI understanding and standards truth data

## 1. Frontend setup

```powershell
Copy-Item .env.example .env
notepad .env
npm install
npm run dev
```

Open `http://localhost:5173` — signed-out users are redirected to `/login`.

In Firebase Console enable:

- Authentication → Sign-in method → Email/Password
- Authentication → Sign-in method → Google
- Authentication → Settings → Authorized domains → add your hosting/custom domain if needed

Copy your Firebase Web App configuration into `.env`.

## 2. Full local document parsing

The model does not parse binary tender files. The architecture is:

```text
Browser file
  -> FastAPI
  -> lightweight format-specific parser
  -> normalized text + sections
  -> Gemma procurement understanding
```

Run frontend + backend:

```powershell
npm run dev:full
```

The first run creates `backend/.venv` and installs `backend/requirements.txt`, including the lightweight parser packages.

Backend URLs:

- `http://127.0.0.1:8000/api/health`
- `http://127.0.0.1:8000/docs`
- `POST /api/documents/parse`
- `POST /api/ai/requirement-profile`

## 3. NVIDIA key

Put this only in the root `.env` used by the backend:

```env
NVIDIA_API_KEY=...
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=google/gemma-4-31b-it
```

Never create `VITE_NVIDIA_API_KEY`.

## 4. Demo Firestore data

See `DEMO_FIRESTORE.md`.

Demo data is isolated at:

```text
datasets/demo/...
```

Future verified data is reserved for:

```text
datasets/real/...
```

Seed demo data:

```powershell
$env:FIREBASE_PROJECT_ID="bharatstandards-ai"
$env:FIREBASE_SERVICE_ACCOUNT_PATH="C:\secure\service-account.json"
npm run seed:demo
```

## 5. Firebase deploy

```powershell
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
npm run build
firebase use default
firebase deploy
```

`firebase.json` deploys Firestore rules/indexes and static Hosting. Hosting rewrites SPA routes to `/index.html`.

## Prototype boundary

The UI currently contains DEMO recommendation records. They are not official BIS records. Real standards data should only enter `datasets/real` after the verified ingestion/validation pipeline is added.

See `MAJOR_TEST_CHECKLIST.md` for the current functional test matrix.

## Python 3.14 backend note

This build uses a Python 3.14-compatible lightweight parsing dependency set. If you previously ran an older build that created `backend/.venv`, remove that virtual environment once before starting the updated project:

```powershell
Remove-Item -Recurse -Force backend\.venv -ErrorAction SilentlyContinue
npm run dev:full
```

The backend bootstrap recreates the environment and installs the compatible dependencies automatically.

## AI provider: LM Studio or NVIDIA

The backend supports two OpenAI-compatible providers. LM Studio is the default local provider and discovers the currently served model from `http://127.0.0.1:1234/v1/models` when `LM_STUDIO_MODEL=auto`. NVIDIA remains available as an online fallback. The active provider can be changed from Settings without exposing API keys to the frontend. See `LM_STUDIO_SETUP.md`.

## Production Hosting: Firebase + Vercel + Firestore

The production hosting split is now supported without changing the analysis pipeline:

- **Frontend:** Firebase Hosting
- **Backend:** Vercel FastAPI (`vercel-backend/api/index.py`)
- **Production AI:** NVIDIA hosted API
- **Local AI:** LM Studio remains available through the normal local FastAPI backend
- **Database:** Cloud Firestore; the Vercel backend can initialize Firebase Admin from server-only environment variables

Prepare/deploy the backend with `npm run vercel:prepare`, then deploy from `vercel-backend`. After Vercel returns the backend URL, configure the Firebase frontend with:

```powershell
npm run api:production -- https://YOUR-BACKEND.vercel.app
npm run build
firebase deploy --only hosting
```

See `VERCEL_BACKEND_FIRESTORE.md` for the full environment-variable and deployment checklist.
