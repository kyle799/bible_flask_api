# bible_flask_api

A simple Flask/SQLite Bible REST API inspired by [seven1m/bible_api](https://github.com/seven1m/bible_api).

## Setup

```bash
pip install -r requirements.txt
```

## Importing Bible data

The importer accepts **OSIS XML** files (the format used by [seven1m/open-bibles](https://github.com/seven1m/open-bibles)) and **CSV** files.

### OSIS XML (recommended)

```bash
# Clone the open-bibles data
git clone https://github.com/seven1m/open-bibles bibles

# Import a translation (identifier is auto-detected from filename)
python import_bible.py bibles/eng-web.osis.xml \
  --name "World English Bible" \
  --license "Public Domain"

# Import another translation
python import_bible.py bibles/eng-kjv.osis.xml \
  --name "King James Version" \
  --license "Public Domain"
```

### CSV

The CSV must have columns: `book_id, book, chapter, verse, text`

```bash
python import_bible.py data/web.csv \
  --id web \
  --name "World English Bible" \
  --language English \
  --language-code eng
```

### Overwrite existing data

```bash
python import_bible.py bibles/eng-web.osis.xml --overwrite
```

## Running the server

```bash
python app.py
# or
flask --app app run
```

The API listens on `http://localhost:5000` by default.

Set `DATABASE_PATH` to use a custom SQLite file location (default: `bible.db`).

---

## Endpoints

### `GET /translations`

Returns all available translations.

```json
{
  "translations": [
    {
      "identifier": "web",
      "name": "World English Bible",
      "language": "English",
      "language_code": "eng",
      "license": "Public Domain"
    }
  ]
}
```

---

### `GET /verse/<book>/<chapter>/<verse>`

Fetch a single verse. `book` accepts full names or abbreviations (case-insensitive).

| Query param   | Default | Description                     |
|---------------|---------|---------------------------------|
| `translation` | `web`   | Translation identifier          |

**Example:** `GET /verse/John/3/16`

```json
{
  "reference": "John 3:16",
  "verses": [
    {
      "book_id": "JHN",
      "book_name": "John",
      "chapter": 3,
      "verse": 16,
      "text": "For God so loved the world..."
    }
  ],
  "text": "For God so loved the world...",
  "translation_id": "web",
  "translation_name": "World English Bible",
  "translation_note": "Public Domain"
}
```

---

### `GET /passage`

Fetch a passage by reference string.

| Query param   | Default | Description                                         |
|---------------|---------|-----------------------------------------------------|
| `ref`         | —       | Reference e.g. `John+3:16-18` or `John+3:16-4:1`   |
| `translation` | `web`   | Translation identifier                              |

Supported reference formats:
- `John 3:16` — single verse
- `John 3:16-18` — verse range, same chapter
- `John 3:16-4:1` — cross-chapter range
- `John 3` — whole chapter

**Example:** `GET /passage?ref=John+3:16-18&translation=web`

```json
{
  "reference": "JHN 3:16-18",
  "verses": [...],
  "text": "For God so loved the world...",
  "translation_id": "web",
  "translation_name": "World English Bible",
  "translation_note": "Public Domain"
}
```
