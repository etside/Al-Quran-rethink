from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Verse, Word

router = APIRouter(tags=["words"])


@router.get("/verses/{chapter_id}/{number}/words")
def verse_words(chapter_id: int, number: int, db: Session = Depends(get_db)):
    """Word-by-word breakdown with root + morphology when corpus data is loaded."""
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
            "root_ar": w.root_ar,
            "part_of_speech": w.part_of_speech,
            "has_root_data": w.root_ar is not None,
        }
        for w in words
    ]
