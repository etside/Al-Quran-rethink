from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Verse, Word

router = APIRouter(prefix="/roots", tags=["roots"])


@router.get("/{root_ar}")
def root_detail(root_ar: str, db: Session = Depends(get_db)):
    """Occurrences of a triliteral/root across the Quran — the basis for
    semantic-range study. Word-level rows joined with verse reference."""
    rows = (
        db.query(Word, Verse.chapter_id, Verse.number)
        .join(Verse, Verse.id == Word.verse_id)
        .filter(Word.root_ar == root_ar)
        .order_by(Verse.id)
        .limit(200)
        .all()
    )
    total = db.query(func.count(Word.id)).filter(Word.root_ar == root_ar).scalar() or 0
    return {
        "root": root_ar,
        "total_occurrences": total,
        "occurrences": [
            {
                "chapter": ch,
                "verse": n,
                "word": w.text_uthmani,
                "part_of_speech": w.part_of_speech,
            }
            for w, ch, n in rows
        ],
    }
