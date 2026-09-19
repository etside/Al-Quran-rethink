import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .db import ensure_bengali_schema
from .routers import bengali, chapters, context, dictionary, layers, roots, search, tafsir, verses, words

ensure_bengali_schema()

app = FastAPI(
    title="Miraz — QuranLayers (Bengali-integrated)",
    version="0.3.0",
    description=(
        "Open scholarly Quran research platform: single webapp serving the "
        "Bengali-first UI and the research API from one origin. Every served "
        "record carries methodology, source, and reliability metadata — only "
        "the Quran itself is unqualified."
    ),
)

# Public read-only research API: permissive by default; set ALLOWED_ORIGINS
# (comma-separated) to restrict, e.g. https://miraz.vercel.app
_origins = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", "*").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chapters.router, prefix="/api")
app.include_router(verses.router, prefix="/api")
app.include_router(words.router, prefix="/api")
app.include_router(roots.router, prefix="/api")
app.include_router(dictionary.router, prefix="/api")
app.include_router(tafsir.router, prefix="/api")
app.include_router(context.router, prefix="/api")
app.include_router(bengali.router, prefix="/api")
app.include_router(layers.router, prefix="/api")
app.include_router(search.router, prefix="/api")


@app.get("/health")
def health():
    """Health check endpoint for monitoring and load balancers."""
    return {"ok": True, "service": "miraz-api", "version": app.version}


@app.get("/api/health")
def api_health():
    """API-specific health check with /api prefix."""
    return {"ok": True, "service": "miraz-api", "version": app.version}


# ── single-webapp static UI ────────────────────────────────────────────
# The React build is served from the same origin as the API, so the UI needs
# no VITE_API_BASE in single-app deployments. Resolution order:
#   1. $MIRAZ_STATIC, 2. backend/static/ (Docker + Vercel builds),
#   3. frontend/dist/ (repo-local `npm run build`).
# Absent a build, the API still runs standalone (dev uses Vite on :5173).

def _static_dir() -> Path | None:
    here = Path(__file__).resolve()
    candidates = []
    env = os.environ.get("MIRAZ_STATIC")
    if env:
        candidates.append(Path(env))
    candidates.append(here.parent.parent / "static")
    candidates.append(here.parent.parent.parent / "frontend" / "dist")
    for c in candidates:
        if c.is_dir() and (c / "index.html").is_file():
            return c
    return None


STATIC_DIR = _static_dir()


@app.get("/web-status", include_in_schema=False)
def web_status():
    """Whether the bundled web UI is being served by this process."""
    return {"web": STATIC_DIR is not None,
            "dir": str(STATIC_DIR) if STATIC_DIR else None}


if STATIC_DIR is None:

    @app.get("/", include_in_schema=False)
    def web_missing():
        """API-only mode (no frontend build bundled): point humans at /docs."""
        return {
            "service": "miraz-api",
            "version": app.version,
            "web": False,
            "docs": "/docs",
            "note": "Frontend build not bundled (set $MIRAZ_STATIC or build frontend/).",
        }

else:

    @app.get("/", include_in_schema=False)
    def web_root():
        return FileResponse(STATIC_DIR / "index.html")  # type: ignore[arg-type]

    @app.get("/{path:path}", include_in_schema=False)
    def web(path: str):
        """Static assets, favicon, and SPA fallback (registered last so
        /api/*, /health, /docs and /openapi.json keep priority)."""
        if path.startswith("api/") or path in (
            "api", "health", "docs", "redoc", "openapi.json", "web-status",
        ):
            raise HTTPException(404)
        target = STATIC_DIR / path  # type: ignore[operator]
        if path and target.is_file():
            return FileResponse(target)
        return FileResponse(STATIC_DIR / "index.html")  # type: ignore[arg-type]
