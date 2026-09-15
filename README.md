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

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm or yarn

### Option 1: Using the startup script (recommended)

```bash
# Make the script executable
chmod +x start-dev.sh

# Run both backend and frontend
./start-dev.sh
```

### Option 2: Manual setup

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Import Quran data (if not already done)
python scripts/import_quran.py

# Start backend server
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173` and will proxy API requests to `http://localhost:8000`.

## Deployment

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Quick Deploy to Vercel

#### Frontend
1. Push your code to GitHub
2. Import the repository in Vercel
3. Set **Root Directory** to `frontend`
4. Add environment variable: `VITE_API_BASE` = your backend URL
5. Deploy!

#### Backend
1. Import the same repository in Vercel (create a second project)
2. Set **Root Directory** to `backend`
3. Add environment variable: `ALLOWED_ORIGINS` = your frontend URL
4. Deploy!

### Alternative: Docker

```bash
# Run full stack with Docker
docker compose up -d

# Access:
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE` | Backend API URL (frontend) | `""` (uses `/api` prefix) |
| `ALLOWED_ORIGINS` | CORS origins (backend) | `*` |
| `MIRAZ_DB` | SQLite database path (backend) | `../miraz.db` |

## Data sources & attribution

- Quran text & translations: [quran.com API v4](https://api.quran.com) / Tanzil.net
- Morphology & roots: Quranic Arabic Corpus (Kais Dukes), open mirrors
- Hadith & grades: community open datasets (sunnah.com-compatible)
- Each served record carries `methodology`, `source`, and reliability metadata.

## License

Code: MIT. Data: licenses of the respective sources (see attribution above).
