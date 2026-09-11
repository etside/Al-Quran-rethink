from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..db import get_db
from ..models import Chapter, Verse

router = APIRouter(prefix="/verses", tags=["verses"])


def _serialize(v: Verse) -> dict:
    by_lang: dict[str, list[dict]] = {}
    for t in v.translations:
        by_lang.setdefault(t.language, []).append(
            {"translator_code": t.translator_code, "translator_name": t.translator_name, "text": t.text}
        )
    return {
        "id": v.id,
        "chapter_id": v.chapter_id,
        "number": v.number,
        "text_uthmani": v.text_uthmani,
        "translations": by_lang,
    }


@router.get("/{chapter_id}")
def chapter_verses(chapter_id: int, db: Session = Depends(get_db)):
    if not db.get(Chapter, chapter_id):
        raise HTTPException(404, "chapter not found")
    rows = (
        db.query(Verse)
        .options(joinedload(Verse.translations))
        .filter(Verse.chapter_id == chapter_id)
        .order_by(Verse.number)
        .all()
    )
    return [_serialize(v) for v in rows]


@router.get("/{chapter_id}/{number}")
def single_verse(chapter_id: int, number: int, db: Session = Depends(get_db)):
    v = (
        db.query(Verse)
        .options(joinedload(Verse.translations))
        .filter(Verse.chapter_id == chapter_id, Verse.number == number)
        .first()
    )
    if not v:
        raise HTTPException(404, "verse not found")
    return _serialize(v)
