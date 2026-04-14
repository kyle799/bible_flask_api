"""Bible Flask API — main application."""

from flask import Flask, jsonify, request, abort, render_template
from database import get_db, init_db, get_translation, list_translations, get_single_verse, get_verses_for_ranges
from books import resolve_book
from ref_parser import parse_ref

app = Flask(__name__)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

DEFAULT_TRANSLATION = "web"


def _translation_or_404(conn, identifier: str) -> dict:
    t = get_translation(conn, identifier)
    if not t:
        abort(404, description=f"Translation '{identifier}' not found.")
    return t


def _json(data, status: int = 200):
    resp = jsonify(data)
    resp.status_code = status
    for k, v in CORS_HEADERS.items():
        resp.headers[k] = v
    return resp


def _verse_dict(v: dict) -> dict:
    return {
        "book_id": v["book_id"],
        "book_name": v["book"],
        "chapter": v["chapter"],
        "verse": v["verse"],
        "text": v["text"],
    }


def _normalize_ref(ranges: list[tuple[dict, dict]]) -> str:
    """Build a human-readable reference string from parsed ranges."""
    parts = []
    for start, end in ranges:
        book = start["book_id"]
        if start["verse"] is None:
            parts.append(f"{book} {start['chapter']}")
        elif start == end:
            parts.append(f"{book} {start['chapter']}:{start['verse']}")
        elif start["chapter"] == end["chapter"]:
            parts.append(f"{book} {start['chapter']}:{start['verse']}-{end['verse']}")
        else:
            parts.append(
                f"{book} {start['chapter']}:{start['verse']}-{end['chapter']}:{end['verse']}"
            )
    return "; ".join(parts)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        resp = app.make_default_options_response()
        for k, v in CORS_HEADERS.items():
            resp.headers[k] = v
        return resp


@app.route("/bible", methods=["GET"])
def bible_reader():
    """Web reader UI."""
    with get_db() as conn:
        translations = list_translations(conn)
    return render_template("bible.html", translations=translations)


@app.route("/translations", methods=["GET"])
def translations():
    """List all available translations."""
    with get_db() as conn:
        rows = list_translations(conn)
    return _json({"translations": rows})


@app.route("/verse/<book>/<int:chapter>/<int:verse>", methods=["GET"])
def single_verse(book: str, chapter: int, verse: int):
    """
    Fetch a single verse.

    Query params
    ------------
    translation : str  (default: web)
    """
    translation_id_param = request.args.get("translation", DEFAULT_TRANSLATION)
    book_id = resolve_book(book)
    if not book_id:
        abort(404, description=f"Book '{book}' not recognised.")

    with get_db() as conn:
        translation = _translation_or_404(conn, translation_id_param)
        row = get_single_verse(conn, translation["id"], book_id, chapter, verse)

    if not row:
        abort(404, description="Verse not found.")

    return _json({
        "reference": f"{row['book']} {chapter}:{verse}",
        "verses": [_verse_dict(row)],
        "text": row["text"],
        "translation_id": translation["identifier"],
        "translation_name": translation["name"],
        "translation_note": translation.get("license", ""),
    })


@app.route("/passage", methods=["GET"])
def passage():
    """
    Fetch a passage by reference string.

    Query params
    ------------
    ref         : str  e.g. "John+3:16-18" or "John 3:16-18"
    translation : str  (default: web)
    """
    ref_param = request.args.get("ref", "").replace("+", " ").strip()
    if not ref_param:
        abort(400, description="Missing 'ref' query parameter.")

    translation_id_param = request.args.get("translation", DEFAULT_TRANSLATION)

    ranges = parse_ref(ref_param)
    if not ranges:
        abort(400, description=f"Could not parse reference '{ref_param}'.")

    with get_db() as conn:
        translation = _translation_or_404(conn, translation_id_param)
        verses = get_verses_for_ranges(conn, translation["id"], ranges)

    if verses is None or len(verses) == 0:
        abort(404, description="Passage not found.")

    verse_dicts = [_verse_dict(v) for v in verses]
    text = " ".join(v["text"] for v in verse_dicts)
    ref_display = _normalize_ref(ranges)

    return _json({
        "reference": ref_display,
        "verses": verse_dicts,
        "text": text,
        "translation_id": translation["identifier"],
        "translation_name": translation["name"],
        "translation_note": translation.get("license", ""),
    })


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(400)
def bad_request(e):
    return _json({"error": str(e.description)}, 400)


@app.errorhandler(404)
def not_found(e):
    return _json({"error": str(e.description)}, 404)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
