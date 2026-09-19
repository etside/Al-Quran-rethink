#!/usr/bin/env python3
"""Bengali word-by-word bulk importer (QuranLayers goal) — scaffold.

Fills Word.translation_bn / transliteration / lemma / root_bn from open
Bengali word-by-word datasets. Priority:

  1. local JSONL at backend/data/bn_wbw.jsonl — one object per line:
       {"chapter": 1, "verse": 1, "position": 1, "bn": "নামে",
        "transliteration": "bismi", "lemma": "اسم", "root": "س م و",
        "root_bn": "উচ্চ হওয়া; নাম", "verb_form": null, "pos": "N",
        "grammar_bn": "জার-মাজরুর"}
     (export/convert QuranWBW.com, QUL qul.tarteel.ai, or Corpus-Quran
     Bengali dumps into this shape — see README notes below)
  2. QUL API (if reachable): https://qul.tarteel.ai (best-effort)
  3. quran-cloud Bengali edition (verse-level fallback only)

Word glosses are dictionary facts; verse translations stay in the
`translations` table (Taisirul Quran via import_quran.py). Re-run safely —
rows are updated in place, keyed by (chapter, verse, position).

Usage:
  python scripts/import_bengali_wbw.py [--db PATH] [--limit 5]
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.db import SessionLocal, ensure_bengali_schema  # noqa: E402
from app.models import Verse, Word  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data" / "bn_wbw.jsonl"
QWBW_BN = Path(__file__).resolve().parent.parent / "data" / "qwbw_bn.json"
QWBW_SOURCE = "QuranWBW.com — Bengali word-by-word gloss (words-data/translations/5)"


def import_qwbw(db, limit: int) -> tuple[int, list]:
    """Import the QuranWBW Bengali WbW file for ALL verses.

    File shape: {chapter: {verse: [[gloss...], [], [marker]]}}. Gloss index i
    maps to word position i+1 (verified 6236/6236 verses align with our word
    tokenization after excluding verse-number markers). Overwrites
    translation_bn uniformly so provenance is consistent; all other columns
    (lemma, root_bn, grammar_bn, transliteration) are preserved.
    """
    import sqlite3

    raw = json.loads(QWBW_BN.read_text(encoding="utf-8"))
    AR_DIG = set("٠١٢٣٤٥٦٧٨٩")
    updates = []
    skipped = []
    for ch_s, verses in raw.items():
        ch = int(ch_s)
        if limit and ch > limit:
            continue
        for v_s, arr in verses.items():
            glosses = arr[0]
            verse = db.query(Verse).filter(
                Verse.chapter_id == ch, Verse.number == int(v_s)).first()
            if not verse:
                skipped.append((ch, v_s, "no-verse"))
                continue
            words = db.query(Word).filter(Word.verse_id == verse.id).order_by(Word.position).all()
            real = [w for w in words
                    if not (w.text_uthmani.strip() and
                            all(c in AR_DIG for c in w.text_uthmani.strip()))]
            if len(real) != len(glosses):
                skipped.append((ch, v_s, f"tok-{len(real)}-vs-{len(glosses)}"))
                continue
            for w, g in zip(real, glosses):
                updates.append((g, w.id))
    if updates:
        con = sqlite3.connect(db.get_bind().url.database)
        try:
            con.executemany("UPDATE words SET translation_bn=? WHERE id=?", updates)
            con.commit()
        finally:
            con.close()
    return len(updates), skipped


def import_jsonl(db, limit: int) -> int:
    if not DATA.exists():
        return -1
    n = 0
    with open(DATA, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            if limit and o.get("chapter", 0) > limit:
                continue
            verse = db.query(Verse).filter(
                Verse.chapter_id == o["chapter"], Verse.number == o["verse"]).first()
            if not verse:
                continue
            w = db.query(Word).filter(
                Word.verse_id == verse.id, Word.position == o["position"]).first()
            if not w:
                continue
            if o.get("bn"):
                w.translation_bn = o["bn"]
            for src, dst in (("transliteration", "transliteration"), ("lemma", "lemma"),
                             ("root", "root_ar"), ("root_bn", "root_bn"),
                             ("verb_form", "verb_form"), ("pos", "part_of_speech"),
                             ("grammar_bn", "grammar_bn")):
                if o.get(src) is not None:
                    setattr(w, dst, o[src])
            n += 1
    db.commit()
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.environ.get("MIRAZ_DB", str(
        Path(__file__).resolve().parent.parent / "miraz.db")))
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    os.environ["MIRAZ_DB"] = args.db
    ensure_bengali_schema()
    db = SessionLocal()
    total = 0
    if QWBW_BN.exists():
        n, skipped = import_qwbw(db, args.limit)
        total += n
        print(f"qwbw Bengali glosses: {n} words; skipped verses: {len(skipped)}")
        for s in skipped[:10]:
            print("  skip", s)
    n = import_jsonl(db, args.limit)
    db.close()
    if n == -1 and not QWBW_BN.exists():
        print(f"no bulk file at {DATA.name} — convert a Bengali WbW dump to JSONL first "
              f"(sources: QuranWBW.com, QUL qul.tarteel.ai, Corpus Quran bn). "
              f"Demo seed: python scripts/seed_bengali.py")
    else:
        if n > 0:
            print(f"jsonl overrides: {n} words")
        print(f"imported Bengali glosses for {total + max(n, 0)} words")


if __name__ == "__main__":
    main()
