"""
Parses human-readable Bible references into structured data.

Supported formats
-----------------
  John 3:16
  John 3:16-18          (verse range, same chapter)
  John 3:16-4:1         (cross-chapter range)
  John 3               (whole chapter)

Returns a list of (start, end) dicts, each with keys:
  book_id, chapter, verse  (verse may be None for chapter-start/end)
"""

import re
from books import resolve_book, SINGLE_CHAPTER_BOOKS

# Matches "Book 3:16" or "Book 3" with optional leading number ("1 John")
_BOOK_RE = r"(?:[123]\s+)?[A-Za-z]+"
_REF_RE = re.compile(
    rf"^({_BOOK_RE})\s+(\d+)(?::(\d+))?(?:\s*[-–]\s*(?:(\d+):)?(\d+))?$",
    re.IGNORECASE,
)


def parse_ref(ref_string: str) -> list[tuple[dict, dict]] | None:
    """
    Parse a reference string and return a list of (start, end) range tuples,
    or None if the reference cannot be parsed.
    """
    ref_string = ref_string.strip()
    m = _REF_RE.match(ref_string)
    if not m:
        return None

    book_name, ch1, v1, ch2, v2 = m.groups()

    book_id = resolve_book(book_name)
    if book_id is None:
        return None

    ch1 = int(ch1)
    v1 = int(v1) if v1 is not None else None

    if v2 is not None:
        # Range given
        v2 = int(v2)
        if ch2 is not None:
            end_ch = int(ch2)
        else:
            end_ch = ch1
        start = {"book_id": book_id, "chapter": ch1, "verse": v1 if v1 is not None else 1}
        end = {"book_id": book_id, "chapter": end_ch, "verse": v2}
    elif v1 is not None:
        # Single verse
        start = {"book_id": book_id, "chapter": ch1, "verse": v1}
        end = {"book_id": book_id, "chapter": ch1, "verse": v1}
    else:
        # Whole chapter
        start = {"book_id": book_id, "chapter": ch1, "verse": None}
        end = {"book_id": book_id, "chapter": ch1, "verse": None}

    return [(start, end)]
