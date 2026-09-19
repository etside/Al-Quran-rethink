"""Combined Bengali verse bundle — one call for the reading view.

GET /api/bn/verse/{chapter}/{number} returns:
  verse (uthmani + en/bn translations), words (bn gloss + transliteration
  + root + root_bn + grammar_bn), tafsir (bn summaries), context (bn notes).

Also GET /api/bn/status — coverage counters so the UI can be honest about
which verses have full Bengali layers (demo seed vs. full corpus).
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..db import get_db
from ..models import ContextNote, RootEntry, Tafsir, Verse, Word

router = APIRouter(prefix="/bn", tags=["bengali"])


@router.get("/status")
def bn_status(db: Session = Depends(get_db)):
    try:
        bn_words = db.query(func.count(Word.id)).filter(Word.translation_bn.isnot(None)).scalar() or 0
    except Exception:
        bn_words = 0
    try:
        n_roots = db.query(func.count(RootEntry.id)).scalar() or 0
        n_tafsir = db.query(func.count(Tafsir.id)).scalar() or 0
        n_context = db.query(func.count(ContextNote.id)).scalar() or 0
    except Exception:
        n_roots = n_tafsir = n_context = 0
    return {
        "words_bn": bn_words,
        "roots_bn": n_roots,
        "tafsir_entries": n_tafsir,
        "context_notes": n_context,
        "seed_scope": "সম্পূর্ণ বাংলা স্তর: ৬,২৩৬ আয়াতের সব শব্দে বাংলা অর্থ + উচ্চারণ; "
                      "সব ধাতুর বাংলা অর্থ; ১১৪ সূরার প্রেক্ষাপট; সম্পূর্ণ বাংলা তাফসীর",
        "methodology": "linguistic analysis + classical-theological (full texts with attribution)",
    }


@router.get("/verse/{chapter_id}/{number}")
def bn_verse(chapter_id: int, number: int, db: Session = Depends(get_db)):
    v = (
        db.query(Verse)
        .options(joinedload(Verse.translations))
        .filter(Verse.chapter_id == chapter_id, Verse.number == number)
        .first()
    )
    if not v:
        from fastapi import HTTPException
        raise HTTPException(404, "verse not found")
    by_lang: dict[str, list[dict]] = {}
    for t in v.translations:
        by_lang.setdefault(t.language, []).append(
            {"translator_code": t.translator_code, "translator_name": t.translator_name, "text": t.text}
        )
    words = db.query(Word).filter(Word.verse_id == v.id).order_by(Word.position).all()
    tafsir = db.query(Tafsir).filter(Tafsir.verse_id == v.id).order_by(Tafsir.work_code).all()
    from .context import verse_context_rows
    context = verse_context_rows(db, chapter_id, number)
    return {
        "id": v.id, "chapter_id": v.chapter_id, "number": v.number,
        "text_uthmani": v.text_uthmani, "translations": by_lang,
        "words": [
            {"position": w.position, "text_uthmani": w.text_uthmani,
             "translation_en": w.translation_en, "translation_bn": getattr(w, "translation_bn", None),
             "transliteration": getattr(w, "transliteration", None), "lemma": getattr(w, "lemma", None),
             "root_ar": w.root_ar, "root_bn": getattr(w, "root_bn", None),
             "verb_form": getattr(w, "verb_form", None), "grammar_bn": getattr(w, "grammar_bn", None),
             "part_of_speech": w.part_of_speech,
             "has_root_data": w.root_ar is not None, "has_bn_data": bool(getattr(w, "translation_bn", None))}
            for w in words
        ],
        "tafsir": [
            {"work_code": t.work_code, "work_name": t.work_name, "language": t.language,
             "text": t.text, "source": t.source, "methodology": t.methodology}
            for t in tafsir
        ],
        "context": [
            {"kind": c["kind"], "kind_label": c.get("kind_label"), "scope": c.get("scope", "verse"),
             "text_bn": c["text_bn"], "text_en": c["text_en"], "source": c["source"]}
            for c in context
        ],
        "coverage": {
            "has_bn_words": any(getattr(w, "translation_bn", None) for w in words),
            "has_tafsir": len(tafsir) > 0,
            "has_context": len(context) > 0,
        },
    }
