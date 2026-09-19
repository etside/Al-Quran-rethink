"""Vercel Python serverless entrypoint for the Miraz single webapp.

Deploy from the REPO ROOT as one Vercel project (see root vercel.json):
the build step compiles the React UI into backend/static/, and this
function serves both the API (/api/*) and the UI (/*) from one origin.

The SQLite database (backend/miraz.db) ships in the serverless bundle; the
runtime filesystem is read-only, which is fine for the read-only research
data. For write traffic / Phase 2+, move to a hosted DB (Turso / Neon) or
run the Docker single-image deployment on a server.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402

# Vercel expects the ASGI app as `app`
