#!/usr/bin/env python3
"""Bulk morphology import from Quranic Arabic Corpus 0.4 (real data).

Fills Word.root_ar / part_of_speech / lemma / verb_form for EVERY word from
`backend/data/corpus_morphology.txt` (verbatim QAC 0.4 file, GPL — see file
header; attribution + link kept per its terms of use).

Corpus notes handled here:
  - lines are per *segment*: `(chapter:verse:word:segment)` tab-separated;
    the STEM segment carries POS/ROOT/LEM; prefixes/suffixes are skipped
  - file is Buckwalter-transliterated; roots/lemmas are decoded to Arabic
    (roots stored spaced, e.g. "س م و", matching the Bengali seed format)
  - verb form is read from `(II)..(X)` markers; PASS adds "(passive)"
  - only NULL columns are filled, so hand-verified seed rows are preserved

Usage:
  python scripts/import_morphology.py [--db PATH]

Called automatically by scripts/import_quran.py when the data file exists.
"""

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.db import SessionLocal, engine, ensure_bengali_schema  # noqa: E402
from app.models import Verse, Word  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data" / "corpus_morphology.txt"

# Mirrors for the verbatim QAC 0.4 file (GPL; header kept on download).
CORPUS_MIRRORS = [
    "https://gitlab.com/cobhuni/quranic_verse_recogniser/-/raw/master/quranic-corpus-morphology-0.4.txt",
    "http://variatim.altervista.org/VARCAR/quranic-corpus-morphology-0.4.txt",
]


def ensure_corpus_file() -> bool:
    """Download the verbatim corpus file if not bundled. Returns True when
    DATA exists afterwards."""
    if DATA.exists():
        return True
    import httpx
    for url in CORPUS_MIRRORS:
        try:
            with httpx.stream("GET", url, timeout=180,
                              headers={"User-Agent": "Miraz/0.3"}) as r:
                if r.status_code != 200:
                    continue
                DATA.parent.mkdir(parents=True, exist_ok=True)
                with open(DATA, "wb") as f:
                    for chunk in r.iter_bytes(65536):
                        f.write(chunk)
            if DATA.stat().st_size > 1_000_000:
                return True
        except Exception:  # noqa: BLE001
            continue
    return DATA.exists()

# Buckwalter -> Arabic (QAC 0.4 flavour: `{` = alif-wasla U+0671)
BW = {
    "'": "ء", "|": "آ", ">": "أ", "&": "ؤ", "<": "إ", "}": "ئ",
    "A": "ا", "{": "ٱ", "b": "ب", "p": "ة", "t": "ت", "v": "ث",
    "j": "ج", "H": "ح", "x": "خ", "d": "د", "*": "ذ", "r": "ر",
    "z": "ز", "s": "س", "$": "ش", "S": "ص", "D": "ض", "T": "ط",
    "Z": "ظ", "E": "ع", "g": "غ", "f": "ف", "q": "ق", "k": "ك",
    "l": "ل", "m": "م", "n": "ن", "h": "ه", "w": "و", "Y": "ى",
    "y": "ي", "F": "ً", "N": "ٌ", "K": "ٍ", "a": "َ", "u": "ُ",
    "i": "ِ", "~": "ّ", "o": "ْ", "`": "ٰ",
}
# QAC lemma disambiguation marks (not phonemes) — dropped
LEMMA_DROP = set("^[]#_2@.")

LOC = re.compile(r"\((\d+):(\d+):(\d+):(\d+)\)")
ROOT_RE = re.compile(r"ROOT:([^|\s]+)")
LEM_RE = re.compile(r"LEM:([^|\s]+)")
FORM_RE = re.compile(r"\(([IVX]+)\)")


def bw_to_ar(s: str, *, drop_unknown: bool = True) -> str:
    out = []
    for ch in s:
        if ch in BW:
            out.append(BW[ch])
        elif ch in LEMMA_DROP or ch in (" ",):
            continue
        elif not drop_unknown:
            out.append(ch)
    return "".join(out)


def load_corpus(path: Path) -> dict[tuple[int, int, int], dict]:
    """(chapter, verse, word) -> {pos, root_bw, lemma_bw, form} from STEM segments."""
    words: dict[tuple[int, int, int], dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("("):
            continue
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        m = LOC.match(parts[0])
        if not m:
            continue
        c, v, w = int(m.group(1)), int(m.group(2)), int(m.group(3))
        tag, feats = parts[2], parts[3]
        if not feats.startswith("STEM|"):
            continue
        key = (c, v, w)
        if key in words:  # keep first STEM per word
            continue
        entry: dict = {"pos": tag or None}
        rm = ROOT_RE.search(feats)
        if rm:
            entry["root_bw"] = rm.group(1)
        lm = LEM_RE.search(feats)
        if lm:
            entry["lemma_bw"] = lm.group(1)
        fm = FORM_RE.search(feats)
        if fm:
            entry["form"] = fm.group(1)
        if "|PASS|" in feats or ":PASS|" in feats or "PASS|" in feats:
            entry["passive"] = True
        words[key] = entry
    return words


def import_morphology(db, corpus: dict[tuple[int, int, int], dict]) -> dict:
    verse_ids = {(v.chapter_id, v.number): v.id for v in db.query(Verse).all()}
    # (verse_id, position) -> word row state
    rows = db.query(Word.id, Word.verse_id, Word.position,
                    Word.root_ar, Word.part_of_speech, Word.lemma, Word.verb_form).all()
    by_key = {(vid, pos): (wid, r, p, l, f) for wid, vid, pos, r, p, l, f in rows}

    updates = []
    covered_roots = set()
    for (c, v, w), e in corpus.items():
        vid = verse_ids.get((c, v))
        if vid is None:
            continue
        hit = by_key.get((vid, w))
        if hit is None:
            continue
        wid, r, p, l, f = hit
        new_root = new_pos = new_lemma = new_form = None
        if e.get("root_bw"):
            ar = " ".join(bw_to_ar(ch) for ch in e["root_bw"])
            covered_roots.add(ar)
            if r is None:
                new_root = ar
        if p is None and e.get("pos"):
            new_pos = e["pos"]
        if l is None and e.get("lemma_bw"):
            new_lemma = bw_to_ar(e["lemma_bw"])
        if f is None and e.get("form"):
            new_form = e["form"] + (" (passive)" if e.get("passive") else "")
        elif f is None and e.get("passive"):
            new_form = "I (passive)"
        if new_root is not None or new_pos is not None or new_lemma is not None or new_form is not None:
            updates.append((new_root or r, new_pos or p, new_lemma or l, new_form or f, wid))

    if updates:
        raw = engine.raw_connection()
        try:
            cur = raw.cursor()
            cur.executemany(
                "UPDATE words SET root_ar=?, part_of_speech=?, lemma=?, verb_form=? WHERE id=?",
                updates)
            raw.commit()
        finally:
            raw.close()
    return {"words_updated": len(updates), "corpus_words": len(corpus),
            "distinct_roots": len(covered_roots)}


def main() -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.environ.get("MIRAZ_DB", str(
        Path(__file__).resolve().parent.parent / "miraz.db")))
    args = ap.parse_args()
    os.environ["MIRAZ_DB"] = args.db
    ensure_bengali_schema()
    ensure_corpus_file()
    if not DATA.exists():
        print(f"missing {DATA} — download Quranic-corpus-morphology-0.4.txt there "
              f"(tried bundled mirrors; offline?)")
        return {}
    corpus = load_corpus(DATA)
    db = SessionLocal()
    try:
        report = import_morphology(db, corpus)
    finally:
        db.close()
    print(report)
    return report


if __name__ == "__main__":
    main()
