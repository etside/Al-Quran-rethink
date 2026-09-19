from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Verse, Word

router = APIRouter(tags=["words"])


@router.get("/verses/{chapter_id}/{number}/words")
def verse_words(chapter_id: int, number: int, db: Session = Depends(get_db)):
    """Word-by-word breakdown: Arabic + English gloss + Bengali gloss,
    transliteration, root (ar + bn meaning), morphology when loaded."""
    v = db.query(Verse).filter(Verse.chapter_id == chapter_id, Verse.number == number).first()
    if not v:
        return []
    words = (
        db.query(Word)
        .filter(Word.verse_id == v.id)
        .order_by(Word.position)
        .all()
    )
    return [
        {
            "position": w.position,
            "text_uthmani": w.text_uthmani,
            "translation_en": w.translation_en,
            "translation_bn": getattr(w, "translation_bn", None),
            "transliteration": getattr(w, "transliteration", None),
            "lemma": getattr(w, "lemma", None),
            "root_ar": w.root_ar,
            "root_bn": getattr(w, "root_bn", None),
            "verb_form": getattr(w, "verb_form", None),
            "grammar_bn": getattr(w, "grammar_bn", None),
            "part_of_speech": w.part_of_speech,
            "has_root_data": w.root_ar is not None,
            "has_bn_data": bool(getattr(w, "translation_bn", None)),
        }
        for w in words
    ]
