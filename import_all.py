#!/usr/bin/env python3
"""
Import all Bible translations from a directory of XML files.

Reads translation metadata from the README.md table in the bibles directory,
then imports each file using the appropriate parser.

Usage
-----
  python import_all.py                         # uses ./bibles/
  python import_all.py --bibles-dir ./bibles
  python import_all.py --overwrite             # reimport all
  python import_all.py --only eng-kjv,eng-web  # subset by filename stem
"""

import argparse
import re
import sys
from pathlib import Path

from import_bible import (
    detect_format,
    import_translation,
    parse_osis,
    parse_usfx,
    parse_zefania,
)

# Language code fixes matching the reference project
LANG_CODE_FIXES = {
    "chi": "zh-tw",
}


def parse_readme_table(readme_path: Path) -> list[dict]:
    """Parse the Markdown table in README.md and return a list of translation dicts."""
    text = readme_path.read_text(encoding="utf-8")
    rows = [line for line in text.splitlines() if re.match(r"^\s*\|", line)]
    if not rows:
        return []

    # First row = headers (filter truly empty ones at edges)
    headers = [h.strip().lower() for h in rows[0].split("|") if h.strip()]
    translations = []
    for row in rows[2:]:  # skip header and separator
        # Strip edge empty cells caused by leading/trailing |, preserve middle empties
        cells = [c.strip() for c in row.split("|")]
        # Drop first and last if empty (they come from the surrounding pipes)
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        if len(cells) < len(headers):
            continue
        entry = dict(zip(headers, cells))
        translations.append(entry)
    return translations


def derive_ids(filename: str, abbrev: str) -> tuple[str, str]:
    """Return (language_code, identifier) from filename and abbrev."""
    stem = filename.split(".")[0]          # e.g. "chi-cuv-simp"
    parts = stem.split("-")
    language_code = parts[0]
    language_code = LANG_CODE_FIXES.get(language_code, language_code)

    # Always derive identifier from the non-language-code parts of the filename
    # to avoid collisions (e.g. chi-cuv vs chi-cuv-simp both have Abbrev "CUV")
    identifier = "-".join(parts[1:]) if len(parts) > 1 else stem

    return language_code, identifier


def main() -> None:
    parser = argparse.ArgumentParser(description="Import all open-bibles translations.")
    parser.add_argument("--bibles-dir", default="bibles", help="Directory containing XML files (default: bibles/)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing translations")
    parser.add_argument("--only", help="Comma-separated list of filename stems to import (e.g. eng-kjv,eng-web)")
    args = parser.parse_args()

    bibles_dir = Path(args.bibles_dir)
    if not bibles_dir.is_dir():
        print(f"Error: directory not found: {bibles_dir}", file=sys.stderr)
        sys.exit(1)

    readme = bibles_dir / "README.md"
    if not readme.exists():
        print(f"Error: README.md not found in {bibles_dir}", file=sys.stderr)
        sys.exit(1)

    only_set = set(args.only.split(",")) if args.only else None

    translations = parse_readme_table(readme)
    if not translations:
        print("Could not parse README.md table.", file=sys.stderr)
        sys.exit(1)

    total = 0
    skipped = 0

    for t in translations:
        filename = t.get("filename", "")
        if not filename:
            continue

        stem = filename.split(".")[0]
        if only_set and stem not in only_set:
            continue

        path = bibles_dir / filename
        if not path.exists():
            print(f"[MISSING] {filename}")
            skipped += 1
            continue

        abbrev = t.get("abbrev", "").strip()
        version = t.get("version", "").strip()
        language = t.get("language", "").strip()
        license_text = t.get("license", "").strip()

        language_code, identifier = derive_ids(filename, abbrev)

        fmt = detect_format(path)
        print(f"\n[{fmt.upper():7s}] {filename}")
        print(f"           id={identifier!r}  name={version!r}  lang={language_code}")

        try:
            if fmt == "osis":
                verses = parse_osis(path)
            elif fmt == "usfx":
                verses = parse_usfx(path)
            elif fmt == "zefania":
                verses = parse_zefania(path)
            else:
                print("  skipping (unsupported format)")
                skipped += 1
                continue

            if not verses:
                print("  WARNING: no verses parsed — skipping")
                skipped += 1
                continue

            import_translation(
                verses=verses,
                identifier=identifier,
                name=version or identifier.upper(),
                language=language,
                language_code=language_code,
                license_text=license_text,
                overwrite=args.overwrite,
            )
            total += 1

        except Exception as exc:
            print(f"  ERROR: {exc}")
            skipped += 1

    print(f"\nDone. Imported: {total}  Skipped/errors: {skipped}")


if __name__ == "__main__":
    main()
