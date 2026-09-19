#!/usr/bin/env python3
"""Miraz data importer (Phase 1).

Fetches from the open quran.com API v4:
  - all 114 chapters (Arabic + English names)
  - Uthmani script text for every verse
  - English translation (Sahih International, resource 131)
  - Bengali translation (auto-selected from /resources/translations?language=bn,
    preferring "Taisirul Quran")
  - word-by-word breakdown per chapter (Arabic word + English gloss)
  - best-effort Quranic Arabic Corpus morphology (word roots) from open mirrors

Every step fails soft: if a source is unreachable the importer logs it and
continues, so the platform still boots. Re-run safely — rows are upserted.

Usage:
  python scripts/import_quran.py [--limit 3] [--skip-words] [--skip-morphology]
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.db import Base, engine, SessionLocal  # noqa: E402
from app.models import Chapter, Translation, Verse, Word  # noqa: E402

API = "https://api.quran.com/api/v4"
EN_TRANSLATION_ID = 20  # Saheeh International
BN_FALLBACK_NOTE = "Bengali resource ids: 161 Taisirul Quran, 163 Sheikh Mujibur Rahman, 162 Rawai Al-bayan"


def backoff_fetch(client: httpx.Client, url: str, params: dict, min_items: int = 1, attempts: int = 4):
    """quran.com rate-limits with HTTP 200 + empty payloads. Detect that and
    back off exponentially until items appear or attempts run out."""
    for i in range(attempts):
        data = fetch(client, url, params)
        key = next((k for k in ("verses", "translations", "chapters") if k in data), None)
        if key is None or len(data.get(key, [])) >= min_items or i == attempts - 1:
            return data
        wait = 2**i + 1
        print(f"  rate-limited? empty {key}; retrying in {wait}s …", flush=True)
        time.sleep(wait)
    return data

FOOTNOTE = re.compile(r"<sup.*?</sup>", re.DOTALL)


def fetch(client: httpx.Client, url: str, params: dict | None = None) -> dict:
    r = client.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def pick_bengali(client: httpx.Client) -> tuple[int, str]:
    """Choose a Bengali translation resource: prefer Taisirul Quran, else first."""
    data = fetch(client, f"{API}/resources/translations", params={"language": "bn"})
    options = data.get("translations", [])
    if not options:
        raise RuntimeError("no Bengali translations listed by quran.com")
    chosen = next((t for t in options if "taisirul" in t["name"].lower()), options[0])
    return chosen["id"], chosen["name"]


def paged(client: httpx.Client, url: str, params: dict, key: str):
    """Yield items across paginated v4 endpoints (stops after 1 page if unpaginated).
    Uses backoff_fetch to survive rate limiting."""
    page = 1
    while True:
        data = backoff_fetch(client, url, {**params, "page": page})
        yield from data.get(key, [])
        meta = data.get("pagination") or data.get("meta") or {}
        total = meta.get("total_pages", 1)
        if page >= total:
            break
        page += 1


def clean(text: str) -> str:
    return FOOTNOTE.sub("", text).strip()


def import_words(client: httpx.Client, db, chapter_id: int) -> int:
    n = 0
    for v in paged(
        client,
        f"{API}/verses/by_chapter/{chapter_id}",
        {"words": "true", "per_page": 50, "word_fields": "text_uthmani,translation", "fields": "text_uthmani"},
        "verses",
    ):
        vk = v["verse_key"]
        _, vnum = (int(x) for x in vk.split(":"))
        verse = db.query(Verse).filter(Verse.chapter_id == chapter_id, Verse.number == vnum).first()
        if not verse:
            continue
        db.query(Word).filter(Word.verse_id == verse.id).delete()
        for w in v.get("words", []):
            trans = (w.get("translation") or {}).get("text")
            db.add(
                Word(
                    verse_id=verse.id,
                    position=w["position"],
                    text_uthmani=w.get("text_uthmani") or "",
                    translation_en=trans,
                )
            )
            n += 1
    db.commit()
    return n


def try_morphology(client: httpx.Client, db) -> str:
    """Load Quranic Arabic Corpus morphology (word roots + POS) via
    scripts/import_morphology.py (Buckwalter-decoded, bulk, fill-nulls)."""
    try:
        from scripts.import_morphology import DATA, import_morphology, load_corpus
    except ImportError:  # pragma: no cover - direct-path fallback
        from import_morphology import DATA, import_morphology, load_corpus  # type: ignore
    if not DATA.exists():
        return (
            "skipped — morphology file not present at backend/data/corpus_morphology.txt; "
            "download Quranic-corpus-morphology-0.4.txt there (see scripts/import_morphology.py)"
        )
    report = import_morphology(db, load_corpus(DATA))
    return f"loaded {report['words_updated']} words ({report['distinct_roots']} roots) from {DATA.name}"


def parse_morphology(raw: str, db) -> int:
    """Legacy entry point (kept for API compat): parse raw corpus text."""
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(raw)
        tmp = Path(f.name)
    try:
        try:
            from scripts.import_morphology import import_morphology, load_corpus
        except ImportError:
            from import_morphology import import_morphology, load_corpus  # type: ignore
        return import_morphology(db, load_corpus(tmp))["words_updated"]
    finally:
        tmp.unlink(missing_ok=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=0, help="import only first N chapters (0 = all)")
    ap.add_argument("--skip-words", action="store_true")
    ap.add_argument("--skip-morphology", action="store_true")
    args = ap.parse_args()

    Base.metadata.create_all(engine)
    db = SessionLocal()
    report: dict[str, str] = {}

    with httpx.Client(
        headers={"User-Agent": "Miraz/0.1 (open Quran research; +github.com/etside/Al-Quran-rethink)"}
    ) as client:
        # 1. chapters
        try:
            chapters = fetch(client, f"{API}/chapters", {"language": "en"})["chapters"]
            for c in chapters:
                row = db.get(Chapter, c["id"])
                if not row:
                    row = Chapter(id=c["id"])
                    db.add(row)
                row.name_ar, row.name_en, row.verses_count = c["name_arabic"], c["name_simple"], c["verses_count"]
            db.commit()
            report["chapters"] = f"{len(chapters)}"
        except Exception as e:  # noqa: BLE001
            db.rollback()
            report["chapters"] = f"FAILED: {e}"

        # 2. Uthmani text
        try:
            verses = fetch(client, f"{API}/quran/verses/uthmani")["verses"]
            max_ch = args.limit or 114
            for v in verses:
                ch, num = (int(x) for x in v["verse_key"].split(":"))
                if ch > max_ch:
                    continue
                row = db.get(Verse, v["id"])
                if not row:
                    row = Verse(id=v["id"])
                    db.add(row)
                row.chapter_id, row.number, row.text_uthmani = ch, num, v["text_uthmani"]
            db.commit()
            report["verses"] = f"{sum(1 for v in verses if int(v['verse_key'].split(':')[0]) <= max_ch)}"
        except Exception as e:  # noqa: BLE001
            db.rollback()
            report["verses"] = f"FAILED: {e}"

        # 3. translations (English + Bengali) via per-chapter verses endpoint,
        #    which embeds verse keys reliably
        try:
            en_name, bn_id, bn_name = "Saheeh International", *pick_bengali(client)
            max_ch = args.limit or 114
            n_en = n_bn = 0
            for ch in range(1, max_ch + 1):
                time.sleep(0.5)  # stay under the rate limit
                for v in paged(
                    client,
                    f"{API}/verses/by_chapter/{ch}",
                    {"fields": "text_uthmani", "per_page": 50, "translations": f"{EN_TRANSLATION_ID},{bn_id}"},
                    "verses",
                ):
                    _, num = (int(x) for x in v["verse_key"].split(":"))
                    verse = db.query(Verse).filter(Verse.chapter_id == ch, Verse.number == num).first()
                    if not verse:
                        continue
                    for t in v.get("translations", []):
                        rid = t["resource_id"]
                        is_bn = rid == bn_id
                        row = (
                            db.query(Translation)
                            .filter(Translation.verse_id == verse.id, Translation.translator_code == str(rid))
                            .first()
                        )
                        if not row:
                            row = Translation(verse_id=verse.id, translator_code=str(rid))
                            db.add(row)
                        row.language = "bn" if is_bn else "en"
                        row.translator_name = bn_name if is_bn else en_name
                        row.text = clean(t["text"])
                        if is_bn:
                            n_bn += 1
                        else:
                            n_en += 1
            db.commit()
            report["translation_en"] = f"{n_en} ({en_name})"
            report["translation_bn"] = f"{n_bn} ({bn_name}, resource {bn_id})"
        except Exception as e:  # noqa: BLE001
            db.rollback()
            report["translation_en"] = report["translation_bn"] = f"FAILED: {e}"

        # 4. words
        if args.skip_words:
            report["words"] = "skipped (--skip-words)"
        else:
            try:
                max_ch = args.limit or 114
                total = 0
                for cid in range(1, max_ch + 1):
                    time.sleep(0.5)  # stay under the rate limit
                    total += import_words(client, db, cid)
                report["words"] = f"{total}"
            except Exception as e:  # noqa: BLE001
                db.rollback()
                report["words"] = f"FAILED: {e}"

        # 5. morphology roots
        if args.skip_morphology:
            report["morphology_roots"] = "skipped (--skip-morphology)"
        else:
            try:
                report["morphology_roots"] = try_morphology(client, db)
            except Exception as e:  # noqa: BLE001
                db.rollback()
                report["morphology_roots"] = f"FAILED: {e}"

    db.close()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
