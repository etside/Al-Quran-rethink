from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..bn_names import CHAPTER_NAMES_BN
from ..db import get_db
from ..models import Chapter

router = APIRouter(prefix="/chapters", tags=["chapters"])


def _serialize(c: Chapter) -> dict:
    return {
        "id": c.id,
        "name_ar": c.name_ar,
        "name_en": c.name_en,
        "name_bn": CHAPTER_NAMES_BN.get(c.id, c.name_en),
        "verses_count": c.verses_count,
    }


@router.get("")
def list_chapters(db: Session = Depends(get_db)):
    rows = db.query(Chapter).order_by(Chapter.id).all()
    if not rows:
        raise HTTPException(503, "No data loaded — run backend/scripts/import_quran.py")
    return [_serialize(c) for c in rows]


@router.get("/{chapter_id}")
def get_chapter(chapter_id: int, db: Session = Depends(get_db)):
    c = db.get(Chapter, chapter_id)
    if not c:
        raise HTTPException(404, "chapter not found")
    return _serialize(c)
