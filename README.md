# Miraz — Al-Quran Re-think

**Miraz** is an open, scholarly, multi-layered Quran research platform. It lets you study any verse
through independent interpretive layers — linguistic root analysis, classical tafsir, graded hadith
with isnad graphs — with full transparency about sources, methods, and reliability.

> Design principle: only the Quran itself is treated as unqualified. Every other source is labeled
> with its methodology, provenance, and grade. Nothing is ever merged silently.

## Layers (roadmap)

| Layer | Methodology label | Status |
|---|---|---|
| Quran text + translations (Arabic, English, **Bengali**) | scripture / translation | ✅ Phase 1 |
| Word → root, morphology (Quranic Arabic Corpus) | linguistic analysis | ✅ Phase 1 |
| Classical tafsir (al-Jalalayn, Ibn Kathir, …) | classical-theological | Phase 2 |
| Hadith + isnad graph, narrator grades | hadith (sahih/hasan/daif grades) | Phase 3 |
| Layer comparison, contradiction flags | metadata-driven | Phase 4 |
| Ahl al-Bayt tafsir subset | ahl-al-bayt | Phase 5 |
| Contemporary linguistic (reference links) | contemporary-linguistic | Phase 5 |
| Scientific interpretation scaffold | scientific (user sources) | Phase 5 |

## Architecture

- `backend/` — FastAPI + SQLAlchemy (SQLite for dev, Postgres in Docker). API-first: `/verses`, `/words`, `/layers`, `/search`.
- `frontend/` — React + Vite + Tailwind. Verse view with toggleable layers and click-any-word root panel.
- `docker-compose.yml` — full stack deployment (backend, frontend, Postgres).

## Run locally (no Docker)

```bash
# Backend
cd backend && pip install -r requirements.txt
python scripts/import_quran.py      # fetches Quran + translations incl. Bengali; offline-safe demo seed
uvicorn app.main:app --reload       # http://localhost:8000/docs

# Frontend
cd frontend && npm install && npm run dev   # http://localhost:5173
```

## Data sources & attribution

- Quran text & translations: [quran.com API v4](https://api.quran.com) / Tanzil.net
- Morphology & roots: Quranic Arabic Corpus (Kais Dukes), open mirrors
- Hadith & grades: community open datasets (sunnah.com-compatible)
- Each served record carries `methodology`, `source`, and reliability metadata.

## License

Code: MIT. Data: licenses of the respective sources (see attribution above).
