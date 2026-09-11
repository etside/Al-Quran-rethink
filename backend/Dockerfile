FROM python:3.12-slim

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

# run the importer on first boot (fails soft offline), then serve
CMD ["sh", "-c", "python scripts/import_quran.py --skip-morphology || true; uvicorn app.main:app --host 0.0.0.0 --port 8000"]
