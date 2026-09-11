from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Translation, Verse

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search(q: str = Query(min_length=2), lang: str = "en", limit: int = 25, db: Session = Depends(get_db)):
    """Keyword search over translations (Phase 1). Root/theme search arrives with the corpus layer."""
    q = f"%{q.strip()}%"
    rows = (
        db.query(Translation, Verse.chapter_id, Verse.number)
        .join(Verse, Verse.id == Translation.verse_id)
        .filter(Translation.text.ilike(q), Translation.language == lang)
        .limit(limit)
        .all()
    )
    return [
        {
            "chapter": ch,
            "verse": n,
            "translator_name": t.translator_name,
            "language": t.language,
            "snippet": t.text[:280],
        }
        for t, ch, n in rows
    ]
