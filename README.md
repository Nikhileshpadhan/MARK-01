# MARK-01 Local Run and Deployment Guide

This project has two apps:
- `frontend/` (React + Vite)
- `marketmind/` (FastAPI backend)

## 1. Run Locally

### Backend (FastAPI)
1. Open terminal in `marketmind/`.
2. Create and activate virtual environment (if needed):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Create `.env` from `.env.example` and set real keys.
5. Start server:

```powershell
uvicorn main:app --host 127.0.0.1 --port 8000
```

If port 8000 is busy:

```powershell
uvicorn main:app --host 127.0.0.1 --port 8001
```

### Frontend (Vite)
1. Open terminal in `frontend/`.
2. Install dependencies:

```powershell
npm install
```

3. Ensure `.env` points to backend:

```env
VITE_API_URL=http://127.0.0.1:8000
VITE_REFRESH_INTERVAL=60000
```

4. Start frontend:

```powershell
npm run dev
```

## 2. CORS Setup (Deployment-safe)

Backend CORS is now environment driven.

Set these in `marketmind/.env`:

```env
CORS_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com
CORS_ALLOW_CREDENTIALS=false
```

Notes:
- Do not use `*` in production for `CORS_ORIGINS`.
- Keep `CORS_ALLOW_CREDENTIALS=false` unless you explicitly use cookie auth.
- If enabling credentials, origins must be explicit (no wildcard).

## 3. How to Verify CORS

### Browser check
1. Open frontend and perform API calls from UI.
2. In DevTools Network tab, check response headers include:
- `Access-Control-Allow-Origin: <your frontend origin>`

### Preflight check with curl (PowerShell)

```powershell
curl -i -X OPTIONS "http://127.0.0.1:8000/ranking/latest" `
  -H "Origin: http://localhost:5173" `
  -H "Access-Control-Request-Method: GET"
```

You should see CORS headers in response.

## 4. Pre-deploy Checklist (Common Mistakes)

1. Secrets exposure
- Do not commit real API keys.
- Keep only placeholders in `.env.example`.

2. Wrong backend startup directory
- Run `uvicorn main:app ...` from `marketmind/`, not project root.

3. Port conflicts
- If `WinError 10048`, another process is already using that port.
- Change port or stop existing process.

4. CORS mismatch
- Frontend domain must be listed in `CORS_ORIGINS`.
- Do not use wildcard in production.

5. Frontend API URL mismatch
- Ensure `VITE_API_URL` matches actual backend host/port.

6. Dependency drift
- Run `pip install -r requirements.txt` and `npm install` in fresh environment before release.

7. Unknown-company behavior expectations
- Unknown companies are resolved by backend logic and added to tracked ranking flow.
- LLM-based company-to-ticker resolution requires valid `GROQ_API_KEY`.

8. Recommendation/news fallback expectations
- If external APIs are unavailable, fallback signal/news logic may be used.
- Keep user warning visible because AI/data inference can be wrong.

## 5. Recommended Deployment Smoke Test

1. `GET /health` returns status `ok`.
2. Frontend loads ranking page without console/network CORS errors.
3. Search known symbol and unknown company name.
4. Open company details and verify score, engagement, prediction, and news sections render.
5. Trigger refresh once and verify data updates.
