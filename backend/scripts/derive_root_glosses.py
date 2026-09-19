#!/usr/bin/env python3
"""Derive Bengali root-dictionary entries for ALL corpus roots (1,642).

Method: majority vote — for each root, the most common Bengali word-gloss
(translation_bn from QuranWBW) among its words becomes meaning_bn, and the
most common English gloss becomes meaning_en. Hand-written seed entries keep
their dictionary glosses; only occurrences are refreshed.

Every auto entry is labeled methodology="derived-draft" with a source note
saying it is an unverified statistical summary — the UI must render that
label (transparency principle). Word.root_bn is filled for every rooted word
from its root entry (preserving hand-set values).

Usage:
  python scripts/derive_root_glosses.py [--db PATH]
"""

import argparse
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.db import SessionLocal, engine, ensure_bengali_schema  # noqa: E402
from app.models import RootEntry, Word  # noqa: E402

DERIVED_SOURCE = (
    "স্বয়ংক্রিয় সার (যাচাই প্রয়োজন): এই ধাতুর শব্দগুলোর সবচেয়ে প্রচলিত "
    "বাংলা অর্থ — উৎস: QuranWBW বাংলা শব্দার্থ + Quranic Arabic Corpus ধাতু-বিশ্লেষণ"
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.environ.get("MIRAZ_DB", str(
        Path(__file__).resolve().parent.parent / "miraz.db")))
    args = ap.parse_args()
    os.environ["MIRAZ_DB"] = args.db
    ensure_bengali_schema()
    db = SessionLocal()

    bn_votes: dict[str, Counter] = defaultdict(Counter)
    en_votes: dict[str, Counter] = defaultdict(Counter)
    counts: Counter = Counter()
    for root_ar, bn, en in db.query(Word.root_ar, Word.translation_bn,
                                    Word.translation_en).filter(Word.root_ar.isnot(None)).all():
        counts[root_ar] += 1
        if bn:
            bn_votes[root_ar][bn.strip()] += 1
        if en:
            en_votes[root_ar][en.strip()] += 1

    derived = kept = 0
    for root_ar, total in counts.items():
        row = db.query(RootEntry).filter(RootEntry.root_ar == root_ar).first()
        if row is None:
            row = RootEntry(root_ar=root_ar)
            db.add(row)
        row.occurrences = total
        if row.meaning_bn:  # hand-written dictionary gloss wins
            kept += 1
            continue
        top_bn = bn_votes[root_ar].most_common(1)
        top_en = en_votes[root_ar].most_common(1)
        row.meaning_bn = top_bn[0][0] if top_bn else "(বাংলা অর্থ এখনও নেই)"
        row.meaning_en = top_en[0][0] if top_en else None
        row.source = DERIVED_SOURCE
        row.methodology = "derived-draft"
        derived += 1
    db.commit()

    # fill Word.root_bn from dictionary (preserve hand-set values)
    meanings = {r.root_ar: r.meaning_bn for r in db.query(RootEntry).all()}
    rows = db.query(Word.id, Word.root_ar, Word.root_bn).filter(
        Word.root_ar.isnot(None), Word.root_bn.is_(None)).all()
    updates = [(meanings[r], wid) for wid, r, _ in rows if r in meanings]
    if updates:
        raw = engine.raw_connection()
        try:
            cur = raw.cursor()
            cur.executemany("UPDATE words SET root_bn=? WHERE id=?", updates)
            raw.commit()
        finally:
            raw.close()
    db.close()
    print(f"roots: {len(counts)} total, {kept} hand-written kept, {derived} derived; "
          f"word root_bn filled: {len(updates)}")


if __name__ == "__main__":
    main()
