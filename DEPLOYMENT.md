# Miraz — Deployment Guide (single webapp)

One process serves everything: the React UI at `/` and the research API at
`/api/*` (docs at `/docs`, health at `/health`, UI status at `/web-status`).
There are no split frontend/backend deployments — every target below runs the
same single image / single serverless function.

## Option A — Docker (recommended for servers)

```bash
docker compose up -d --build
```

- UI: http://localhost:8000/
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health (`{"ok": true, ...}`)
- UI bundle status: http://localhost:8000/web-status

How it works: the multi-stage `Dockerfile` builds the React UI, bundles the
FastAPI app + `miraz.db` + data files, then boots with
`scripts/ensure_data.py` (idempotent: fills only missing data, fails soft
offline) and serves on `$PORT`.

Persistence: the database lives at `/data/miraz.db` on the `miraz-data`
volume (the baked-in DB is copied there on first boot). Rebuilds never lose
data; `docker compose down -v` resets it (a fresh boot re-imports, slow).

Production hardening:
- Set `ALLOWED_ORIGINS=https://your-domain` (same-origin needs no CORS, but
  explicit is better).
- Put a TLS reverse proxy (Caddy/Traefik) in front; the app itself is plain HTTP.

## Option B — Vercel (single project)

1. Push the repo to GitHub; import it in Vercel with **Root Directory = repo root**.
2. No framework preset needed — root `vercel.json` does it all:
   - `buildCommand` compiles the UI (`VITE_API_BASE=` for same-origin) into
     `backend/static/`;
   - every route is served by `backend/api/index.py` (FastAPI: API + static UI).
3. Environment: none required. Optional: `ALLOWED_ORIGINS=https://<your-app>.vercel.app`.
4. `miraz.db` ships inside the function bundle (read-only at runtime — fine,
   the research data is read-only). For write traffic use Docker + a hosted DB.

## Option C — bare host / VPS

```bash
cd backend && pip install -r requirements.txt && python scripts/ensure_data.py
cd ../frontend && npm ci && VITE_API_BASE= npm run build
cd ../backend && MIRAZ_DB=$PWD/miraz.db uvicorn app.main:app --host 0.0.0.0 --port 8000
```

(`ensure_data.py` = full pipeline: base text, morphology, transliteration,
Bengali glosses, tafsir, roots, context, hand-seed backfill.)

## Local development

```bash
./start-dev.sh           # Vite HMR :5173 + API :8000 (proxy)
./start-dev.sh --single  # production-like: everything on :8000
```

## Troubleshooting

### `/` shows API-only JSON instead of the UI
The frontend build isn't bundled (`/web-status` → `{"web": false}`). Build it:
`cd frontend && VITE_API_BASE= npm run build` (API auto-discovers
`frontend/dist/`), or set `$MIRAZ_STATIC` to a dist directory.

### UI calls the wrong backend
The bundle bakes `VITE_API_BASE` at build time. For single-origin serving it
must be empty: rebuild with `VITE_API_BASE= npm run build`. (A stale
`.env.local` pointing at an old split backend is the usual culprit.)

### CORS errors
Only possible in split setups (Vite dev proxy or custom `VITE_API_BASE`).
Set `ALLOWED_ORIGINS` to the UI origin.

### Database issues
- Check `miraz.db` exists next to `backend/` (or `$MIRAZ_DB`).
- Run `python backend/scripts/ensure_data.py` to fill gaps.
- Docker: `docker compose logs web` shows which boot steps ran/skipped.

## Monitoring
- `GET /health` → `{"ok": true, "service": "miraz-api", "version": "0.3.0"}`
- `GET /web-status` → `{"web": true, "dir": "..."}` when the UI is bundled.
- Vercel: Dashboard → Project → Deployments → Logs (build + function).
