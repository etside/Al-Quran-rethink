"""Context of revelation in Bengali: asbab, historical background,
early-Arabic semantic notes. Verse-level notes plus chapter-level fallback
so EVERY verse has context coverage."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ContextNote, Verse

router = APIRouter(prefix="/context", tags=["context"])

KIND_LABELS = {
    "asbab": "শানে নুযূল (অবতরণের প্রেক্ষাপট)",
    "historical": "ঐতিহাসিক প্রেক্ষাপট",
    "linguistic": "আদি আরবি অর্থ (অবতরণকালীন প্রয়োগ)",
}


def _serialize(r: ContextNote) -> dict:
    return {
        "kind": r.kind,
        "kind_label": KIND_LABELS.get(r.kind, r.kind),
        "scope": r.scope or ("chapter" if r.chapter_id else "verse"),
        "text_bn": r.text_bn,
        "text_en": r.text_en,
        "source": r.source,
        "methodology": "classical-theological",
    }


def verse_context_rows(db: Session, chapter_id: int, number: int) -> list[dict]:
    v = db.query(Verse).filter(Verse.chapter_id == chapter_id, Verse.number == number).first()
    if not v:
        return []
    rows = db.query(ContextNote).filter(ContextNote.verse_id == v.id).order_by(ContextNote.kind).all()
    out = [_serialize(r) for r in rows]
    kinds = {r.kind for r in rows}
    chap = db.query(ContextNote).filter(
        ContextNote.scope == "chapter", ContextNote.chapter_id == chapter_id
    ).order_by(ContextNote.kind).all()
    out.extend(_serialize(r) for r in chap if r.kind not in kinds)
    return out


@router.get("/{chapter_id}/{number}")
def verse_context(chapter_id: int, number: int, db: Session = Depends(get_db)):
    return verse_context_rows(db, chapter_id, number)
