"""Vercel Python serverless entrypoint for the Miraz API.

Deploy the backend as its own Vercel project with `backend/` as the root
directory. The SQLite database (backend/miraz.db) is committed to the repo and
ships in the serverless bundle; the runtime filesystem is read-only, which is
fine for Phase 1's read-only data. For Phase 2+ move to a hosted DB (Turso /
Neon) or run the Docker deployment on a server.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402

# Vercel expects the ASGI app as `app`
