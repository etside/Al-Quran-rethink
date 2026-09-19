#!/usr/bin/env python3
"""Chapter-level context notes for ALL 114 surahs (Bengali).

Writes, per chapter:
  - historical: Makki/Madani type + revelation order + verse count + period
    background (facts from quran.com chapter metadata + standard summaries)
  - asbab: only for chapters with a famous, well-attested sabab (93, 108,
    109, 111, 112, 113, 114) — framed as reported summaries, never asserted

Chapter notes carry scope='chapter' and are served as fallback for every
verse of the chapter (see routers/context.py), so all 6,236 verses have
context coverage. Idempotent.

Usage:
  python scripts/seed_chapter_context.py [--db PATH]
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.bn_names import CHAPTER_NAMES_BN  # noqa: E402
from app.db import SessionLocal, ensure_bengali_schema  # noqa: E402
from app.models import Chapter, ContextNote  # noqa: E402

META_CACHE = Path(__file__).resolve().parent.parent / "data" / "chapter_meta.json"

# Fallback if the API is unreachable: the 28 Madani surahs (standard list)
MADANI_FALLBACK = {2, 3, 4, 5, 8, 9, 13, 22, 24, 33, 47, 48, 49, 55, 57, 58,
                   59, 60, 61, 62, 63, 64, 65, 66, 76, 98, 99, 110}

HIST_SOURCE = ("সূরা-পরিচিতি সার: অবতরণ-স্থান ও ক্রম quran.com API (Tanzil) মেটাডেটা; "
               "যুগ-বৈশিষ্ট্য সীরাত ও তাফসীর-ভূমিকার প্রসিদ্ধ সারসংক্ষেপ")

MAKKI_BG = ("মক্কী যুগে (নবুয়তের প্রথম ~১৩ বছর) অবতীর্ণ সূরাগুলোর মূল বিষয়: তাওহীদ "
            "(আল্লাহর একত্ব), রিসালাত ও আখিরাতের প্রতি ঈমান; পূর্ববর্তী নবীদের ঘটনা, "
            "সৎকর্মে উৎসাহ এবং শিরক ও অন্যায় থেকে সতর্কবাণী।")
MADANI_BG = ("মাদানী যুগে (হিজরতের পর মদীনায়, ~১০ বছর) মুসলিম সমাজ গঠনের প্রেক্ষাপটে "
             "অবতীর্ণ: ইবাদত-বিধান, পারিবারিক ও সামাজিক আইন, আহলে কিতাব ও মুনাফিকদের "
             "প্রসঙ্গ এবং জামাআতবদ্ধ জীবনের নির্দেশনা এই যুগের সূরার বৈশিষ্ট্য।")

# chapter -> (text_bn, text_en) — famous, well-attested sababs only
ASBAB = {
    93: ("ওহী আসা কিছুদিন বন্ধ থাকার পর মুশরিকরা কটাক্ষ করেছিল যে ‘তোমার রব তোমাকে "
         "ত্যাগ করেছেন’ — এমন প্রসঙ্গে সান্ত্বনা ও সুসংবাদ হিসেবে সূরা আদ-দুহা নাযিল "
         "হয় বলে প্রসিদ্ধ বর্ণনায় এসেছে।",
         "After a pause in revelation, detractors taunted the Prophet ﷺ; Ad-Duha came as consolation, per well-known reports."),
    108: ("পুত্রদের ইন্তেকালের পর আস ইবনে ওয়ায়িল তাঁকে ‘আবতার’ (বংশহীন) বলে কটাক্ষ "
           "করেছিল — এর জবাবে আল-কাউসারের সুসংবাদ নাযিল হয় বলে প্রসিদ্ধ।",
         "After the death of his sons, detractors called him 'cut off'; Al-Kawthar came as reassurance, per well-known reports."),
    109: ("মুশরিকরা আপস প্রস্তাব দিয়েছিল — এক বছর তাদের উপাস্য, এক বছর আল্লাহর "
           "ইবাদত — তা চূড়ান্তভাবে প্রত্যাখ্যান করে আল-কাফিরূন নাযিল হয়।",
         "The disbelievers proposed alternating worship; Al-Kafirun came as a decisive rejection."),
    111: ("সাফা পাহাড়ে আত্মীয়দের দাওয়াতের দিন আবু লাহাব ‘তাব্বান লাকা’ (তোমার ধ্বংস "
           "হোক) বলেছিল — এর জবাবে আল-মাসাদ নাযিল হয় বলে সহীহ বর্ণনায় এসেছে।",
         "After Abu Lahab cursed the Prophet ﷺ at Safa, Al-Masad was revealed, per authentic reports."),
    112: ("মুশরিকরা ‘তোমার রবের বংশ-পরিচয় বলো’ দাবি করলে জবাবে আল-ইখলাস নাযিল হয় "
           "বলে প্রসিদ্ধ বর্ণনায় এসেছে।",
         "When asked to describe his Lord's lineage, Al-Ikhlas was revealed in reply, per well-known reports."),
    113: ("আশ্রয়-প্রার্থনার সূরা (মুআওবিযাতাইন-এর একটি)। যাদু ও হিংসুকের অনিষ্টসহ সব "
           "অনিষ্ট থেকে আল্লাহর আশ্রয় চাওয়ার শিক্ষা; রুকইয়াহ (ঝাড়ফুঁক) হিসেবে পাঠ "
           "প্রসিদ্ধ হাদীসে এসেছে।",
         "A surah of refuge (one of the Mu'awwidhatayn); recited as ruqyah per well-known hadith."),
    114: ("আশ্রয়-প্রার্থনার সূরা (মুআওবিযাতাইন-এর একটি)। কুমন্ত্রণাদানকারী শয়তান থেকে "
           "আল্লাহর আশ্রয় চাওয়ার শিক্ষা; রুকইয়াহ হিসেবে পাঠ প্রসিদ্ধ হাদীসে এসেছে।",
         "A surah of refuge (one of the Mu'awwidhatayn); recited as ruqyah per well-known hadith."),
}
ASBAB_SOURCE = "শানে নুযূলের প্রসিদ্ধ বর্ণনার সারসংক্ষেপ (বিস্তারিত সনদ-যাচাই হাদীস স্তরে)"


def get_meta() -> dict[int, dict]:
    if META_CACHE.exists():
        return {int(k): v for k, v in json.loads(META_CACHE.read_text(encoding="utf-8")).items()}
    try:
        import httpx
        with httpx.Client(headers={"User-Agent": "Miraz/0.2"}, timeout=60) as c:
            data = c.get("https://api.quran.com/api/v4/chapters",
                         params={"language": "en"}).json()["chapters"]
        meta = {c["id"]: {"place": c.get("revelation_place"),
                          "order": c.get("revelation_order"),
                          "verses": c.get("verses_count")} for c in data}
        META_CACHE.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
        return meta
    except Exception as e:  # noqa: BLE001
        print(f"  meta fetch failed ({e}); using fallback classification")
        return {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.environ.get("MIRAZ_DB", str(
        Path(__file__).resolve().parent.parent / "miraz.db")))
    args = ap.parse_args()
    os.environ["MIRAZ_DB"] = args.db
    ensure_bengali_schema()
    db = SessionLocal()
    meta = get_meta()

    n_h = n_a = 0
    chapters = db.query(Chapter).order_by(Chapter.id).all()
    for ch in chapters:
        m = meta.get(ch.id, {})
        place = (m.get("place") or ("madinah" if ch.id in MADANI_FALLBACK else "makkah"))
        madani = place == "madinah"
        order = m.get("order")
        name = CHAPTER_NAMES_BN.get(ch.id, ch.name_en)
        order_txt = f"অবতরণ ক্রম {order}তম, " if order else ""
        text_bn = (f"{name} — {'মাদানী' if madani else 'মক্কী'} সূরা "
                   f"({order_txt}{ch.verses_count} আয়াত)। {(MADANI_BG if madani else MAKKI_BG)}")
        text_en = (f"{ch.name_en} — a {'Medinan' if madani else 'Meccan'} surah "
                   f"({ch.verses_count} verses).")
        row = db.query(ContextNote).filter(
            ContextNote.scope == "chapter", ContextNote.chapter_id == ch.id,
            ContextNote.kind == "historical").first()
        if not row:
            row = ContextNote(chapter_id=ch.id, verse_id=None, kind="historical", scope="chapter")
            db.add(row)
        row.text_bn, row.text_en, row.source = text_bn, text_en, HIST_SOURCE
        n_h += 1

        if ch.id in ASBAB:
            bn, en = ASBAB[ch.id]
            row = db.query(ContextNote).filter(
                ContextNote.scope == "chapter", ContextNote.chapter_id == ch.id,
                ContextNote.kind == "asbab").first()
            if not row:
                row = ContextNote(chapter_id=ch.id, verse_id=None, kind="asbab", scope="chapter")
                db.add(row)
            row.text_bn, row.text_en, row.source = bn, en, ASBAB_SOURCE
            n_a += 1
    db.commit()
    db.close()
    print(f"chapter context: historical={n_h} asbab={n_a}")


if __name__ == "__main__":
    main()
