"""Layered tafsir in Bengali — short attributed summaries per verse."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Tafsir, Verse

router = APIRouter(prefix="/tafsir", tags=["tafsir"])

WORKS = [
    {"code": "ahsanul-bn", "name": "তাফসীর আহসানুল বায়ান (সম্পূর্ণ)",
     "methodology": "classical-theological",
     "source": "Tafsir Ahsanul Bayaan (Bayaan Foundation, Bengali) via quran.com API v4 — full text with attribution"},
    {"code": "zakaria-bn", "name": "তাফসীর আবু বকর যাকারিয়া (সম্পূর্ণ)",
     "methodology": "classical-theological",
     "source": "Tafsir Abu Bakr Zakaria (King Fahd Complex Bengali tr.) via quran.com API v4 — full text with attribution"},
    {"code": "jalalayn-bn", "name": "তাফসীর জালালাইন (সংক্ষেপ, বাংলা)",
     "methodology": "classical-theological",
     "source": "Tafsir al-Jalalayn — Bengali summary with attribution; full text via published editions"},
    {"code": "ibn-kathir-bn", "name": "তাফসীর ইবনে কাসীর (সংক্ষেপ, বাংলা)",
     "methodology": "classical-theological",
     "source": "Tafsir Ibn Kathir, Bengali tr. Dr. Muhammad Mujibur Rahman (18 vols) — summary; full text via publisher"},
    {"code": "maariful-bn", "name": "মাআরিফুল কুরআন (সংক্ষেপ, বাংলা)",
     "methodology": "classical-theological",
     "source": "Maariful Quran, Mufti Shafi Usmani, Bengali tr. Muhiuddin Khan — summary; full text via publisher"},
    {"code": "tabari-bn", "name": "তাফসীর তাবারী (সংক্ষেপ, বাংলা)",
     "methodology": "classical-theological",
     "source": "Tafsir al-Tabari, Bengali tr. under Islamic Foundation Bangladesh — summary"},
    {"code": "tafhim-bn", "name": "তাফহীমুল কুরআন (সংক্ষেপ, বাংলা)",
     "methodology": "classical-theological",
     "source": "Tafhimul Quran, Abul Ala Maududi (Bengali ed.) — summary"},
]


@router.get("/works")
def list_works():
    return WORKS


@router.get("/{chapter_id}/{number}")
def verse_tafsir(
    chapter_id: int,
    number: int,
    lang: str = Query(default="bn"),
    db: Session = Depends(get_db),
):
    v = db.query(Verse).filter(Verse.chapter_id == chapter_id, Verse.number == number).first()
    if not v:
        return []
    rows = (
        db.query(Tafsir)
        .filter(Tafsir.verse_id == v.id, Tafsir.language == lang)
        .order_by(Tafsir.work_code)
        .all()
    )
    return [
        {
            "work_code": r.work_code,
            "work_name": r.work_name,
            "language": r.language,
            "text": r.text,
            "source": r.source,
            "methodology": r.methodology,
        }
        for r in rows
    ]
