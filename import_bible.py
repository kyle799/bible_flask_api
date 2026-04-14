#!/usr/bin/env python3
"""
Import a Bible translation into the SQLite database.

Supported formats
-----------------
  OSIS XML   (.osis.xml or any .xml whose root is <osis>)
  USFX XML   (.usfx.xml or any .xml whose root is <usfx>)
  Zefania XML (.zefania.xml or any .xml whose root is <XMLBIBLE>)
  CSV        (.csv)  columns: book_id, book, chapter, verse, text

Usage
-----
  python import_bible.py bibles/eng-web.usfx.xml
  python import_bible.py bibles/eng-kjv.osis.xml --name "King James Version"
  python import_bible.py bibles/eng-asv.zefania.xml --id asv --name "American Standard Version"
  python import_bible.py data/web.csv --id web --name "World English Bible"
  python import_bible.py bibles/eng-web.usfx.xml --overwrite
"""

import argparse
import csv
import os
import sqlite3
import sys
from pathlib import Path

from lxml import etree

from database import DB_PATH, init_db
from books import BOOK_ORDER, resolve_book

OSIS_NS = "http://www.bibletechnologies.net/2003/OSIS/namespace"

# Tags whose text content should be skipped (footnotes, cross-refs, headings)
OSIS_SKIP = {"note", "title", "rdg", "catchWord"}
USFX_SKIP = {"f", "x", "fe", "note", "rq", "xt"}


# ---------------------------------------------------------------------------
# OSIS — supports both container-style and milestone-style verses
# ---------------------------------------------------------------------------

def parse_osis(path: Path) -> list[dict]:
    tree = etree.parse(str(path))
    root = tree.getroot()

    verses: list[dict] = []
    current_book_id: str | None = None
    current_book_name: str | None = None
    book_num = 0
    in_verse = False
    milestone = False      # True = milestone style, False = container style
    current_verse_num = 0
    current_chapter = 0
    text_parts: list[str] = []
    skip_depth = 0

    def save_verse() -> None:
        text = " ".join(" ".join(text_parts).split())
        if text and current_book_id and current_chapter and current_verse_num:
            verses.append({
                "book_num": book_num,
                "book_id": current_book_id,
                "book": current_book_name or current_book_id,
                "chapter": current_chapter,
                "verse": current_verse_num,
                "text": text,
            })
        text_parts.clear()

    def ns(tag: str) -> str:
        return f"{{{OSIS_NS}}}{tag}"

    for event, elem in etree.iterwalk(root, events=("start", "end")):
        local = etree.QName(elem.tag).localname

        if event == "start":
            # ── Book ──────────────────────────────────────────────────────
            if local == "div" and elem.get("type") == "book":
                if in_verse:
                    save_verse()
                    in_verse = False
                raw_id = elem.get("osisID", "")
                book_id = resolve_book(raw_id.split(".")[0])
                if book_id:
                    current_book_id = book_id
                    book_num = BOOK_ORDER.index(book_id) + 1
                    current_book_name = None
                else:
                    current_book_id = None

            # ── Chapter ───────────────────────────────────────────────────
            elif local == "chapter":
                # Skip end-markers
                if elem.get("eID"):
                    continue
                if in_verse:
                    save_verse()
                    in_verse = False
                # osisID style: "Gen.1"  — milestone sID style: "Gen.1.seID.xxxxx"
                ref = elem.get("osisID") or elem.get("sID") or ""
                parts = ref.split(".")
                if len(parts) >= 2:
                    try:
                        current_chapter = int(parts[1])
                    except ValueError:
                        pass

            # ── Verse ─────────────────────────────────────────────────────
            elif local == "verse":
                eid = elem.get("eID")
                sid = elem.get("sID")
                osisID = elem.get("osisID")

                if eid:
                    # Milestone end marker
                    if in_verse:
                        save_verse()
                    in_verse = False
                    milestone = False
                elif osisID:
                    if in_verse:
                        save_verse()
                    # Parse verse number from osisID (e.g. "Gen.1.1")
                    parts = osisID.split(".")
                    try:
                        current_verse_num = int(parts[-1])
                    except ValueError:
                        current_verse_num = 0
                    # Detect style
                    milestone = sid is not None
                    text_parts.clear()
                    skip_depth = 0
                    in_verse = True
                    if not milestone and elem.text:
                        # Container style: text is directly in elem.text
                        text_parts.append(elem.text)

            # ── Skip tags ─────────────────────────────────────────────────
            elif in_verse and local in OSIS_SKIP:
                skip_depth += 1

            # ── Inline elements ───────────────────────────────────────────
            elif in_verse and skip_depth == 0:
                if elem.text:
                    text_parts.append(elem.text)

        else:  # event == "end"
            if local == "div" and elem.get("type") == "book":
                if in_verse:
                    save_verse()
                    in_verse = False

            elif local == "title" and current_book_id and current_book_name is None:
                # Grab book title from first <title> inside the book div
                t = (elem.text or "").strip()
                if t:
                    current_book_name = t

            elif local == "verse":
                sid = elem.get("sID")
                osisID = elem.get("osisID")
                if in_verse and milestone and sid and osisID:
                    # Milestone start element: collect tail (actual verse text)
                    if elem.tail:
                        text_parts.append(elem.tail)
                elif in_verse and not milestone and osisID:
                    # Container style end: verse is complete
                    save_verse()
                    in_verse = False

            elif local in OSIS_SKIP:
                skip_depth = max(0, skip_depth - 1)
                if in_verse and skip_depth == 0 and elem.tail:
                    text_parts.append(elem.tail)

            elif in_verse and skip_depth == 0 and local not in ("div", "chapter"):
                if elem.tail:
                    text_parts.append(elem.tail)

    return verses


# ---------------------------------------------------------------------------
# USFX
# ---------------------------------------------------------------------------

def parse_usfx(path: Path) -> list[dict]:
    tree = etree.parse(str(path))
    root = tree.getroot()

    verses: list[dict] = []
    current_book_id: str | None = None
    current_book_name: str | None = None
    book_num = 0
    current_chapter = 0
    current_verse_num = 0
    text_parts: list[str] = []
    in_verse = False
    skip_depth = 0

    VALID_BOOKS = set(BOOK_ORDER)

    def save_verse() -> None:
        text = " ".join(" ".join(text_parts).split())
        if text and current_book_id and current_chapter and current_verse_num:
            verses.append({
                "book_num": book_num,
                "book_id": current_book_id,
                "book": current_book_name or current_book_id,
                "chapter": current_chapter,
                "verse": current_verse_num,
                "text": text,
            })
        text_parts.clear()

    for event, elem in etree.iterwalk(root, events=("start", "end")):
        local = etree.QName(elem.tag).localname

        if event == "start":
            if local == "book":
                bid = elem.get("id", "").upper()
                if bid in VALID_BOOKS:
                    if in_verse:
                        save_verse()
                        in_verse = False
                    current_book_id = bid
                    book_num = BOOK_ORDER.index(bid) + 1
                    current_book_name = None
                    current_chapter = 0
                else:
                    current_book_id = None

            elif local == "c" and current_book_id:
                if in_verse:
                    save_verse()
                    in_verse = False
                try:
                    current_chapter = int(elem.get("id", 0))
                except ValueError:
                    current_chapter = 0

            elif local == "v" and current_book_id and current_chapter:
                if in_verse:
                    save_verse()
                vid = elem.get("id", "0")
                try:
                    current_verse_num = int(vid.split("-")[0])
                except ValueError:
                    current_verse_num = 0
                text_parts.clear()
                skip_depth = 0
                in_verse = True
                # v.text is None (self-closing), text is in tail (collected at end)

            elif local == "ve":
                if in_verse:
                    save_verse()
                in_verse = False

            elif local in USFX_SKIP:
                skip_depth += 1

            elif in_verse and skip_depth == 0 and local not in ("v", "ve", "c", "book"):
                # Inline element — collect leading text
                if elem.text:
                    text_parts.append(elem.text)

        else:  # event == "end"
            if local == "h" and current_book_id and current_book_name is None:
                t = (elem.text or "").strip()
                if t:
                    current_book_name = t

            elif local in USFX_SKIP:
                skip_depth = max(0, skip_depth - 1)
                if in_verse and skip_depth == 0 and elem.tail:
                    text_parts.append(elem.tail)

            elif local == "v" and in_verse:
                # Tail of <v/> is the start of verse text
                if elem.tail:
                    text_parts.append(elem.tail)

            elif in_verse and skip_depth == 0 and local not in ("ve", "c", "book"):
                if elem.tail:
                    text_parts.append(elem.tail)

    return verses


# ---------------------------------------------------------------------------
# Zefania
# ---------------------------------------------------------------------------

def parse_zefania(path: Path) -> list[dict]:
    tree = etree.parse(str(path))
    root = tree.getroot()

    verses: list[dict] = []

    for book_elem in root.iter("BIBLEBOOK"):
        bnumber = int(book_elem.get("bnumber", 0))
        if bnumber < 1 or bnumber > len(BOOK_ORDER):
            continue
        book_id = BOOK_ORDER[bnumber - 1]
        book_name = book_elem.get("bname", book_id)

        for chap_elem in book_elem.iter("CHAPTER"):
            try:
                chapter = int(chap_elem.get("cnumber", 0))
            except ValueError:
                continue

            for vers_elem in chap_elem.iter("VERS"):
                try:
                    verse_num = int(vers_elem.get("vnumber", 0))
                except ValueError:
                    continue
                # Collect all text (Zefania rarely has inline markup)
                text = "".join(vers_elem.itertext()).strip()
                text = " ".join(text.split())
                if text:
                    verses.append({
                        "book_num": bnumber,
                        "book_id": book_id,
                        "book": book_name,
                        "chapter": chapter,
                        "verse": verse_num,
                        "text": text,
                    })

    return verses


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def parse_csv(path: Path) -> list[dict]:
    verses: list[dict] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            book_id = row["book_id"].upper()
            book_num = BOOK_ORDER.index(book_id) + 1 if book_id in BOOK_ORDER else 0
            verses.append({
                "book_num": int(row.get("book_num", book_num)),
                "book_id": book_id,
                "book": row["book"],
                "chapter": int(row["chapter"]),
                "verse": int(row["verse"]),
                "text": row["text"],
            })
    return verses


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------

def detect_format(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".csv"):
        return "csv"
    if "usfx" in name:
        return "usfx"
    if "zefania" in name:
        return "zefania"
    # Peek at the XML root tag
    try:
        for _, elem in etree.iterparse(str(path), events=("start",)):
            local = etree.QName(elem.tag).localname.lower()
            if local == "usfx":
                return "usfx"
            if local in ("xmlbible", "zefania"):
                return "zefania"
            # osis or osisText → osis
            return "osis"
    except Exception:
        pass
    return "osis"


# ---------------------------------------------------------------------------
# Database write
# ---------------------------------------------------------------------------

def import_translation(
    verses: list[dict],
    identifier: str,
    name: str,
    language: str,
    language_code: str,
    license_text: str,
    overwrite: bool,
) -> None:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        existing = conn.execute(
            "SELECT id FROM translations WHERE LOWER(identifier)=LOWER(?)", (identifier,)
        ).fetchone()

        if existing:
            if not overwrite:
                print(f"  skipping '{identifier}' (already exists, use --overwrite)")
                return
            conn.execute("DELETE FROM verses WHERE translation_id=?", (existing["id"],))
            conn.execute("DELETE FROM translations WHERE id=?", (existing["id"],))
            conn.commit()

        conn.execute(
            "INSERT INTO translations (identifier, name, language, language_code, license) "
            "VALUES (?, ?, ?, ?, ?)",
            (identifier, name, language, language_code, license_text),
        )
        translation_id = conn.execute(
            "SELECT id FROM translations WHERE LOWER(identifier)=LOWER(?)", (identifier,)
        ).fetchone()["id"]

        conn.executemany(
            "INSERT INTO verses (book_num, book_id, book, chapter, verse, text, translation_id) "
            "VALUES (:book_num, :book_id, :book, :chapter, :verse, :text, :translation_id)",
            [{**v, "translation_id": translation_id} for v in verses],
        )
        conn.commit()
        print(f"  imported {len(verses):,} verses")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Import a Bible translation into the SQLite database.")
    parser.add_argument("file", help="Path to .osis.xml, .usfx.xml, .zefania.xml, or .csv")
    parser.add_argument("--id", dest="identifier", help="Translation identifier (e.g. web, kjv)")
    parser.add_argument("--name", help="Human-readable translation name")
    parser.add_argument("--language", default="English")
    parser.add_argument("--language-code", default="eng")
    parser.add_argument("--license", default="")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    stem = path.name.split(".")[0]
    parts = stem.split("-")
    auto_id = "-".join(parts[1:]) if len(parts) > 1 else stem

    identifier = (args.identifier or auto_id).lower()
    name = args.name or identifier.upper()

    fmt = detect_format(path)
    print(f"{path.name}  [{fmt}]")

    if fmt == "osis":
        verses = parse_osis(path)
    elif fmt == "usfx":
        verses = parse_usfx(path)
    elif fmt == "zefania":
        verses = parse_zefania(path)
    else:
        verses = parse_csv(path)

    if not verses:
        print("No verses found — check the file format.", file=sys.stderr)
        sys.exit(1)

    import_translation(
        verses=verses,
        identifier=identifier,
        name=name,
        language=args.language,
        language_code=args.language_code,
        license_text=args.license,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
