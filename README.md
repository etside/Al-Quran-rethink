# Miraz — Al-Quran Research Platform (QuranLayers: Bengali-integrated)

**Miraz** is an open, scholarly, multi-layered Quran research platform for
**Bengali-speaking users**: study any verse with Arabic text, Bengali +
English translations, word-by-word Bengali glosses with transliteration,
root/morphology analysis in Bengali, contextual (asbab/historical/linguistic)
notes, and layered Bengali tafsir summaries — with full transparency about
sources, methods, and reliability.

> Design principle: only the Quran itself is treated as unqualified. Every other source is labeled
> with its methodology, provenance, and grade. Nothing is ever merged silently.

## Layers (Bengali-integrated)

| Layer | Methodology label | Status |
|---|---|---|
| Quran text + translations (Arabic, English, **Bengali** — Taisirul Quran + alternates) | scripture / translation | ✅ live (6,236 verses) |
| Word-by-word Bengali + transliteration + tajweed reading aid (শব্দে শব্দে) | linguistic analysis | ✅ live — 77,429 words (QuranWBW Bengali WbW + quran.com transliteration) |
| Root & morphology with Bengali glosses (Quranic Arabic Corpus 0.4 + Lugatul Quran / Amar Arabi Ovidhan / Al-Kamus) | linguistic analysis | ✅ live — 49,967 rooted words, 77,429 with POS |
| Bengali root dictionary explorer (ধাতু অভিধান) | linguistic analysis | ✅ live — all 1,642 roots (29 dictionary, 1,613 labeled derived-draft) |
| Context of revelation in Bengali (শানে নুযূল, history, early-Arabic semantics) | classical-theological | ✅ live — verse notes + chapter fallback for all 114 surahs |
| Classical tafsir in Bengali — Ahsanul Bayaan + Abu Bakr Zakaria full text; Jalalayn, Ibn Kathir, Maariful summaries | classical-theological | ✅ live — 12,494 entries (4 source-side gaps) |
| Ahl al-Bayt tafsir subset | ahl-al-bayt | planned |
| Contemporary linguistic (reference links) | contemporary-linguistic | planned |
| Hadith + isnad graph, narrator grades | hadith (sahih/hasan/daif grades) | planned |
| Scientific interpretation scaffold | scientific (user sources) | planned |

Seed scope honesty: every one of the 6,236 verses carries full Bengali layers
(77,429 word glosses, transliteration, roots, 12,494 tafsir entries, verse or
chapter-level context). The root dictionary covers all 1,642 Quranic roots;
1,613 auto-derived entries are explicitly labeled derived-draft (majority-gloss
summary, needs dictionary verification) per the transparency principle.

## Architecture — one webapp, one origin

- `backend/` — FastAPI + SQLAlchemy (SQLite baked in / persisted via volume).
  Serves the API (`/api/*`: `/verses`, `/words`, `/roots`, `/dictionary`,
  `/tafsir`, `/context`, `/bn/*`, `/layers`, `/search`) **and** the built React
  UI (`/`) from a single process — no CORS, no split deployments.
- `frontend/` — React + Vite + Tailwind. Bengali-first UI (বাং/EN toggle), verse view with শব্দে শব্দে / তাফসীর / প্রেক্ষাপট tabs, click-any-word Bengali root panel, ধাতু explorer, Bengali search. Same-origin `/api` by default (`VITE_API_BASE` only needed for split setups).
- `Dockerfile` — single image: builds the UI, bundles API + data, runs `scripts/ensure_data.py` on boot, serves on `$PORT`.
- `docker-compose.yml` — one service (`web` on :8000, database persisted).
- `vercel.json` — one Vercel project: builds UI into `backend/static/`, all routes served by `backend/api/index.py`.

## Quick Start

### Prerequisites
- Python 3.9+, Node.js 18+

### Run it (single webapp)

```bash
# Two-server dev with HMR:
./start-dev.sh

# True single webapp — UI + API on http://localhost:8000 :
./start-dev.sh --single
```

### Manual setup

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python scripts/import_quran.py      # base text (first run only)
python scripts/ensure_data.py       # all Bengali layers (idempotent)
uvicorn app.main:app --port 8000    # UI at /, API at /api, docs at /docs
```

```bash
cd frontend
npm install
npm run dev                         # dev UI on :5173 (proxies /api to :8000)
VITE_API_BASE= npm run build        # production bundle (picked up by the API)
```

Key endpoints: `GET /` (UI), `GET /api/bn/status`,
`GET /api/bn/verse/{ch}/{v}`, `GET /api/verses/{ch}/{v}/words`,
`GET /api/roots?q=দয়া`, `GET /api/dictionary/roots/{root}`,
`GET /api/tafsir/{ch}/{v}`, `GET /api/context/{ch}/{v}`,
`GET /api/search?q=...&lang=bn`, `GET /api/layers`, `GET /web-status`.

### Data pipeline (all idempotent, fail-soft)

```bash
python scripts/import_quran.py          # base text + translations + English WbW
python scripts/import_morphology.py     # QAC 0.4 roots/POS/lemma (auto-downloads file if missing)
python scripts/import_transliteration.py# quran.com transliteration for all words
python scripts/import_bengali_wbw.py    # QuranWBW Bengali word glosses (needs backend/data/qwbw_bn.json)
python scripts/import_bengali_tafsir.py # Ahsanul Bayaan + Zakaria tafsir, all verses
python scripts/derive_root_glosses.py   # Bengali gloss for every root (majority vote, labeled draft)
python scripts/seed_chapter_context.py  # Makki/Madani + famous-asbab context, all 114 surahs
python scripts/seed_bengali.py          # hand-verified core backfill (Fatiha + Baqarah 1–5)
# …or simply: python scripts/ensure_data.py   (runs every missing piece; used by Docker boot)
```

## Deployment — one webapp everywhere

For details, see [DEPLOYMENT.md](DEPLOYMENT.md).

```bash
# Docker (single image: UI + API + data on :8000)
docker compose up -d --build
# → http://localhost:8000/ (UI), /docs (API docs), /health, /web-status
```

```bash
# Vercel (single project, repo root)
vercel --prod
# buildCommand compiles the UI into backend/static/; every route is served
# by backend/api/index.py (API + static UI, one origin).
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE` | Only for split setups; leave empty for the single webapp | `""` (same-origin `/api`) |
| `ALLOWED_ORIGINS` | CORS origins (same-origin needs none) | `*` |
| `MIRAZ_DB` | SQLite database path | `backend/miraz.db` (`/data/miraz.db` in Docker) |
| `MIRAZ_STATIC` | Built UI directory override | `backend/static/` → `frontend/dist/` |
| `PORT` | Server port (Docker/hosts) | `8000` |

## Data sources & attribution

- Quran text & translations: [quran.com API v4](https://api.quran.com) / Tanzil.net
  (Bengali: Taisirul Quran resource 161; alternates 163 Sheikh Mujibur Rahman, 162 Rawai Al-bayan)
- Bengali word-by-word: QuranWBW.com Bengali WbW (`words-data/translations/5`,
  full-Quran file mirrored to `backend/data/qwbw_bn.json`), QUL (qul.tarteel.ai),
  Corpus Quran Bengali glosses — via `scripts/import_bengali_wbw.py`
- Morphology & roots: Quranic Arabic Corpus 0.4 (Kais Dukes, GPL — verbatim file
  kept at `backend/data/corpus_morphology.txt` with its license header; attribution
  + link per its terms of use), open mirrors
- Bengali tafsir full text: Tafsir Ahsanul Bayaan + Tafsir Abu Bakr Zakaria via
  quran.com API v4 (HTML stripped, attribution kept per verse)
- Bengali root glossaries: Mukammal Lugatul Quran (Maulana Ahmad Maimun / Maulana Saeed Ahmad Ayubi),
  Amar Arabi Ovidhan, Al Kamus (Dr. Kamrul Ahsan), শব্দে শব্দে আল কুরআন
- Bengali tafsir summaries (short, attributed; full text via publishers): Tafsir Ibn Kathir
  (tr. Dr. Muhammad Mujibur Rahman), Tafsir Tabari (Islamic Foundation Bangladesh),
  Maariful Quran (tr. Muhiuddin Khan), Tafsir Jalalayn, Tafhimul Quran
- Hadith & grades: community open datasets (sunnah.com-compatible)
- Each served record carries `methodology`, `source`, and reliability metadata.

## License

Code: MIT. Data: licenses of the respective sources (see attribution above).
