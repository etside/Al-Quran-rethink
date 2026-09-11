from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Chapter

router = APIRouter(prefix="/chapters", tags=["chapters"])


@router.get("")
def list_chapters(db: Session = Depends(get_db)):
    rows = db.query(Chapter).order_by(Chapter.id).all()
    if not rows:
        raise HTTPException(503, "No data loaded — run backend/scripts/import_quran.py")
    return [
        {"id": c.id, "name_ar": c.name_ar, "name_en": c.name_en, "verses_count": c.verses_count}
        for c in rows
    ]


@router.get("/{chapter_id}")
def get_chapter(chapter_id: int, db: Session = Depends(get_db)):
    c = db.get(Chapter, chapter_id)
    if not c:
        raise HTTPException(404, "chapter not found")
    return {"id": c.id, "name_ar": c.name_ar, "name_en": c.name_en, "verses_count": c.verses_count}
