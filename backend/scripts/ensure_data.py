#!/usr/bin/env python3
"""Boot-time data check for the single-webapp image (fail-soft, idempotent).

Inspects the SQLite database and runs only the importers whose data is
missing, so a baked-in database boots instantly while a fresh volume gets
fully populated (network required for the fetch steps). Every step logs and
continues on failure — the app always boots.

Order matters: base text -> morphology -> transliteration -> Bengali WbW ->
tafsir -> derived layers -> context. Hand seed runs last as a backfill.

Usage:
  python scripts/ensure_data.py [--db PATH]
"""

import argparse
import os
import sys
import traceback
from pathlib import Path

# Parse args BEFORE importing app modules (app.db reads $MIRAZ_DB at import).
_ap = argparse.ArgumentParser()
_ap.add_argument("--db", default=os.environ.get("MIRAZ_DB", str(
    Path(__file__).resolve().parent.parent / "miraz.db")))
_args, _ = _ap.parse_known_args()
os.environ["MIRAZ_DB"] = _args.db

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.db import SessionLocal, ensure_bengali_schema  # noqa: E402


def step(name: str, fn) -> None:
    try:
        fn()
        print(f"[ensure_data] {name}: ok", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"[ensure_data] {name}: SKIPPED ({e})", flush=True)
        traceback.print_exc(limit=3)


def main() -> None:
    ensure_bengali_schema()
    db = SessionLocal()
    try:
        from app.models import ContextNote, RootEntry, Tafsir, Translation, Verse, Word
        n_verses = db.query(Verse).count()
        n_words = db.query(Word).count()
        n_pos = db.query(Word).filter(Word.part_of_speech.isnot(None)).count()
        n_tr = db.query(Word).filter(Word.transliteration.isnot(None)).count()
        n_bn = db.query(Word).filter(Word.translation_bn.isnot(None)).count()
        n_tafsir = db.query(Tafsir).count()
        n_roots = db.query(RootEntry).count()
        n_ctx = db.query(ContextNote).count()
        n_trans = db.query(Translation).count()
    finally:
        db.close()
    print(f"[ensure_data] verses={n_verses} words={n_words} pos={n_pos} "
          f"translit={n_tr} bn={n_bn} tafsir={n_tafsir} roots={n_roots} "
          f"context={n_ctx} translations={n_trans}", flush=True)

    if n_verses == 0 or n_trans == 0:
        def _base():
            from scripts.import_quran import main as imp
            sys.argv = ["import_quran.py"]
            imp()
        step("base quran import", _base)

    if n_words and n_pos < n_words * 0.9:
        def _morph():
            from scripts.import_morphology import DATA, import_morphology, load_corpus
            from scripts.import_morphology import ensure_corpus_file
            from app.db import SessionLocal as S
            ensure_corpus_file()
            if not DATA.exists():
                raise RuntimeError("corpus morphology file unavailable")
            s = S()
            try:
                print(import_morphology(s, load_corpus(DATA)), flush=True)
            finally:
                s.close()
        step("morphology", _morph)

    if n_words and n_tr < n_words * 0.9:
        def _tr():
            from scripts.import_transliteration import main as imp
            sys.argv = ["import_transliteration.py"]
            imp()
        step("transliteration", _tr)

    if n_words and n_bn < n_words * 0.9:
        def _wbw():
            from scripts.import_bengali_wbw import QWBW_BN, import_qwbw
            from app.db import SessionLocal as S
            if not QWBW_BN.exists():
                raise RuntimeError("qwbw_bn.json not bundled; run seed_bengali.py for the core sample")
            s = S()
            try:
                n, skipped = import_qwbw(s, 0)
                print(f"qwbw: {n} words, skipped={len(skipped)}", flush=True)
            finally:
                s.close()
        step("bengali word glosses", _wbw)

    if n_tafsir < 6000:
        def _tafsir():
            from scripts.import_bengali_tafsir import main as imp
            sys.argv = ["import_bengali_tafsir.py"]
            imp()
        step("bengali tafsir", _tafsir)

    if n_roots == 0:
        def _roots():
            from scripts.derive_root_glosses import main as imp
            sys.argv = ["derive_root_glosses.py"]
            imp()
        step("root glosses", _roots)

    if n_ctx == 0:
        def _ctx():
            from scripts.seed_chapter_context import main as imp
            sys.argv = ["seed_chapter_context.py"]
            imp()
        step("chapter context", _ctx)

    def _seed():
        from scripts.seed_bengali import main as imp
        sys.argv = ["seed_bengali.py"]
        imp()
    step("hand-seed backfill", _seed)
    print("[ensure_data] done", flush=True)


if __name__ == "__main__":
    main()
