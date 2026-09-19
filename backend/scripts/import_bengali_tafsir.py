#!/usr/bin/env python3
"""Bulk Bengali tafsir import for ALL 6,236 verses (real data, quran.com API v4).

Resources (both Bengali, openly served by quran.com API):
  - 165 Tafsir Ahsanul Bayaan  (work_code ahsanul-bn) — concise, ~6MB total
  - 166 Tafsir Abu Bakr Zakaria (work_code zakaria-bn) — detailed, ~11MB total

HTML markup is stripped to plain text; each row keeps work/source/methodology
labels so the UI stays transparent. Idempotent upserts; resume-safe.

Usage:
  python scripts/import_bengali_tafsir.py [--limit 5] [--works ahsanul-bn]
"""

import argparse
import html
import os
import re
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.db import SessionLocal, ensure_bengali_schema  # noqa: E402
from app.models import Tafsir, Verse  # noqa: E402
from scripts.import_quran import backoff_fetch  # noqa: E402

API = "https://api.quran.com/api/v4"

WORKS = {
    "ahsanul-bn": {
        "resource_id": 165, "slug": "bn-tafsir-ahsanul-bayaan",
        "work_name": "তাফসীর আহসানুল বায়ান",
        "source": "Tafsir Ahsanul Bayaan (Bayaan Foundation, Bengali) via quran.com API v4 — full text with attribution",
    },
    "zakaria-bn": {
        "resource_id": 166, "slug": "bn-tafsir-abu-bakr-zakaria",
        "work_name": "তাফসীর আবু বকর যাকারিয়া",
        "source": "Tafsir Abu Bakr Zakaria (King Fahd Complex Bengali tr.) via quran.com API v4 — full text with attribution",
    },
}

TAG = re.compile(r"<br\s*/?>", re.I)
ALL_TAGS = re.compile(r"<[^>]+>")


def clean(text: str) -> str:
    text = TAG.sub("\n", text)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.I)
    text = ALL_TAGS.sub("", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--works", default=",".join(WORKS),
                    help="comma-separated subset of: " + ",".join(WORKS))
    ap.add_argument("--db", default=os.environ.get("MIRAZ_DB", str(
        Path(__file__).resolve().parent.parent / "miraz.db")))
    args = ap.parse_args()
    os.environ["MIRAZ_DB"] = args.db
    ensure_bengali_schema()
    db = SessionLocal()

    verse_ids = {(v.chapter_id, v.number): v.id for v in db.query(Verse).all()}
    wanted = [w for w in args.works.split(",") if w in WORKS]
    max_ch = args.limit or 114
    total = 0
    with httpx.Client(headers={"User-Agent": "Miraz/0.2 (Bengali tafsir import)"}) as client:
        for code in wanted:
            meta = WORKS[code]
            n = 0
            for ch in range(1, max_ch + 1):
                time.sleep(0.5)
                try:
                    data = backoff_fetch(
                        client, f"{API}/tafsirs/{meta['slug']}/by_chapter/{ch}",
                        {"per_page": 300})
                except Exception as e:  # noqa: BLE001
                    print(f"  ! {code} ch{ch} FAILED: {e}", flush=True)
                    continue
                for item in data.get("tafsirs", []):
                    vk = item.get("verse_key", "")
                    if ":" not in vk:
                        continue
                    c2, num = (int(x) for x in vk.split(":"))
                    vid = verse_ids.get((c2, num))
                    if vid is None or not item.get("text"):
                        continue
                    row = db.query(Tafsir).filter(
                        Tafsir.verse_id == vid, Tafsir.work_code == code,
                        Tafsir.language == "bn").first()
                    if not row:
                        row = Tafsir(verse_id=vid, work_code=code, language="bn")
                        db.add(row)
                    row.work_name = meta["work_name"]
                    row.text = clean(item["text"])
                    row.source = meta["source"]
                    row.methodology = "classical-theological"
                    n += 1
                db.commit()
                print(f"{code} ch{ch}: {n} total", flush=True)
            print(f"{code}: {n} verses")
            total += n
    db.close()
    print(f"tafsir rows upserted: {total}")


if __name__ == "__main__":
    main()
