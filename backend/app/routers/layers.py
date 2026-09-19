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
        "name": "Quran text & translations (আরবি · বাংলা · English)",
        "methodology": "scripture / translation",
        "reliability": "unqualified — the Quran itself; translations are scholarly renderings, not revelation",
        "sources": [
            "quran.com API v4 (Tanzil Uthmani text)",
            "Bengali: Taisirul Quran via quran.com (resource 161); alt: Sheikh Mujibur Rahman (163), Rawai Al-bayan (162)",
            "English: Saheeh International (resource 20)",
        ],
        "status": "live",
    },
    {
        "code": "wbw-bn",
        "name": "Word-by-word Bengali (শব্দে শব্দে)",
        "methodology": "linguistic analysis",
        "reliability": "dictionary glosses + transliteration; descriptive, not interpretation",
        "sources": [
            "QuranWBW.com / QUL (qul.tarteel.ai) — Bengali word data (importer stub)",
            "Corpus Quran Bengali word meanings + morphology",
            "Demo seed: Al-Fatiha + Al-Baqarah 1-5 fully glossed",
        ],
        "status": "live",
    },
    {
        "code": "morphology",
        "name": "Root & morphology (ধাতু ও ব্যাকরণ)",
        "methodology": "linguistic analysis",
        "reliability": "corpus-derived — descriptive grammar, not interpretation",
        "sources": [
            "Quranic Arabic Corpus (K. Dukes) and open mirrors",
            "Bengali root glossaries: Mukammal Lugatul Quran (Maimun/Ayubi), Amar Arabi Ovidhan, Al-Kamus (Kamrul Ahsan)",
        ],
        "status": "live",
    },
    {
        "code": "dictionary-bn",
        "name": "Bengali root dictionary (ধাতু অভিধান)",
        "methodology": "linguistic analysis",
        "reliability": "dictionary facts; full lexicon text not bundled (copyright)",
        "sources": [
            "Mukammal Lugatul Quran Arabic-Bangla (parts 1-15)",
            "Amar Arabi Ovidhan (root-word + Quranic-words sections)",
            "Al Kamus Arabic-Bengali-English (Dr. Kamrul Ahsan)",
        ],
        "status": "live",
    },
    {
        "code": "context-bn",
        "name": "Context of revelation (শানে নুযূল ও ইতিহাস)",
        "methodology": "classical-theological",
        "reliability": "labeled summaries with sources; classical claims reported, not asserted",
        "sources": [
            "Asbab al-Nuzul summaries (bn) with classical citations",
            "7th-century Arabia background notes",
            "Early-Arabic semantic notes (Jahili usage, Lisan al-Arab / Kitab al-Ayn refs)",
        ],
        "status": "live",
    },
    {
        "code": "classical-tafsir",
        "name": "Classical tafsir in Bengali (তাফসীর)",
        "methodology": "classical-theological",
        "reliability": "graded per work and school; short attributed summaries seeded, full text via source links",
        "sources": [
            "Tafsir Ibn Kathir bn (18 vols, tr. Dr. Muhammad Mujibur Rahman)",
            "Tafsir Tabari bn (Islamic Foundation Bangladesh)",
            "Maariful Quran bn (Mufti Shafi Usmani, tr. Muhiuddin Khan)",
            "Tafsir Jalalayn bn, Tafhimul Quran bn",
        ],
        "status": "live",
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
        "sources": ["Bayyinah / N. A. Khan study links (Bengali subtitles where available)"],
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
    from ..models import ContextNote, RootEntry, Tafsir

    morph_loaded = db.query(func.count(Word.id)).filter(Word.root_ar.isnot(None)).scalar() or 0
    try:
        bn_words = db.query(func.count(Word.id)).filter(Word.translation_bn.isnot(None)).scalar() or 0
    except Exception:
        bn_words = 0
    try:
        n_roots = db.query(func.count(RootEntry.id)).scalar() or 0
        n_tafsir = db.query(func.count(Tafsir.id)).scalar() or 0
        n_context = db.query(func.count(ContextNote.id)).scalar() or 0
    except Exception:
        n_roots = n_tafsir = n_context = 0
    flags = {
        "quran": True,
        "morphology": morph_loaded > 0,
        "wbw-bn": bn_words > 0,
        "dictionary-bn": n_roots > 0,
        "classical-tafsir": n_tafsir > 0,
        "context-bn": n_context > 0,
    }
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
