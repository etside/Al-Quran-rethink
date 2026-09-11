"""Layer registry — the transparency core of Miraz.

Each interpretive layer is declared here with its methodology, provenance and
status. The API never presents a layer without these labels, and the frontend
renders them verbatim. Only the Quran itself is unqualified.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Word

router = APIRouter(prefix="/layers", tags=["layers"])

LAYERS = [
    {
        "code": "quran",
        "name": "Quran text & translations",
        "methodology": "scripture / translation",
        "reliability": "unqualified — the Quran itself; translations are scholarly renderings, not revelation",
        "sources": ["quran.com API v4 (Tanzil text)"],
        "status": "live",
    },
    {
        "code": "morphology",
        "name": "Root & morphology",
        "methodology": "linguistic analysis",
        "reliability": "corpus-derived — descriptive grammar, not interpretation",
        "sources": ["Quranic Arabic Corpus (K. Dukes) and open mirrors"],
        "status": "live",
    },
    {
        "code": "classical-tafsir",
        "name": "Classical tafsir",
        "methodology": "classical-theological",
        "reliability": "graded per work and school; see work metadata",
        "sources": ["al-Jalalayn", "Ibn Kathir", "al-Muyassar", "al-Tabari (planned)"],
        "status": "planned",
    },
    {
        "code": "hadith",
        "name": "Hadith & isnad",
        "methodology": "prophetic tradition",
        "reliability": "per-narration grades (sahih / hasan / daif) with narrator chains",
        "sources": ["community open hadith datasets (sunnah.com-compatible)"],
        "status": "planned",
    },
    {
        "code": "ahl-al-bayt",
        "name": "Ahl al-Bayt tafsir",
        "methodology": "ahl-al-bayt",
        "reliability": "per-work provenance (al-Mizan, al-Qummi, al-Ayyashi subsets)",
        "sources": ["curated subsets + source links"],
        "status": "planned",
    },
    {
        "code": "contemporary-linguistic",
        "name": "Contemporary linguistic",
        "methodology": "contemporary-linguistic",
        "reliability": "labeled contemporary opinion; reference links, not bundled text (copyright)",
        "sources": ["Bayyinah / N. A. Khan study links"],
        "status": "planned",
    },
    {
        "code": "scientific",
        "name": "Scientific interpretation",
        "methodology": "scientific",
        "reliability": "distinct interpretive framework — user-supplied sources, not consensus",
        "sources": ["user-provided"],
        "status": "planned",
    },
]


@router.get("")
def list_layers(db: Session = Depends(get_db)):
    """Registry with live data flags so the UI can show what is actually loaded."""
    morph_loaded = db.query(func.count(Word.id)).filter(Word.root_ar.isnot(None)).scalar() or 0
    flags = {"quran": True, "morphology": morph_loaded > 0}
    return [
        {**layer, "has_data": flags.get(layer["code"], layer["status"] == "live")}
        for layer in LAYERS
    ]


@router.get("/{code}")
def get_layer(code: str):
    for layer in LAYERS:
        if layer["code"] == code:
            return layer
    from fastapi import HTTPException

    raise HTTPException(404, f"unknown layer: {code}")
