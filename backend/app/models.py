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
    reports honestly that morphology data is not loaded."""

    __tablename__ = "words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    verse_id: Mapped[int] = mapped_column(ForeignKey("verses.id"), index=True)
    position: Mapped[int]
    text_uthmani: Mapped[str]
    translation_en: Mapped[str | None] = mapped_column(Text, default=None)
    root_ar: Mapped[str | None] = mapped_column(String(12), index=True, default=None)
    part_of_speech: Mapped[str | None] = mapped_column(String(64), default=None)
