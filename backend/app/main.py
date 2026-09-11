import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import chapters, layers, roots, search, verses, words

app = FastAPI(
    title="Miraz API",
    version="0.1.0",
    description=(
        "Open scholarly Quran research platform. Every served record carries "
        "methodology, source, and reliability metadata — only the Quran itself is unqualified."
    ),
)

# Comma-separated list, e.g. ALLOWED_ORIGINS=https://miraz.vercel.app,https://miraz.example
_origins = [
    o.strip()
    for o in os.environ.get(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chapters.router)
app.include_router(verses.router)
app.include_router(words.router)
app.include_router(roots.router)
app.include_router(layers.router)
app.include_router(search.router)


@app.get("/health")
def health():
    return {"ok": True, "service": "miraz-api"}
