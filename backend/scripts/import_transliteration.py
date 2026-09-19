#!/usr/bin/env python3
"""Bulk transliteration import for ALL words (real data, quran.com API v4).

Fills Word.transliteration from the `transliteration` word field
(e.g. "bis'mi"). Only NULL cells are filled, preserving hand-set seed rows.
Verse-number marker tokens (char_type "end") are skipped.

Usage:
  python scripts/import_transliteration.py [--limit 3]
"""

import argparse
import os
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.db import SessionLocal, engine, ensure_bengali_schema  # noqa: E402
from app.models import Verse, Word  # noqa: E402
from scripts.import_quran import backoff_fetch  # noqa: E402

API = "https://api.quran.com/api/v4"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--db", default=os.environ.get("MIRAZ_DB", str(
        Path(__file__).resolve().parent.parent / "miraz.db")))
    args = ap.parse_args()
    os.environ["MIRAZ_DB"] = args.db
    ensure_bengali_schema()
    db = SessionLocal()

    verse_ids = {(v.chapter_id, v.number): v.id for v in db.query(Verse).all()}
    existing = {(w.verse_id, w.position): (w.id, w.transliteration)
                for w in db.query(Word).all()}

    updates = []
    max_ch = args.limit or 114
    with httpx.Client(headers={"User-Agent": "Miraz/0.2 (transliteration import)"}) as client:
        for ch in range(1, max_ch + 1):
            page = 1
            while True:
                time.sleep(0.4)
                data = backoff_fetch(
                    client, f"{API}/verses/by_chapter/{ch}",
                    {"words": "true", "per_page": 50, "page": page,
                     "word_fields": "text_uthmani,transliteration", "fields": "text_uthmani"})
                verses = data.get("verses", [])
                if not verses:
                    break
                for v in verses:
                    _, num = (int(x) for x in v["verse_key"].split(":"))
                    vid = verse_ids.get((ch, num))
                    if vid is None:
                        continue
                    for w in v.get("words", []):
                        if w.get("char_type_name") == "end":
                            continue
                        hit = existing.get((vid, w["position"]))
                        if hit is None or hit[1] is not None:
                            continue
                        tr = (w.get("transliteration") or {}).get("text")
                        if tr:
                            updates.append((tr, hit[0]))
                meta = data.get("pagination") or {}
                if page >= meta.get("total_pages", 1):
                    break
                page += 1
            print(f"chapter {ch}: {len(updates)} pending updates", flush=True)

    if updates:
        raw = engine.raw_connection()
        try:
            cur = raw.cursor()
            cur.executemany("UPDATE words SET transliteration=? WHERE id=?", updates)
            raw.commit()
        finally:
            raw.close()
    db.close()
    print(f"transliteration filled for {len(updates)} words")


if __name__ == "__main__":
    main()
