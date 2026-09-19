"""Bengali root dictionary API (alias over the root_dictionary table).

GET /api/dictionary/roots?q=...     — search/browse
GET /api/dictionary/roots/{root}    — single entry + corpus occurrence count
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import RootEntry, Word

router = APIRouter(prefix="/dictionary", tags=["dictionary"])


@router.get("/roots")
def list_roots(q: str = Query(default="", max_length=64), limit: int = Query(default=50, le=200),
               db: Session = Depends(get_db)):
    query = db.query(RootEntry)
    if q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(RootEntry.root_ar.like(like) | RootEntry.meaning_bn.like(like))
    rows = query.order_by(RootEntry.root_ar).limit(limit).all()
    return [
        {"root_ar": r.root_ar, "meaning_bn": r.meaning_bn, "meaning_en": r.meaning_en,
         "pos_summary": r.pos_summary, "verb_forms": r.verb_forms,
         "occurrences": r.occurrences, "source": r.source, "methodology": r.methodology}
        for r in rows
    ]


@router.get("/roots/{root_ar}")
def get_root(root_ar: str, db: Session = Depends(get_db)):
    r = db.query(RootEntry).filter(RootEntry.root_ar == root_ar).first()
    if not r:
        raise HTTPException(404, f"root not in Bengali dictionary seed: {root_ar}")
    live = db.query(func.count(Word.id)).filter(Word.root_ar == root_ar).scalar() or 0
    return {
        "root_ar": r.root_ar, "meaning_bn": r.meaning_bn, "meaning_en": r.meaning_en,
        "pos_summary": r.pos_summary, "verb_forms": r.verb_forms,
        "occurrences": max(r.occurrences, live), "source": r.source, "methodology": r.methodology,
    }
