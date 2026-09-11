"""Vercel Python serverless entrypoint for the Miraz API.

Deploy the backend as its own Vercel project with `backend/` as the root
directory. Build Command should pre-generate the database (serverless FS is
read-only at runtime):

    pip install -r requirements.txt && python scripts/import_quran.py --skip-words

For production traffic prefer the Docker deployment (see README) — SQLite in a
serverless bundle is read-only and re-uploaded per deployment.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402

# Vercel expects the ASGI app as `app`
