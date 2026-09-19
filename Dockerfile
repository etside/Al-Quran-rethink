# Miraz — single webapp image (FastAPI API + bundled React UI, one origin).
# Stage 1 builds the frontend; stage 2 serves API + static UI via uvicorn.
# The SQLite database ships baked in when present in build context
# (backend/miraz.db); otherwise scripts/ensure_data.py populates it on boot.

FROM node:22-slim AS web
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MIRAZ_DB=/srv/miraz.db \
    MIRAZ_STATIC=/srv/static \
    PORT=8000
WORKDIR /srv
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY backend/scripts ./scripts
COPY backend/api ./api
COPY backend/miraz.db ./miraz.db
COPY backend/data ./data
COPY --from=web /app/frontend/dist ./static
EXPOSE 8000
CMD ["sh", "-c", "mkdir -p \"$(dirname \"$MIRAZ_DB\")\" && { [ -f \"$MIRAZ_DB\" ] || cp /srv/miraz.db \"$MIRAZ_DB\" 2>/dev/null || true; }; python scripts/ensure_data.py || true; uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
