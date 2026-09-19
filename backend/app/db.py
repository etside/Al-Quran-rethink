import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DB_PATH = os.environ.get(
    "MIRAZ_DB",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "miraz.db"),
)

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def ensure_bengali_schema() -> None:
    """Create new tables and additively patch legacy `words` tables.

    SQLite has no IF NOT EXISTS ADD COLUMN, so inspect pragma and add
    only missing Bengali columns. Safe to call on every startup.
    """
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        existing = {r[1] for r in conn.exec_driver_sql("PRAGMA table_info(words)").fetchall()}
        wanted = {
            "translation_bn": "TEXT",
            "transliteration": "VARCHAR(128)",
            "lemma": "VARCHAR(64)",
            "root_bn": "TEXT",
            "verb_form": "VARCHAR(32)",
            "grammar_bn": "TEXT",
        }
        for name, ddl in wanted.items():
            if name not in existing:
                conn.exec_driver_sql(f"ALTER TABLE words ADD COLUMN {name} {ddl}")
    _ensure_context_notes_schema()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_context_notes_schema() -> None:
    """Migrate legacy context_notes (verse-only) to verse+chapter scope.

    Adds chapter_id/scope columns and relaxes verse_id to nullable via a
    table rebuild (SQLite), preserving existing rows. Safe to re-run.
    """
    with engine.begin() as conn:
        info = conn.exec_driver_sql("PRAGMA table_info(context_notes)").fetchall()
        if not info:
            return
        cols = {r[1]: r for r in info}  # name -> (cid, name, type, notnull, dflt, pk)
        needs = ("chapter_id" not in cols or "scope" not in cols
                 or cols["verse_id"][3] == 1)
        if not needs:
            return
        conn.exec_driver_sql(
            "CREATE TABLE IF NOT EXISTS context_notes_new ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "verse_id INTEGER REFERENCES verses(id), "
            "chapter_id INTEGER, kind VARCHAR(32), scope VARCHAR(16) DEFAULT 'verse', "
            "text_bn TEXT, text_en TEXT, source TEXT)")
        have_scope = "scope" in cols
        conn.exec_driver_sql(
            "INSERT INTO context_notes_new (id, verse_id, kind, scope, text_bn, text_en, source) "
            f"SELECT id, verse_id, kind, {'scope' if have_scope else chr(39) + 'verse' + chr(39)}, "
            "text_bn, text_en, source FROM context_notes")
        conn.exec_driver_sql("DROP TABLE context_notes")
        conn.exec_driver_sql("ALTER TABLE context_notes_new RENAME TO context_notes")
        conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_context_notes_verse_id ON context_notes (verse_id)")
        conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_context_notes_chapter_id ON context_notes (chapter_id)")
        conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_context_notes_kind ON context_notes (kind)")
