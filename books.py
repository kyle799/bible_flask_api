# Mapping from common book names/abbreviations to canonical book IDs (OSIS/USFM style)
# Keys are lowercase; values are uppercase IDs used in the database.

BOOK_MAP: dict[str, str] = {
    # Old Testament
    "genesis": "GEN", "gen": "GEN",
    "exodus": "EXO", "exo": "EXO", "exod": "EXO", "ex": "EXO",
    "leviticus": "LEV", "lev": "LEV",
    "numbers": "NUM", "num": "NUM",
    "deuteronomy": "DEU", "deu": "DEU", "deut": "DEU",
    "joshua": "JOS", "jos": "JOS", "josh": "JOS",
    "judges": "JDG", "jdg": "JDG", "judg": "JDG",
    "ruth": "RUT", "rut": "RUT",
    "1samuel": "1SA", "1sa": "1SA", "1sam": "1SA", "1 samuel": "1SA", "1 sam": "1SA",
    "2samuel": "2SA", "2sa": "2SA", "2sam": "2SA", "2 samuel": "2SA", "2 sam": "2SA",
    "1kings": "1KI", "1ki": "1KI", "1kgs": "1KI", "1 kings": "1KI", "1 kgs": "1KI",
    "2kings": "2KI", "2ki": "2KI", "2kgs": "2KI", "2 kings": "2KI", "2 kgs": "2KI",
    "1chronicles": "1CH", "1ch": "1CH", "1chr": "1CH", "1 chronicles": "1CH", "1 chr": "1CH",
    "2chronicles": "2CH", "2ch": "2CH", "2chr": "2CH", "2 chronicles": "2CH", "2 chr": "2CH",
    "ezra": "EZR", "ezr": "EZR",
    "nehemiah": "NEH", "neh": "NEH",
    "esther": "EST", "est": "EST", "esth": "EST",
    "job": "JOB",
    "psalms": "PSA", "psalm": "PSA", "psa": "PSA", "ps": "PSA",
    "proverbs": "PRO", "pro": "PRO", "prov": "PRO",
    "ecclesiastes": "ECC", "ecc": "ECC", "eccl": "ECC", "qoh": "ECC",
    "songofsolomon": "SNG", "song": "SNG", "sng": "SNG", "sos": "SNG", "canticles": "SNG",
    "isaiah": "ISA", "isa": "ISA",
    "jeremiah": "JER", "jer": "JER",
    "lamentations": "LAM", "lam": "LAM",
    "ezekiel": "EZK", "ezk": "EZK", "ezek": "EZK",
    "daniel": "DAN", "dan": "DAN",
    "hosea": "HOS", "hos": "HOS",
    "joel": "JOL", "jol": "JOL",
    "amos": "AMO", "amo": "AMO",
    "obadiah": "OBA", "oba": "OBA", "obad": "OBA",
    "jonah": "JON", "jon": "JON",
    "micah": "MIC", "mic": "MIC",
    "nahum": "NAM", "nam": "NAM",
    "habakkuk": "HAB", "hab": "HAB",
    "zephaniah": "ZEP", "zep": "ZEP", "zeph": "ZEP",
    "haggai": "HAG", "hag": "HAG",
    "zechariah": "ZEC", "zec": "ZEC", "zech": "ZEC",
    "malachi": "MAL", "mal": "MAL",
    # New Testament
    "matthew": "MAT", "mat": "MAT", "matt": "MAT", "mt": "MAT",
    "mark": "MRK", "mrk": "MRK", "mk": "MRK", "mar": "MRK",
    "luke": "LUK", "luk": "LUK", "lk": "LUK",
    "john": "JHN", "jhn": "JHN", "jn": "JHN",
    "acts": "ACT", "act": "ACT",
    "romans": "ROM", "rom": "ROM",
    "1corinthians": "1CO", "1co": "1CO", "1cor": "1CO", "1 corinthians": "1CO", "1 cor": "1CO",
    "2corinthians": "2CO", "2co": "2CO", "2cor": "2CO", "2 corinthians": "2CO", "2 cor": "2CO",
    "galatians": "GAL", "gal": "GAL",
    "ephesians": "EPH", "eph": "EPH",
    "philippians": "PHP", "php": "PHP", "phil": "PHP",
    "colossians": "COL", "col": "COL",
    "1thessalonians": "1TH", "1th": "1TH", "1thess": "1TH", "1 thessalonians": "1TH", "1 thess": "1TH",
    "2thessalonians": "2TH", "2th": "2TH", "2thess": "2TH", "2 thessalonians": "2TH", "2 thess": "2TH",
    "1timothy": "1TI", "1ti": "1TI", "1tim": "1TI", "1 timothy": "1TI", "1 tim": "1TI",
    "2timothy": "2TI", "2ti": "2TI", "2tim": "2TI", "2 timothy": "2TI", "2 tim": "2TI",
    "titus": "TIT", "tit": "TIT",
    "philemon": "PHM", "phm": "PHM", "phlm": "PHM",
    "hebrews": "HEB", "heb": "HEB",
    "james": "JAS", "jas": "JAS",
    "1peter": "1PE", "1pe": "1PE", "1pet": "1PE", "1 peter": "1PE", "1 pet": "1PE",
    "2peter": "2PE", "2pe": "2PE", "2pet": "2PE", "2 peter": "2PE", "2 pet": "2PE",
    "1john": "1JN", "1jn": "1JN", "1jo": "1JN", "1 john": "1JN",
    "2john": "2JN", "2jn": "2JN", "2jo": "2JN", "2 john": "2JN",
    "3john": "3JN", "3jn": "3JN", "3jo": "3JN", "3 john": "3JN",
    "jude": "JUD", "jud": "JUD",
    "revelation": "REV", "rev": "REV", "revelations": "REV",
}

# Books with only one chapter (verse numbers may be omitted in chapter position)
SINGLE_CHAPTER_BOOKS = {"OBA", "PHM", "2JN", "3JN", "JUD"}

# Ordered list of canonical Protestant book IDs
BOOK_ORDER: list[str] = [
    "GEN", "EXO", "LEV", "NUM", "DEU", "JOS", "JDG", "RUT",
    "1SA", "2SA", "1KI", "2KI", "1CH", "2CH", "EZR", "NEH", "EST",
    "JOB", "PSA", "PRO", "ECC", "SNG", "ISA", "JER", "LAM", "EZK",
    "DAN", "HOS", "JOL", "AMO", "OBA", "JON", "MIC", "NAM", "HAB",
    "ZEP", "HAG", "ZEC", "MAL",
    "MAT", "MRK", "LUK", "JHN", "ACT", "ROM",
    "1CO", "2CO", "GAL", "EPH", "PHP", "COL",
    "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS",
    "1PE", "2PE", "1JN", "2JN", "3JN", "JUD", "REV",
]


def resolve_book(name: str) -> str | None:
    """Return canonical book ID from a human-readable name, or None if unknown."""
    key = name.lower().replace(".", "").strip()
    return BOOK_MAP.get(key)
