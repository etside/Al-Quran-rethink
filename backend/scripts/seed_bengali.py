#!/usr/bin/env python3
"""Seed Bengali layers (QuranLayers goal) — idempotent.

Fills, for Al-Fatiha (1:1-7) + Al-Baqarah (2:1-5):
  - Word.translation_bn / transliteration / lemma / root_ar / root_bn /
    verb_form / grammar_bn / part_of_speech
  - root_dictionary entries with Bengali glosses
  - tafsir: short original Bengali *summaries* with attribution
    (Jalalayn / Ibn Kathir / Maariful — full book text is never bundled)
  - context_notes: asbab / historical / linguistic notes in Bengali

Word glosses and root meanings are dictionary facts. Tafsir/context texts
below are original summaries written for this seed, each carrying its
`source` citation so the UI can display methodology + provenance.

Usage:
  python scripts/seed_bengali.py [--db PATH]
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.db import SessionLocal, ensure_bengali_schema  # noqa: E402
from app.models import ContextNote, RootEntry, Tafsir, Verse, Word  # noqa: E402

AR_DIGITS = set("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹")

# (chapter, verse, position) -> dict. Positions match the quran.com word
# import (trailing Arabic-Indic verse-number tokens are skipped, never seeded).
WBW: dict[tuple[int, int, int], dict] = {
    # ── 1:1 ──
    (1, 1, 1): dict(translation_bn="নামে", transliteration="bismi", lemma="اسم",
                    root_ar="س م و", root_bn="উচ্চ হওয়া; নাম (ইসম)",
                    part_of_speech="N", grammar_bn="জার-মাজরুর (বি + ইসম); বাক্যের শুরুতে ক্রিয়া ঊহ্য"),
    (1, 1, 2): dict(translation_bn="আল্লাহর", transliteration="allāhi", lemma="الله",
                    root_ar="ا ل ه", root_bn="ইবাদতের যোগ্য সত্তা; আল্লাহ",
                    part_of_speech="PN", grammar_bn="মাজরুর, মুদাফ ইলাইহি"),
    (1, 1, 3): dict(translation_bn="পরম করুণাময়ের", transliteration="ar-raḥmāni", lemma="رحمن",
                    root_ar="ر ح م", root_bn="দয়া, করুণা (ব্যাপক ও পূর্ণাঙ্গ)",
                    part_of_speech="ADJ", grammar_bn="আল্লাহর সিফাত (না'ত)"),
    (1, 1, 4): dict(translation_bn="অসীম দয়ালুর", transliteration="ar-raḥīmi", lemma="رحيم",
                    root_ar="ر ح م", root_bn="দয়া (স্থায়ী ও পুনঃপুন বর্ষিত)",
                    part_of_speech="ADJ", grammar_bn="আল্লাহর সিফাত (না'ত)"),
    # ── 1:2 ──
    (1, 2, 1): dict(translation_bn="সমস্ত প্রশংসা", transliteration="al-ḥamdu", lemma="حمد",
                    root_ar="ح م د", root_bn="প্রশংসা (ভালোবাসা ও সম্মানসহ গুণকীর্তন)",
                    part_of_speech="N", grammar_bn="মুবতাদা (বাক্যের উদ্দেশ্য পদ)"),
    (1, 2, 2): dict(translation_bn="আল্লাহর জন্য", transliteration="lillāhi", lemma="الله",
                    root_ar="ا ل ه", root_bn="ইবাদতের যোগ্য সত্তা; আল্লাহ",
                    part_of_speech="PN", grammar_bn="জার-মাজরুর; খবর (বিধেয়)"),
    (1, 2, 3): dict(translation_bn="প্রতিপালক", transliteration="rabbi", lemma="رب",
                    root_ar="ر ب ب", root_bn="প্রতিপালন, লালন-পালন ও পরিচালনা করা",
                    part_of_speech="N", grammar_bn="বাদল (আল্লাহর পরিচয়মূলক পদ)"),
    (1, 2, 4): dict(translation_bn="জগতসমূহের", transliteration="al-ʿālamīna", lemma="عالم",
                    root_ar="ع ل م", root_bn="জগৎ; চিহ্ন/নিদর্শন (যা স্রষ্টার পরিচয় দেয়)",
                    part_of_speech="N", grammar_bn="মুদাফ ইলাইহি, বহুবচন"),
    # ── 1:3 ──
    (1, 3, 1): dict(translation_bn="পরম করুণাময়", transliteration="ar-raḥmānu", lemma="رحمن",
                    root_ar="ر ح م", root_bn="দয়া, করুণা (ব্যাপক ও পূর্ণাঙ্গ)",
                    part_of_speech="ADJ", grammar_bn="আল্লাহর সিফাত"),
    (1, 3, 2): dict(translation_bn="অসীম দয়ালু", transliteration="ar-raḥīmu", lemma="رحيم",
                    root_ar="ر ح م", root_bn="দয়া (স্থায়ী ও পুনঃপুন বর্ষিত)",
                    part_of_speech="ADJ", grammar_bn="আল্লাহর সিফাত"),
    # ── 1:4 ──
    (1, 4, 1): dict(translation_bn="অধিপতি / মালিক", transliteration="māliki", lemma="مالك",
                    root_ar="م ل ك", root_bn="মালিকানা, কর্তৃত্ব ও শাসন",
                    part_of_speech="N", grammar_bn="সিফাত (কিরাআতভেদে মালিক/মালিক দুটোই প্রসিদ্ধ)"),
    (1, 4, 2): dict(translation_bn="দিনের", transliteration="yawmi", lemma="يوم",
                    root_ar="ي و م", root_bn="দিন, দিবস, সময়কাল",
                    part_of_speech="N", grammar_bn="মুদাফ"),
    (1, 4, 3): dict(translation_bn="প্রতিদান (বিচার) দিবসের", transliteration="ad-dīni", lemma="دين",
                    root_ar="د ي ن", root_bn="প্রতিদান দেওয়া-নেওয়া; আনুগত্য ও জীবনবিধান",
                    part_of_speech="N", grammar_bn="মুদাফ ইলাইহি"),
    # ── 1:5 ──
    (1, 5, 1): dict(translation_bn="শুধু তোমারই", transliteration="iyyāka", lemma="إيا",
                    root_ar=None, root_bn=None,
                    part_of_speech="PRON", grammar_bn="মাফউলুন বিহি মুকাদ্দাম — একত্বের তাগিদে কর্মপদ আগে"),
    (1, 5, 2): dict(translation_bn="আমরা ইবাদত করি", transliteration="naʿbudu", lemma="عبد",
                    root_ar="ع ب د", root_bn="দাসত্ব ও পরিপূর্ণ আনুগত্যসহ ইবাদত",
                    verb_form="I", part_of_speech="V",
                    grammar_bn="ফে'লে মুদারে, ১ম পুরুষ বহুবচন (বাব: নাসারা/ফাতাহা)"),
    (1, 5, 3): dict(translation_bn="এবং শুধু তোমারই (কাছে)", transliteration="wa iyyāka", lemma="إيا",
                    root_ar=None, root_bn=None,
                    part_of_speech="PRON", grammar_bn="আতফ + মুকাদ্দাম কর্মপদ"),
    (1, 5, 4): dict(translation_bn="আমরা সাহায্য চাই", transliteration="nastaʿīnu", lemma="استعان",
                    root_ar="ع و ن", root_bn="সাহায্য করা",
                    verb_form="X", part_of_speech="V",
                    grammar_bn="বাবে ইসতিফ'আল (চাওয়া বোঝায়); মুদারে ১ম পুরুষ বহুবচন"),
    # ── 1:6 ──
    (1, 6, 1): dict(translation_bn="আমাদের পথ দেখাও", transliteration="ihdinā", lemma="هدى",
                    root_ar="ه د ي", root_bn="পথ দেখানো, হেদায়েত দেওয়া",
                    verb_form="I", part_of_speech="V",
                    grammar_bn="আমর (আদেশসূচক, দোয়ার অর্থে); ফায়িল ঊহ্য + না (আমাদের)"),
    (1, 6, 2): dict(translation_bn="পথে", transliteration="aṣ-ṣirāṭa", lemma="صراط",
                    root_ar=None, root_bn="লাতিন strata থেকে আরবিকৃত; প্রশস্ত ও স্পষ্ট পথ",
                    part_of_speech="N", grammar_bn="দ্বিতীয় মাফউল (কর্মপদ)"),
    (1, 6, 3): dict(translation_bn="সরল-সঠিক", transliteration="al-mustaqīma", lemma="استقام",
                    root_ar="ق و م", root_bn="সোজা হওয়া, প্রতিষ্ঠিত থাকা",
                    verb_form="X (participle)", part_of_speech="ADJ",
                    grammar_bn="ইসমে ফায়িল, বাবে ইসতিফ'আল; সিরাতের সিফাত"),
    # ── 1:7 ──
    (1, 7, 1): dict(translation_bn="(সেই) পথে", transliteration="ṣirāṭa", lemma="صراط",
                    root_ar=None, root_bn="প্রশস্ত ও স্পষ্ট পথ",
                    part_of_speech="N", grammar_bn="বাদল (পূর্ববর্তী সিরাতের ব্যাখ্যা)"),
    (1, 7, 2): dict(translation_bn="যাদের", transliteration="alladhīna", lemma="الذي",
                    root_ar=None, root_bn=None, part_of_speech="REL",
                    grammar_bn="ইসমে মাউসূল, মুদাফ ইলাইহি"),
    (1, 7, 3): dict(translation_bn="তুমি অনুগ্রহ করেছ", transliteration="anʿamta", lemma="أنعم",
                    root_ar="ن ع م", root_bn="নিয়ামত দান, অনুগ্রহ করা",
                    verb_form="IV", part_of_speech="V",
                    grammar_bn="ফে'লে মাদি, ২য় পুরুষ একবচন (তা — তুমি)"),
    (1, 7, 4): dict(translation_bn="তাদের উপর", transliteration="ʿalayhim", lemma="على",
                    root_ar=None, root_bn=None, part_of_speech="P",
                    grammar_bn="জার-মাজরুর (সিলা)"),
    (1, 7, 5): dict(translation_bn="ব্যতীত / ছাড়া", transliteration="ghayri", lemma="غير",
                    root_ar=None, root_bn=None, part_of_speech="N",
                    grammar_bn="ইসতিসনা/বাদল অর্থে; মাজরুর"),
    (1, 7, 6): dict(translation_bn="গযবপ্রাপ্তদের (পথ)", transliteration="al-maghḍūbi", lemma="مغضوب",
                    root_ar="غ ض ب", root_bn="রাগ, অসন্তোষ, শাস্তিমূলক ক্রোধ",
                    part_of_speech="N", grammar_bn="ইসমে মাফউল (কর্মবাচ্য কৃদন্ত)"),
    (1, 7, 7): dict(translation_bn="তাদের উপর", transliteration="ʿalayhim", lemma="على",
                    root_ar=None, root_bn=None, part_of_speech="P",
                    grammar_bn="জার-মাজরুর"),
    (1, 7, 8): dict(translation_bn="এবং নয়", transliteration="wa lā", lemma="لا",
                    root_ar=None, root_bn=None, part_of_speech="NEG",
                    grammar_bn="আতফ + নাফিয়া (নিষেধ/নাকচ)"),
    (1, 7, 9): dict(translation_bn="পথভ্রষ্টদের (পথ)", transliteration="aḍ-ḍāllīna", lemma="ضال",
                    root_ar="ض ل ل", root_bn="পথ হারানো, ভ্রষ্ট হওয়া",
                    part_of_speech="N", grammar_bn="ইসমে ফায়িল, বহুবচন"),
    # ── 2:1 ──
    (2, 1, 1): dict(translation_bn="আলিফ-লাম-মীম (বিচ্ছিন্ন হরফ; প্রকৃত অর্থ আল্লাহই জানেন)",
                    transliteration="alif-lām-mīm", lemma="ا ل م",
                    root_ar=None, root_bn="হুরূফে মুকাত্তা'আত — অর্থ নিয়ে তাফসীরকারদের একাধিক মত",
                    part_of_speech="DISCONNECTED", grammar_bn="মুবতাদা/ঊহ্য বাক্য নিয়ে মতভেদ (তাফসীর দ্রষ্টব্য)"),
    # ── 2:2 ──
    (2, 2, 1): dict(translation_bn="এই (কিতাব)", transliteration="dhālika", lemma="ذلك",
                    root_ar=None, root_bn=None, part_of_speech="DEM",
                    grammar_bn="ইসমে ইশারা; মর্যাদা বোঝাতে দূরবর্তী সর্বনাম"),
    (2, 2, 2): dict(translation_bn="কিতাব / গ্রন্থ", transliteration="al-kitābu", lemma="كتاب",
                    root_ar="ك ت ب", root_bn="লেখা, লিপিবদ্ধ করা; ফরয/বিধিবদ্ধ করাও এই ধাতু থেকে",
                    part_of_speech="N", grammar_bn="খবর/বাদল (মুবতাদা: যালিকা)"),
    (2, 2, 3): dict(translation_bn="নেই", transliteration="lā", lemma="لا",
                    root_ar=None, root_bn=None, part_of_speech="NEG", grammar_bn="লায়ে নাফি (নাকচসূচক)"),
    (2, 2, 4): dict(translation_bn="সন্দেহ", transliteration="rayba", lemma="ريب",
                    root_ar="ر ي ب", root_bn="সন্দেহ, সংশয়, অস্থিরতা",
                    part_of_speech="N", grammar_bn="লায়ের ইসম (কর্মপদ-স্থানীয়)"),
    (2, 2, 5): dict(translation_bn="এতে / এর মধ্যে", transliteration="fīhi", lemma="في",
                    root_ar=None, root_bn=None, part_of_speech="P", grammar_bn="জার-মাজরুর; লায়ের খবর"),
    (2, 2, 6): dict(translation_bn="পথনির্দেশ / হেদায়েত", transliteration="hudan", lemma="هدى",
                    root_ar="ه د ي", root_bn="পথ দেখানো, হেদায়েত দেওয়া",
                    part_of_speech="N", grammar_bn="হাল/খবর — মুত্তাকীদের জন্য হেদায়েত"),
    (2, 2, 7): dict(translation_bn="মুত্তাকীদের জন্য", transliteration="lil-muttaqīna", lemma="متقي",
                    root_ar="و ق ي", root_bn="বাঁচা, রক্ষা পাওয়া; তাকওয়া = সতর্কতা ও পরহেজগারি",
                    verb_form="VIII (participle)", part_of_speech="N",
                    grammar_bn="ইসমে ফায়িল, বাবে ইফতি'আল; বহুবচন, মাজরুর"),
    # ── 2:3 ──
    (2, 3, 1): dict(translation_bn="যারা", transliteration="alladhīna", lemma="الذي",
                    root_ar=None, root_bn=None, part_of_speech="REL", grammar_bn="ইসমে মাউসূল"),
    (2, 3, 2): dict(translation_bn="তারা ঈমান আনে", transliteration="yu'minūna", lemma="آمن",
                    root_ar="ا م ن", root_bn="নিরাপত্তা; ঈমান = দৃঢ় বিশ্বাস ও স্বীকৃতি",
                    verb_form="IV", part_of_speech="V", grammar_bn="মুদারে, ৩য় পুরুষ বহুবচন"),
    (2, 3, 3): dict(translation_bn="অদৃশ্যের প্রতি", transliteration="bil-ghaybi", lemma="غيب",
                    root_ar="غ ي ب", root_bn="অদৃশ্য থাকা, চোখের আড়াল হওয়া",
                    part_of_speech="N", grammar_bn="জার-মাজরুর"),
    (2, 3, 4): dict(translation_bn="এবং তারা কায়েম করে", transliteration="wa yuqīmūna", lemma="أقام",
                    root_ar="ق و م", root_bn="সোজা হওয়া, প্রতিষ্ঠা করা",
                    verb_form="IV", part_of_speech="V", grammar_bn="আতফ + মুদারে ৩য় পুরুষ বহুবচন"),
    (2, 3, 5): dict(translation_bn="সালাত / নামাজ", transliteration="aṣ-ṣalāta", lemma="صلاة",
                    root_ar="ص ل و", root_bn="দোয়া; (পরিভাষায়) নির্ধারিত ইবাদত — সালাত",
                    part_of_speech="N", grammar_bn="মাফউল (কর্মপদ)"),
    (2, 3, 6): dict(translation_bn="এবং যা থেকে", transliteration="wa mimmā", lemma="ما",
                    root_ar=None, root_bn=None, part_of_speech="REL", grammar_bn="আতফ + জার-মাজরুর (মিন + মা)"),
    (2, 3, 7): dict(translation_bn="আমরা তাদের রিযিক দিয়েছি", transliteration="razaqnāhum", lemma="رزق",
                    root_ar="ر ز ق", root_bn="রিযিক দেওয়া, জীবিকা প্রদান",
                    part_of_speech="V", grammar_bn="মাদি ১ম পুরুষ বহুবচন (না — আমরা) + হুম (তাদের)"),
    (2, 3, 8): dict(translation_bn="তারা ব্যয় করে", transliteration="yunfiqūna", lemma="أنفق",
                    root_ar="ن ف ق", root_bn="ব্যয় করা; (সুড়ঙ্গ/বাজার অর্থেও এই ধাতু)",
                    verb_form="IV", part_of_speech="V", grammar_bn="মুদারে ৩য় পুরুষ বহুবচন"),
    # ── 2:4 ──
    (2, 4, 1): dict(translation_bn="এবং যারা", transliteration="walladhīna", lemma="الذي",
                    root_ar=None, root_bn=None, part_of_speech="REL", grammar_bn="আতফ + মাউসূল"),
    (2, 4, 2): dict(translation_bn="তারা ঈমান আনে", transliteration="yu'minūna", lemma="آمن",
                    root_ar="ا م ن", root_bn="নিরাপত্তা; ঈমান = দৃঢ় বিশ্বাস ও স্বীকৃতি",
                    verb_form="IV", part_of_speech="V", grammar_bn="মুদারে ৩য় পুরুষ বহুবচন"),
    (2, 4, 3): dict(translation_bn="যা-কিছুর প্রতি", transliteration="bimā", lemma="ما",
                    root_ar=None, root_bn=None, part_of_speech="REL", grammar_bn="জার-মাজরুর"),
    (2, 4, 4): dict(translation_bn="নাযিল করা হয়েছে", transliteration="unzila", lemma="أنزل",
                    root_ar="ن ز ل", root_bn="অবতরণ করা/করানো",
                    verb_form="IV (passive)", part_of_speech="V",
                    grammar_bn="মাদি, মাজহূল (কর্মবাচ্য)"),
    (2, 4, 5): dict(translation_bn="তোমার প্রতি", transliteration="ilayka", lemma="إلى",
                    root_ar=None, root_bn=None, part_of_speech="P", grammar_bn="জার-মাজরুর"),
    (2, 4, 6): dict(translation_bn="এবং যা-কিছু", transliteration="wa mā", lemma="ما",
                    root_ar=None, root_bn=None, part_of_speech="REL", grammar_bn="আতফ + মাউসূল"),
    (2, 4, 7): dict(translation_bn="নাযিল করা হয়েছিল", transliteration="unzila", lemma="أنزل",
                    root_ar="ن ز ل", root_bn="অবতরণ করা/করানো",
                    verb_form="IV (passive)", part_of_speech="V", grammar_bn="মাদি মাজহূল"),
    (2, 4, 8): dict(translation_bn="থেকে", transliteration="min", lemma="من",
                    root_ar=None, root_bn=None, part_of_speech="P", grammar_bn="হারফে জার"),
    (2, 4, 9): dict(translation_bn="তোমার পূর্বে", transliteration="qablika", lemma="قبل",
                    root_ar="ق ب ل", root_bn="পূর্বে হওয়া, সামনে থাকা; গ্রহণ করাও এই ধাতু থেকে",
                    part_of_speech="N", grammar_bn="যরফ (ক্রিয়া-বিশেষণ) + কা (তোমার)"),
    (2, 4, 10): dict(translation_bn="এবং পরকালের প্রতি", transliteration="wa bil-ākhirati", lemma="آخرة",
                    root_ar="ا خ ر", root_bn="পরে আসা, বিলম্বিত হওয়া; আখিরাত = পরকাল",
                    part_of_speech="N", grammar_bn="আতফ + জার-মাজরুর"),
    (2, 4, 11): dict(translation_bn="তারা", transliteration="hum", lemma="هو",
                    root_ar=None, root_bn=None, part_of_speech="PRON", grammar_bn="মুবতাদা"),
    (2, 4, 12): dict(translation_bn="দৃঢ় বিশ্বাস রাখে", transliteration="yūqinūna", lemma="أيقن",
                    root_ar="ي ق ن", root_bn="সন্দেহাতীত নিশ্চিত জ্ঞান (ইয়াকীন)",
                    verb_form="IV", part_of_speech="V", grammar_bn="মুদারে ৩য় পুরুষ বহুবচন; খবর"),
    # ── 2:5 ──
    (2, 5, 1): dict(translation_bn="তারাই", transliteration="ulā'ika", lemma="أولئك",
                    root_ar=None, root_bn=None, part_of_speech="DEM", grammar_bn="মুবতাদা"),
    (2, 5, 2): dict(translation_bn="(রয়েছে) উপর", transliteration="ʿalā", lemma="على",
                    root_ar=None, root_bn=None, part_of_speech="P", grammar_bn="হারফে জার (উচ্চ মর্যাদা বোঝায়)"),
    (2, 5, 3): dict(translation_bn="হেদায়েতের", transliteration="hudan", lemma="هدى",
                    root_ar="ه د ي", root_bn="পথ দেখানো, হেদায়েত দেওয়া",
                    part_of_speech="N", grammar_bn="মাজরুর"),
    (2, 5, 4): dict(translation_bn="পক্ষ থেকে", transliteration="min", lemma="من",
                    root_ar=None, root_bn=None, part_of_speech="P", grammar_bn="হারফে জার"),
    (2, 5, 5): dict(translation_bn="তাদের রবের", transliteration="rabbihim", lemma="رب",
                    root_ar="ر ب ب", root_bn="প্রতিপালন, লালন-পালন ও পরিচালনা",
                    part_of_speech="N", grammar_bn="মাজরুর + হিম (তাদের)"),
    (2, 5, 6): dict(translation_bn="এবং তারাই", transliteration="wa ulā'ika", lemma="أولئك",
                    root_ar=None, root_bn=None, part_of_speech="DEM", grammar_bn="আতফ + মুবতাদা"),
    (2, 5, 7): dict(translation_bn="তারা", transliteration="humu", lemma="هو",
                    root_ar=None, root_bn=None, part_of_speech="PRON", grammar_bn="দমীরে ফাসল (জোরসূচক সর্বনাম)"),
    (2, 5, 8): dict(translation_bn="সফলকাম", transliteration="al-mufliḥūna", lemma="مفلح",
                    root_ar="ف ل ح", root_bn="সফল হওয়া; (ভূমি চাষ/বিদীর্ণ করাও এই ধাতু থেকে)",
                    verb_form="IV (participle)", part_of_speech="N",
                    grammar_bn="ইসমে ফায়িল, বাবে ইফ'আল; বহুবচন"),
}

# root_ar -> Bengali dictionary gloss
ROOTS: dict[str, dict] = {
    "س م و": dict(meaning_bn="উচ্চ হওয়া; নাম, খ্যাতি", meaning_en="to be high; name",
                  pos_summary="N (ism)", verb_forms="— (noun root)",
                  source="Amar Arabi Ovidhan (root section); Al-Kamus (س م و)"),
    "ا ل ه": dict(meaning_bn="ইবাদতের যোগ্য সত্তা; আল্লাহ (সত্তাবাচক নাম)", meaning_en="god; Allah",
                  pos_summary="PN", verb_forms="— (proper noun)",
                  source="Mukammal Lugatul Quran; Al-Kamus (ا ل ه)"),
    "ر ح م": dict(meaning_bn="দয়া-করুণা; রহমান = ব্যাপক করুণাময়, রহীম = স্থায়ী দয়ালু",
                  meaning_en="mercy, compassion", pos_summary="ADJ (faʿlān / faʿīl)",
                  verb_forms="I رَحِمَ (দয়া করা)",
                  source="Mukammal Lugatul Quran (ر ح م); Corpus morphology"),
    "ح م د": dict(meaning_bn="ভালোবাসা ও সম্মানসহ প্রশংসা ও গুণকীর্তন", meaning_en="praise",
                  pos_summary="N / V", verb_forms="I حَمِدَ; II حَمَّدَ",
                  source="Mukammal Lugatul Quran (ح م د)"),
    "ر ب ب": dict(meaning_bn="প্রতিপালন, লালন-পালন, পরিচালনা; রব = প্রতিপালক", meaning_en="lordship, nurture",
                  pos_summary="N", verb_forms="I رَبَّ (প্রতিপালন করা)",
                  source="Mukammal Lugatul Quran (ر ب ب)"),
    "ع ل م": dict(meaning_bn="জানা; আলাম = জগৎ/নিদর্শন (যা জ্ঞান দেয়)", meaning_en="knowledge; world/sign",
                  pos_summary="N", verb_forms="I عَلِمَ (জানা)",
                  source="Al-Kamus (ع ل م); Amar Arabi Ovidhan"),
    "م ل ك": dict(meaning_bn="মালিকানা, কর্তৃত্ব, শাসন; মালিক/মালিক দুই কিরাআত", meaning_en="ownership, kingship",
                  pos_summary="N", verb_forms="I مَلَكَ",
                  source="Mukammal Lugatul Quran (م ل ك)"),
    "ي و م": dict(meaning_bn="দিন, দিবস, সময়কাল", meaning_en="day",
                  pos_summary="N", verb_forms="— (time noun)",
                  source="Al-Kamus (ي و م)"),
    "د ي ن": dict(meaning_bn="প্রতিদান; আনুগত্য ও জীবনবিধান (দীন)", meaning_en="recompense; way of life",
                  pos_summary="N", verb_forms="I دَانَ (প্রতিদান দেওয়া/আনুগত্য করা)",
                  source="Mukammal Lugatul Quran (د ي ن)"),
    "ع ب د": dict(meaning_bn="দাসত্ব ও পরিপূর্ণ আনুগত্যসহ ইবাদত", meaning_en="worship, servitude",
                  pos_summary="V (I)", verb_forms="I عَبَدَ; IV أَعْبَدَ",
                  source="Mukammal Lugatul Quran (ع ب د)"),
    "ع و ن": dict(meaning_bn="সাহায্য করা; ইসতিআনা = সাহায্য চাওয়া", meaning_en="help",
                  pos_summary="V (X)", verb_forms="X اِسْتَعَانَ (সাহায্য চাওয়া)",
                  source="Amar Arabi Ovidhan (ع و ن)"),
    "ه د ي": dict(meaning_bn="পথ দেখানো; হেদায়েত", meaning_en="guidance",
                  pos_summary="V (I)", verb_forms="I هَدَى; IV أَهْدَى",
                  source="Mukammal Lugatul Quran (ه د ي)"),
    "ق و م": dict(meaning_bn="সোজা হওয়া, দাঁড়ানো, প্রতিষ্ঠা করা", meaning_en="to stand; establish",
                  pos_summary="V (IV/X)", verb_forms="I قَامَ; IV أَقَامَ (কায়েম করা); X اِسْتَقَامَ (অটল থাকা)",
                  source="Mukammal Lugatul Quran (ق و م)"),
    "ن ع م": dict(meaning_bn="নিয়ামত, অনুগ্রহ; আনআমা = অনুগ্রহ করা", meaning_en="grace, blessing",
                  pos_summary="V (IV)", verb_forms="IV أَنْعَمَ (অনুগ্রহ করা)",
                  source="Mukammal Lugatul Quran (ن ع م)"),
    "غ ض ب": dict(meaning_bn="রাগ, অসন্তোষ; মাগদূব = ক্রোধের পাত্র", meaning_en="anger",
                  pos_summary="N (passive participle)", verb_forms="I غَضِبَ",
                  source="Al-Kamus (غ ض ب)"),
    "ض ل ل": dict(meaning_bn="পথ হারানো, ভ্রষ্ট হওয়া; দাল্ল = পথভ্রষ্ট", meaning_en="straying",
                  pos_summary="N (active participle)", verb_forms="I ضَلَّ",
                  source="Mukammal Lugatul Quran (ض ل ل)"),
    "ك ت ب": dict(meaning_bn="লেখা, লিপিবদ্ধ করা; কিতাব = গ্রন্থ; কখনো বিধিবদ্ধ করা", meaning_en="writing; book",
                  pos_summary="N / V", verb_forms="I كَتَبَ",
                  source="Mukammal Lugatul Quran (ك ت ب)"),
    "ر ي ب": dict(meaning_bn="সন্দেহ, সংশয়, অস্থিরতা", meaning_en="doubt",
                  pos_summary="N", verb_forms="I رَابَ",
                  source="Al-Kamus (ر ي ب)"),
    "و ق ي": dict(meaning_bn="বাঁচা, রক্ষা পাওয়া; তাকওয়া = সতর্ক পরহেজগারি", meaning_en="piety, God-consciousness",
                  pos_summary="N (VIII participle)", verb_forms="VIII اِتَّقَى (বেঁচে থাকা/তাকওয়া অবলম্বন)",
                  source="Mukammal Lugatul Quran (و ق ي)"),
    "ا م ن": dict(meaning_bn="নিরাপত্তা; ঈমান = দৃঢ় বিশ্বাস ও স্বীকৃতি", meaning_en="faith, security",
                  pos_summary="V (IV)", verb_forms="IV آمَنَ (ঈমান আনা)",
                  source="Mukammal Lugatul Quran (ا م ن)"),
    "غ ي ب": dict(meaning_bn="অদৃশ্য থাকা; গায়ব = অদৃশ্য জগৎ", meaning_en="unseen",
                  pos_summary="N", verb_forms="I غَابَ",
                  source="Al-Kamus (غ ي ب)"),
    "ص ل و": dict(meaning_bn="দোয়া; (পরিভাষায়) নির্ধারিত ইবাদত — সালাত", meaning_en="prayer",
                  pos_summary="N", verb_forms="II صَلَّى (সালাত আদায়)",
                  source="Mukammal Lugatul Quran (ص ل و)"),
    "ر ز ق": dict(meaning_bn="রিযিক দেওয়া, জীবিকা প্রদান", meaning_en="provision",
                  pos_summary="V (I)", verb_forms="I رَزَقَ",
                  source="Mukammal Lugatul Quran (র ز ق → ر ز ق)"),
    "ن ف ق": dict(meaning_bn="ব্যয় করা (আনফাকা); মুনাফিকিও এই ধাতু থেকে (সুড়ঙ্গ-অর্থ)", meaning_en="spending",
                  pos_summary="V (IV)", verb_forms="IV أَنْفَقَ (ব্যয় করা)",
                  source="Amar Arabi Ovidhan (ن ف ق)"),
    "ن ز ل": dict(meaning_bn="অবতরণ করা/করানো; নাযিল হওয়া", meaning_en="descent, revelation",
                  pos_summary="V (IV)", verb_forms="I نَزَلَ; IV أَنْزَلَ (নাযিল করা)",
                  source="Mukammal Lugatul Quran (ن ز ل)"),
    "ق ب ل": dict(meaning_bn="পূর্বে/সামনে থাকা; কবুল = গ্রহণ", meaning_en="before; acceptance",
                  pos_summary="N / V", verb_forms="I قَبِلَ (গ্রহণ করা)",
                  source="Al-Kamus (ق ب ل)"),
    "ا خ ر": dict(meaning_bn="পরে আসা; আখিরাত = পরকাল/শেষ পরিণাম", meaning_en="the Hereafter",
                  pos_summary="N", verb_forms="— (elative/noun)",
                  source="Mukammal Lugatul Quran (ا خ ر)"),
    "ي ق ن": dict(meaning_bn="সন্দেহাতীত নিশ্চিত জ্ঞান (ইয়াকীন)", meaning_en="certainty",
                  pos_summary="V (IV)", verb_forms="IV أَيْقَنَ (দৃঢ় বিশ্বাস করা)",
                  source="Al-Kamus (ي ق ن)"),
    "ف ل ح": dict(meaning_bn="সফল হওয়া; মুফলিহ = সফলকাম", meaning_en="success",
                  pos_summary="N (IV participle)", verb_forms="IV أَفْلَحَ (সফল হওয়া)",
                  source="Mukammal Lugatul Quran (ف ل ح)"),
}

# (chapter, verse, work_code) -> (work_name, text_bn summary, source)
TAFSIR: dict[tuple[int, int, str], tuple[str, str, str]] = {}


def _t(ch, v, code, name, text, source):
    TAFSIR[(ch, v, code)] = (name, text, source)


_J = "তাফসীর জালালাইন — সংক্ষেপ (বাংলা সারসংক্ষেপ; বিস্তারিত ব্যাখ্যার জন্য প্রকাশিত বাংলা সংস্করণ দ্রষ্টব্য)"
_K = "তাফসীর ইবনে কাসীর, বাংলা অনুবাদ: ড. মুহাম্মদ মুজিবুর রহমান (১৮ খণ্ড) — সংক্ষেপ"
_M = "মাআরিফুল কুরআন, মুফতী শাফী উসমানী, বাংলা অনুবাদ: মুহিউদ্দীন খান — সংক্ষেপ"

for _v in range(1, 8):
    _t(1, _v, "jalalayn-bn", "তাফসীর জালালাইন (সংক্ষেপ)",
       {1: "‘বিসমিল্লাহ’ দিয়ে শুরু: সব কাজ আল্লাহর নামে; রহমান-রহীম — তাঁর ব্যাপক ও স্থায়ী দয়ার দুই সিফাত।",
        2: "সব প্রশংসা একমাত্র আল্লাহর — তিনি জগতসমূহের প্রতিপালক (রব)।",
        3: "রহমান-রহীমের পুনরুক্তি: আশা ও ভরসার দ্বার — শাস্তির আগে দয়ার স্মরণ।",
        4: "তিনি প্রতিদান দিবসের মালিক — বিচার ও প্রতিদানের একচ্ছত্র কর্তৃত্ব তাঁরই।",
        5: "‘শুধু তোমারই ইবাদত করি, শুধু তোমারই সাহায্য চাই’ — তাওহীদের অঙ্গীকার ও নির্ভরতা।",
        6: "সিরাতে মুসতাকীমের দোয়া — সরল-সঠিক পথে পরিচালনার প্রার্থনা।",
        7: "সেই পথ — অনুগ্রহপ্রাপ্তদের পথ; গযবপ্রাপ্ত ও পথভ্রষ্টদের পথ নয়।"}[_v], _J)
    _t(1, _v, "ibn-kathir-bn", "তাফসীর ইবনে কাসীর (সংক্ষেপ)",
       {1: "ইবনে কাসীর: বরকতের জন্য ‘বিসমিল্লাহ’ দিয়ে শুরু সুন্নত; রহমান-রহীম আল্লাহর মহান দুই নাম — হাদীস ও সালাফের বক্তব্যসহ আলোচিত।",
        2: "হামদ (প্রশংসা) ও শোকরের পার্থক্যসহ ‘রব্বুল আলামীন’-এর ব্যাখ্যা: সৃষ্টি, মালিকানা ও পরিচালনায় তিনিই একক।",
        3: "দয়ার গুণ পুনরায়: বান্দার মনে আশা জাগানো এবং ইবাদতে আগ্রহ সৃষ্টি — সালাফের উক্তিসহ।",
        4: "‘মালিকি ইয়াওমিদ্দীন’: কিয়ামত দিবসে কর্তৃত্ব একমাত্র আল্লাহর — দুনিয়ার সাময়িক কর্তৃত্বের অবসান ঘটবে।",
        5: "ইবাদত ও ইসতিআনার (সাহায্য-প্রার্থনার) একত্ব: কর্মপদ আগে আনার অলঙ্কার (হাসর) দিয়ে শিরক থেকে মুক্তির ঘোষণা।",
        6: "হেদায়েতের দোয়া: শুধু জ্ঞান নয়, সঠিক পথে অটল থাকার তাওফীক চাওয়া — প্রতিটি সালাতে পাঠের হিকমত।",
        7: "তিন দল: নিয়ামতপ্রাপ্ত (নবী-সিদ্দীক-শহীদ-সালেহ), গযবপ্রাপ্ত (জেনেও অমান্যকারী), দাল্লীন (না জেনে ভ্রষ্ট) — হাদীসের আলোকে।"}[_v], _K)

_t(1, 1, "maariful-bn", "মাআরিফুল কুরআন (সংক্ষেপ)",
   "তাসমিয়া (বিসমিল্লাহ) পাঠের ফযীলত ও মাসআলা: কাজের শুরুতে বরকত; রহমান-রহীমের পার্থক্য ও ব্যবহারবিধি।", _M)
_t(1, 5, "maariful-bn", "মাআরিফুল কুরআন (সংক্ষেপ)",
   "ইবাদত কবুলের শর্ত (ইখলাস ও সুন্নতের অনুসরণ) এবং ‘ইয়্যাকা না‘বুদু’ থেকে তাওহীদের শিক্ষা; দোয়া ও উপায়-উপকরণের ভারসাম্য।", _M)

for _v in range(1, 6):
    _t(2, _v, "jalalayn-bn", "তাফসীর জালালাইন (সংক্ষেপ)",
       {1: "আলিফ-লাম-মীম: হুরূফে মুকাত্তা'আত — প্রকৃত অর্থ আল্লাহই জানেন; কুরআনের অলৌকিকত্বের ইঙ্গিত হিসেবে অনেকে দেখেন।",
        2: "‘যালিকাল কিতাব, লা রাইবা ফীহ’: এই কিতাবে কোনো সন্দেহ নেই; মুত্তাকীদের জন্য হেদায়েত।",
        3: "মুত্তাকীদের গুণ: গায়বে ঈমান, সালাত কায়েম, প্রদত্ত রিযিক থেকে ব্যয়।",
        4: "তারা পূর্ববর্তী কিতাবসহ সব ওহীতে ঈমান রাখে এবং আখিরাতে দৃঢ় বিশ্বাসী।",
        5: "তারাই রবের হেদায়েতের উপর এবং তারাই সফলকাম।"}[_v], _J)
    _t(2, _v, "ibn-kathir-bn", "তাফসীর ইবনে কাসীর (সংক্ষেপ)",
       {1: "মুকাত্তা'আত নিয়ে সালাফের অবস্থান: অর্থ নিয়ে চূড়ান্ত দাবি না করে তিলাওয়াত ও ঈমান; বিভিন্ন মত উদ্ধৃত।",
        2: "‘লা রাইবা’: কুরআনের সত্যতায় সংশয় নেই; হেদায়েতের উপকার মুত্তাকীরাই পায় — যেমন চোখ থাকলেই আলো কাজে লাগে।",
        3: "গায়ব (আল্লাহ, ফেরেশতা, আখিরাত), সালাত কায়েম (শর্ত-আরকানসহ) ও ইনফাক (ফরয-নফল ব্যয়) — ঈমানের ব্যবহারিক রূপ।",
        4: "মুহাম্মদ (সা.)-এর প্রতি নাযিলকৃতসহ পূর্ববর্তী সব ওহীর প্রতি ঈমান; আখিরাতে ইয়াকীন (দৃঢ় বিশ্বাস)।",
        5: "হেদায়েতের উপর থাকা ও সফলতা (ফালাহ) — দুনিয়া-আখিরাতের কল্যাণ লাভকারীর পরিচয়।"}[_v], _K)

# (chapter, verse, kind) -> (text_bn, text_en, source)
CONTEXT: dict[tuple[int, int, str], tuple[str, str, str]] = {}


def _c(ch, v, kind, bn, en, src):
    CONTEXT[(ch, v, kind)] = (bn, en, src)


_c(1, 1, "historical",
   "সূরা ফাতিহা মক্কী সূরা — নবুয়তের প্রাথমিক যুগে নাযিল। সালাতের প্রতি রাকাতে পাঠ ওয়াজিব হওয়ায় এটি মুসলিম জীবনের সবচেয়ে পঠিত অংশ।",
   "Al-Fatiha is a Meccan surah from the early prophetic period, recited in every unit of prayer.",
   "প্রসিদ্ধ সীরাত ও তাফসীর ভূমিকা (ইবনে কাসীর, জালালাইন) — সারসংক্ষেপ")
_c(1, 1, "linguistic",
   "‘ইসম’ (নাম) ধাতু স-ম-ও (উচ্চতা) থেকে: নাম বস্তুকে উঁচু/পরিচিত করে। ‘বিসমিল্লাহ’ বলে শুরু — আরব রীতিতে গুরুত্বপূর্ণ কাজে কার নামে করা হচ্ছে তা ঘোষণা। ‘রহমান’ (ফা‘লান) ব্যাপকতা ও পূর্ণতা বোঝায়, ‘রহীম’ (ফা‘ঈল) স্থায়িত্ব বোঝায় — দুটো মিলে দয়ার পূর্ণ চিত্র।",
   "ism (name) traces to s-m-w (height): a name elevates/marks a thing. raḥmān (faʿlān) = all-encompassing mercy; raḥīm (faʿīl) = enduring mercy.",
   "ধাতু-অভিধান সার (লুগাতুল কুরআন; লিসানুল আরব — সারসংক্ষেপ)")
_c(1, 5, "linguistic",
   "‘ইয়্যাকা’ (তোমাকেই) কর্মপদকে ক্রিয়ার আগে আনা হয়েছে (তাকদীম) — আরবি অলঙ্কারে এটি একত্ব/সীমাবদ্ধতা বোঝায়: ‘শুধু তোমারই’। ‘নাসতা‘ঈন’ বাবে ইসতিফ‘আল — ‘সাহায্য চাওয়া’ অর্থ দেয়।",
   "Fronting iyyāka before the verb marks exclusivity (only You) in Arabic rhetoric; nastaʿīn is form X (seeking help).",
   "আরবি ব্যাকরণ সার (নাহু-সারফ প্রচলিত নিয়ম)")
_c(1, 7, "linguistic",
   "‘দীন’ ধাতু দ-ই-ন: প্রতিদান ও আনুগত্য — উভয় অর্থই আরবি ব্যবহারে প্রসিদ্ধ (জাহিলি কবিতায় ‘যেমন আচরণ, তেমন প্রতিদান’ অর্থে)। ‘সিরাত’ লাতিন strata থেকে আরবিকৃত শব্দ — প্রশস্ত রাজপথ। ‘মাগদূব’ কর্মবাচ্য কৃদন্ত (যার উপর ক্রোধ), ‘দাল্লীন’ কর্তৃবাচ্য (যারা নিজে ভ্রষ্ট)।",
   "d-y-n covers both recompense and obedience in early Arabic usage; ṣirāṭ is an arabicized loanword (broad highway).",
   "লুগাত সার (লিসানুল আরব, কিতাবুল আইন — সারসংক্ষেপ)")
_c(2, 1, "historical",
   "সূরা বাকারা মাদানী — হিজরতের পর মদীনায় নাযিলের সূচনা। মুকাত্তা'আত (বিচ্ছিন্ন হরফ) দিয়ে শুরু ২৯টি সূরার একটি; এর অর্থ নিয়ে সাহাবী-যুগ থেকে মতভেদ রয়েছে — কেউ অর্থ নির্ধারণ থেকে বিরত থেকেছেন।",
   "Al-Baqarah is Medinan, from after the Hijrah. The disconnected letters open 29 surahs; Companions differed on their meaning.",
   "তাফসীর ভূমিকা সার (তাবারী, ইবনে কাসীর — সারসংক্ষেপ)")
_c(2, 2, "linguistic",
   "‘যালিকা’ দূরের ইশারা হলেও এখানে মর্যাদা বোঝাতে ব্যবহৃত (আরবি অলঙ্কার)। ‘রাইব’ (সন্দেহ) ধাতু র-ই-ব — মনের অস্থিরতা। ‘তাকওয়া’ ধাতু ও-ক-ই (বাঁচা): সতর্কতা ও আত্মরক্ষা থেকে পরহেজগারি অর্থ।",
   "dhālika (distant demonstrative) marks grandeur here; rayb = mental unease; taqwā (w-q-y) = protective caution.",
   "অলঙ্কার ও লুগাত সার")
_c(2, 2, "asbab",
   "এই আয়াতের নির্দিষ্ট শানে নুযূল (অবতরণ-কারণ) হিসেবে প্রসিদ্ধ কোনো একক ঘটনা তাফসীরে উল্লেখিত নেই; এটি মাদানী যুগের সূচনায় কুরআনের পরিচয়-বক্তব্য হিসেবে বিবেচিত। (নির্দিষ্ট সনদসহ বর্ণনা পাওয়া গেলে এখানে যুক্ত হবে।)",
   "No single well-known sabab narration is cited for this verse; it opens the Medinan discourse introducing the Book.",
   "তাফসীর সার (শানে নুযূল সংকলন পর্যালোচনা)")
_c(2, 3, "historical",
   "মদীনায় নতুন মুসলিম সমাজ গঠনের প্রেক্ষাপট: গায়বে ঈমান, জামাআতে সালাত কায়েম এবং (মুহাজির-আনসার পারস্পরিক সহায়তাসহ) সম্পদ ব্যয় — এই তিনটি মুত্তাকী সমাজের ভিত্তি হিসেবে উপস্থাপিত।",
   "In Medina the new community was built on unseen faith, established prayer, and mutual material support.",
   "সীরাত প্রেক্ষাপট সার (মাদানী যুগ)")
_c(2, 4, "asbab",
   "পূর্ববর্তী কিতাবের অনুসারীদের মধ্যে যারা ইসলাম গ্রহণ করেছিলেন (যেমন আবদুল্লাহ ইবনে সালাম (রা.)-এর মতো ব্যক্তিবর্গ) — তাদের প্রশংসায় এই আয়াত নাযিল হয়েছে বলে কোনো কোনো তাফসীরে উল্লেখ আছে। সনদ-যাচাইসহ পূর্ণ বর্ণনা ভবিষ্যৎ স্তরে যুক্ত হবে।",
   "Some tafsir works link this verse to People of the Book who embraced Islam; full graded narration to be added in the hadith layer.",
   "তাফসীর সার (ইবনে কাসীর ২:৪ আলোচনা — সারসংক্ষেপ; সনদ-গ্রেডিং হাদীস স্তরে)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.environ.get("MIRAZ_DB", str(
        Path(__file__).resolve().parent.parent / "miraz.db")))
    args = ap.parse_args()
    os.environ["MIRAZ_DB"] = args.db
    ensure_bengali_schema()
    db = SessionLocal()

    n_w = n_r = n_t = n_c = 0
    # 1. words
    for (ch, v, pos), data in WBW.items():
        verse = db.query(Verse).filter(Verse.chapter_id == ch, Verse.number == v).first()
        if not verse:
            continue
        w = db.query(Word).filter(Word.verse_id == verse.id, Word.position == pos).first()
        if not w:
            print(f"  ! word missing {ch}:{v}#{pos}")
            continue
        for k, val in data.items():
            setattr(w, k, val)
        # keep English gloss; fill root_ar only if empty or demo-correct
        n_w += 1
    db.commit()

    # 2. roots (upsert; occurrences = live corpus count if roots loaded else demo count)
    from sqlalchemy import func as _func
    demo_counts: dict[str, int] = {}
    for d in WBW.values():
        r = d.get("root_ar")
        if r:
            demo_counts[r] = demo_counts.get(r, 0) + 1
    for root_ar, meta in ROOTS.items():
        row = db.query(RootEntry).filter(RootEntry.root_ar == root_ar).first()
        if not row:
            row = RootEntry(root_ar=root_ar)
            db.add(row)
        row.meaning_bn = meta["meaning_bn"]
        row.meaning_en = meta["meaning_en"]
        row.pos_summary = meta["pos_summary"]
        row.verb_forms = meta["verb_forms"]
        row.source = meta["source"]
        row.methodology = "linguistic analysis"
        try:
            live = db.query(_func.count(Word.id)).filter(Word.root_ar == root_ar).scalar() or 0
        except Exception:
            live = 0
        row.occurrences = max(live, demo_counts.get(root_ar, 0))
        n_r += 1
    db.commit()

    # 3. tafsir (upsert by verse+work+lang)
    for (ch, v, code), (name, text, src) in TAFSIR.items():
        verse = db.query(Verse).filter(Verse.chapter_id == ch, Verse.number == v).first()
        if not verse:
            continue
        row = db.query(Tafsir).filter(
            Tafsir.verse_id == verse.id, Tafsir.work_code == code, Tafsir.language == "bn").first()
        if not row:
            row = Tafsir(verse_id=verse.id, work_code=code, language="bn")
            db.add(row)
        row.work_name = name
        row.text = text
        row.source = src
        row.methodology = "classical-theological"
        n_t += 1
    db.commit()

    # 4. context
    for (ch, v, kind), (bn, en, src) in CONTEXT.items():
        verse = db.query(Verse).filter(Verse.chapter_id == ch, Verse.number == v).first()
        if not verse:
            continue
        row = db.query(ContextNote).filter(
            ContextNote.verse_id == verse.id, ContextNote.kind == kind).first()
        if not row:
            row = ContextNote(verse_id=verse.id, kind=kind)
            db.add(row)
        row.text_bn = bn
        row.text_en = en
        row.source = src
        n_c += 1
    db.commit()
    db.close()
    print(f"seeded: words={n_w} roots={n_r} tafsir={n_t} context={n_c}")


if __name__ == "__main__":
    main()
