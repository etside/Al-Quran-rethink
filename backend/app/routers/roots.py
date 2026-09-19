from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import RootEntry, Verse, Word

router = APIRouter(prefix="/roots", tags=["roots"])


@router.get("")
def root_explorer(
    q: str = Query(default="", max_length=32),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """Root explorer: browse the Bengali root dictionary (1,651 roots in the
    full language; demo seed covers Fatiha/Baqarah-opening roots)."""
    query = db.query(RootEntry)
    if q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(
            (RootEntry.root_ar.like(like)) | (RootEntry.meaning_bn.like(like))
        )
    rows = query.order_by(RootEntry.root_ar).limit(limit).all()
    return [
        {
            "root_ar": r.root_ar,
            "meaning_bn": r.meaning_bn,
            "meaning_en": r.meaning_en,
            "pos_summary": r.pos_summary,
            "verb_forms": r.verb_forms,
            "occurrences": r.occurrences,
            "source": r.source,
            "methodology": r.methodology,
        }
        for r in rows
    ]


@router.get("/{root_ar}")
def root_detail(root_ar: str, db: Session = Depends(get_db)):
    """Occurrences of a triliteral/root across the Quran — the basis for
    semantic-range study. Word-level rows joined with verse reference,
    plus the Bengali dictionary gloss when seeded."""
    rows = (
        db.query(Word, Verse.chapter_id, Verse.number)
        .join(Verse, Verse.id == Word.verse_id)
        .filter(Word.root_ar == root_ar)
        .order_by(Verse.id)
        .limit(200)
        .all()
    )
    total = db.query(func.count(Word.id)).filter(Word.root_ar == root_ar).scalar() or 0
    entry = db.query(RootEntry).filter(RootEntry.root_ar == root_ar).first()
    return {
        "root": root_ar,
        "total_occurrences": total,
        "meaning_bn": entry.meaning_bn if entry else None,
        "meaning_en": entry.meaning_en if entry else None,
        "pos_summary": entry.pos_summary if entry else None,
        "verb_forms": entry.verb_forms if entry else None,
        "source": entry.source if entry else None,
        "methodology": entry.methodology if entry else "linguistic analysis",
        "occurrences": [
            {
                "chapter": ch,
                "verse": n,
                "word": w.text_uthmani,
                "translation_bn": getattr(w, "translation_bn", None),
                "part_of_speech": w.part_of_speech,
            }
            for w, ch, n in rows
        ],
    }
