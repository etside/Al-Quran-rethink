from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ContextNote, RootEntry, Tafsir, Translation, Verse, Word

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search(q: str = Query(min_length=2), lang: str = "en", limit: int = 25, db: Session = Depends(get_db)):
    """Keyword search over translations (en/bn). Bengali search matches
    Bengali translations, Bengali word glosses, root-dictionary Bengali
    meanings, and Bengali tafsir/context summaries."""
    needle = q.strip()
    like = f"%{needle}%"
    out: list[dict] = []
    seen: set[tuple[int, int, str]] = set()

    def push(ch: int, n: int, label: str, language: str, snippet: str):
        key = (ch, n, label)
        if key in seen:
            return
        seen.add(key)
        out.append(
            {"chapter": ch, "verse": n, "translator_name": label, "language": language, "snippet": snippet[:280]}
        )

    # 1. translations in requested language (fallback: both en+bn)
    langs = [lang] if lang in ("en", "bn") else ["en", "bn"]
    if lang not in ("en", "bn"):
        langs = ["en", "bn"]
    rows = (
        db.query(Translation, Verse.chapter_id, Verse.number)
        .join(Verse, Verse.id == Translation.verse_id)
        .filter(Translation.text.ilike(like), Translation.language.in_(langs))
        .limit(limit)
        .all()
    )
    for t, ch, n in rows:
        push(ch, n, t.translator_name, t.language, t.text)
        if len(out) >= limit:
            return out[:limit]

    # 2. Bengali word glosses
    try:
        wrows = (
            db.query(Word, Verse.chapter_id, Verse.number)
            .join(Verse, Verse.id == Word.verse_id)
            .filter(Word.translation_bn.ilike(like))
            .limit(limit)
            .all()
        )
        for w, ch, n in wrows:
            push(ch, n, f"শব্দ: {w.text_uthmani} — {w.translation_bn}", "bn", f"{w.text_uthmani} = {w.translation_bn}")
            if len(out) >= limit:
                return out[:limit]
    except Exception:
        pass

    # 3. Bengali tafsir summaries
    try:
        trows = (
            db.query(Tafsir, Verse.chapter_id, Verse.number)
            .join(Verse, Verse.id == Tafsir.verse_id)
            .filter(Tafsir.text.ilike(like))
            .limit(limit)
            .all()
        )
        for t, ch, n in trows:
            push(ch, n, f"তাফসীর: {t.work_name}", t.language, t.text)
            if len(out) >= limit:
                return out[:limit]
    except Exception:
        pass

    # 3b. context notes (asbab / historical / linguistic, Bengali)
    try:
        crows = (
            db.query(ContextNote, Verse.chapter_id, Verse.number)
            .join(Verse, Verse.id == ContextNote.verse_id)
            .filter(ContextNote.text_bn.ilike(like))
            .limit(limit)
            .all()
        )
        for c, ch, n in crows:
            push(ch, n, f"প্রেক্ষাপট ({c.kind})", "bn", c.text_bn)
            if len(out) >= limit:
                return out[:limit]
    except Exception:
        pass

    # 4. root dictionary Bengali meanings → surface first occurrence verse
    try:
        rrows = db.query(RootEntry).filter(RootEntry.meaning_bn.ilike(like)).limit(5).all()
        for r in rrows:
            occ = (
                db.query(Word, Verse.chapter_id, Verse.number)
                .join(Verse, Verse.id == Word.verse_id)
                .filter(Word.root_ar == r.root_ar)
                .order_by(Verse.id)
                .first()
            )
            if occ:
                _, ch, n = occ
                push(ch, n, f"ধাতু {r.root_ar}: {r.meaning_bn}", "bn", f"ধাতু {r.root_ar} — {r.meaning_bn}")
            if len(out) >= limit:
                break
    except Exception:
        pass

    return out[:limit]
