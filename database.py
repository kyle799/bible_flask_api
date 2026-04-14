"""Database helpers — schema creation and query helpers."""

import sqlite3
import os
from typing import Any

DB_PATH = os.environ.get("DATABASE_PATH", "bible.db")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they do not already exist."""
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS translations (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier    TEXT NOT NULL UNIQUE,
                name          TEXT NOT NULL,
                language      TEXT,
                language_code TEXT,
                license       TEXT
            );

            CREATE TABLE IF NOT EXISTS verses (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                book_num       INTEGER,
                book_id        TEXT NOT NULL,
                book           TEXT NOT NULL,
                chapter        INTEGER NOT NULL,
                verse          INTEGER NOT NULL,
                text           TEXT NOT NULL,
                translation_id INTEGER NOT NULL REFERENCES translations(id)
            );

            CREATE INDEX IF NOT EXISTS idx_verses_lookup
                ON verses (translation_id, book_id, chapter, verse);
            """
        )


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def _row(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> dict | None:
    row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None


def _rows(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_translation(conn: sqlite3.Connection, identifier: str) -> dict | None:
    return _row(
        conn,
        "SELECT * FROM translations WHERE LOWER(identifier) = LOWER(?)",
        (identifier,),
    )


def list_translations(conn: sqlite3.Connection) -> list[dict]:
    return _rows(
        conn,
        "SELECT identifier, name, language, language_code, license "
        "FROM translations ORDER BY language, name",
    )


def get_single_verse(
    conn: sqlite3.Connection,
    translation_id: int,
    book_id: str,
    chapter: int,
    verse: int,
) -> dict | None:
    return _row(
        conn,
        "SELECT book_id, book, chapter, verse, text FROM verses "
        "WHERE translation_id=? AND book_id=? AND chapter=? AND verse=?",
        (translation_id, book_id.upper(), chapter, verse),
    )


def _verse_id(
    conn: sqlite3.Connection,
    translation_id: int,
    book_id: str,
    chapter: int,
    verse: int | None,
    last: bool = False,
) -> int | None:
    if verse is not None:
        sql = (
            "SELECT id FROM verses WHERE translation_id=? AND book_id=? "
            "AND chapter=? AND verse=?"
        )
        params: tuple[Any, ...] = (translation_id, book_id.upper(), chapter, verse)
    else:
        order = "DESC" if last else "ASC"
        sql = (
            f"SELECT id FROM verses WHERE translation_id=? AND book_id=? "
            f"AND chapter=? ORDER BY id {order} LIMIT 1"
        )
        params = (translation_id, book_id.upper(), chapter)

    row = conn.execute(sql, params).fetchone()
    return row["id"] if row else None


def get_verses_for_ranges(
    conn: sqlite3.Connection,
    translation_id: int,
    ranges: list[tuple[dict, dict]],
) -> list[dict] | None:
    """
    Fetch all verses for a list of (start, end) ref dicts.
    Returns None if any range boundary cannot be resolved.
    """
    all_verses: list[dict] = []
    for start, end in ranges:
        start_id = _verse_id(
            conn, translation_id,
            start["book_id"], start["chapter"], start.get("verse"),
            last=False,
        )
        end_id = _verse_id(
            conn, translation_id,
            end["book_id"], end["chapter"], end.get("verse"),
            last=True,
        )
        if start_id is None or end_id is None:
            return None
        rows = _rows(
            conn,
            "SELECT book_id, book, chapter, verse, text FROM verses "
            "WHERE id BETWEEN ? AND ? AND translation_id=? ORDER BY id",
            (start_id, end_id, translation_id),
        )
        all_verses.extend(rows)
    return all_verses
