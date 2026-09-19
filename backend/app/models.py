from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name_ar: Mapped[str]
    name_en: Mapped[str]
    verses_count: Mapped[int]


class Verse(Base):
    __tablename__ = "verses"

    id: Mapped[int] = mapped_column(primary_key=True)  # global verse number 1..6236
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id"), index=True)
    number: Mapped[int]
    text_uthmani: Mapped[str] = mapped_column(Text)

    translations: Mapped[list["Translation"]] = relationship(
        back_populates="verse", cascade="all, delete-orphan"
    )


class Translation(Base):
    __tablename__ = "translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    verse_id: Mapped[int] = mapped_column(ForeignKey("verses.id"), index=True)
    language: Mapped[str]  # "en" | "bn"
    translator_code: Mapped[str]
    translator_name: Mapped[str]
    text: Mapped[str] = mapped_column(Text)

    verse: Mapped["Verse"] = relationship(back_populates="translations")

    __table_args__ = (UniqueConstraint("verse_id", "translator_code", name="uq_verse_translator"),)


class Word(Base):
    """One word of the Uthmani text. Root data comes from the Quranic Arabic
    Corpus importer; until it runs, root_ar stays null and the root panel
    reports honestly that morphology data is not loaded.

    Bengali layer (QuranLayers goal): translation_bn, transliteration,
    lemma, root_bn, verb_form are filled by scripts/seed_bengali.py for
    the demo corpus (Al-Fatiha + Al-Baqarah 1-5) and by
    scripts/import_bengali_wbw.py for larger imports (QUL / QuranWBW /
    Corpus mirrors)."""

    __tablename__ = "words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    verse_id: Mapped[int] = mapped_column(ForeignKey("verses.id"), index=True)
    position: Mapped[int]
    text_uthmani: Mapped[str]
    translation_en: Mapped[str | None] = mapped_column(Text, default=None)
    root_ar: Mapped[str | None] = mapped_column(String(12), index=True, default=None)
    part_of_speech: Mapped[str | None] = mapped_column(String(64), default=None)
    # ── Bengali-integrated layer ──
    translation_bn: Mapped[str | None] = mapped_column(Text, default=None)
    transliteration: Mapped[str | None] = mapped_column(String(128), default=None)
    lemma: Mapped[str | None] = mapped_column(String(64), default=None)
    root_bn: Mapped[str | None] = mapped_column(Text, default=None)
    verb_form: Mapped[str | None] = mapped_column(String(32), default=None)
    grammar_bn: Mapped[str | None] = mapped_column(Text, default=None)


class RootEntry(Base):
    """Bengali root dictionary: one row per Arabic root (1,651 in the full
    language; demo seed covers the Fatiha/Baqarah-opening roots).

    Sources documented per row: Mukammal Lugatul Quran (Ahmad Maimun /
    Saeed Ahmad Ayubi), Amar Arabi Ovidhan, Al-Kamus (Dr. Kamrul Ahsan),
    Quranic Arabic Corpus morphology. Meanings here are short dictionary
    glosses (facts), full lexicon text is NOT bundled."""

    __tablename__ = "root_dictionary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    root_ar: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    meaning_bn: Mapped[str] = mapped_column(Text)
    meaning_en: Mapped[str | None] = mapped_column(Text, default=None)
    pos_summary: Mapped[str | None] = mapped_column(String(128), default=None)
    verb_forms: Mapped[str | None] = mapped_column(Text, default=None)
    occurrences: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str] = mapped_column(Text, default="")
    methodology: Mapped[str] = mapped_column(String(64), default="linguistic analysis")


class Tafsir(Base):
    """Layered tafsir excerpts/summaries per verse.

    Copyright rule: only short original Bengali *summaries* with full
    attribution are seeded (works: Jalalayn, Ibn Kathir-bn tr. Mujibur
    Rahman, Tabari-bn / Islamic Foundation, Maariful Quran-bn tr.
    Muhiuddin Khan, Tafhimul Quran). Full book text is never bundled —
    use `source` links / importer stubs for licensed corpora."""

    __tablename__ = "tafsir"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    verse_id: Mapped[int] = mapped_column(ForeignKey("verses.id"), index=True)
    work_code: Mapped[str] = mapped_column(String(64), index=True)
    work_name: Mapped[str] = mapped_column(String(128))
    language: Mapped[str] = mapped_column(String(8), default="bn")
    text: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text, default="")
    methodology: Mapped[str] = mapped_column(String(64), default="classical-theological")


class ContextNote(Base):
    """Asbab al-Nuzul + historical + early-Arabic semantic notes, in Bengali
    (with optional English gloss). Verse-level (verse_id) or chapter-level
    (chapter_id, applies to every verse of the chapter as fallback).
    Summaries with attribution; classical claims are labeled, not asserted."""

    __tablename__ = "context_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    verse_id: Mapped[int | None] = mapped_column(ForeignKey("verses.id"), index=True, default=None)
    chapter_id: Mapped[int | None] = mapped_column(Integer, index=True, default=None)
    kind: Mapped[str] = mapped_column(String(32), index=True)  # asbab | historical | linguistic
    scope: Mapped[str] = mapped_column(String(16), default="verse")  # verse | chapter
    text_bn: Mapped[str] = mapped_column(Text)
    text_en: Mapped[str | None] = mapped_column(Text, default=None)
    source: Mapped[str] = mapped_column(Text, default="")
