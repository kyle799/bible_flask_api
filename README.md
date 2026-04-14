# bible_flask_api

A simple Flask/SQLite Bible REST API inspired by [seven1m/bible_api](https://github.com/seven1m/bible_api).

Includes a web reader at `/bible` and JSON endpoints for verses, passages, and translations.

---

## Quickstart (Docker)

The default setup ships with **WEB** (World English Bible), **KJV** (King James Version), and **ASV** (American Standard Version). WEB is the default translation.

```bash
git clone https://github.com/kyle799/bible_flask_api
cd bible_flask_api

# Get the Bible source files
git clone https://github.com/seven1m/open-bibles bibles

# Build the image, import the three default translations, start the API
docker compose build
docker compose run --rm importer --bibles-dir /bibles --only eng-web,eng-kjv,eng-asv
docker compose up -d
```

The API is now running at `http://localhost:5002`.
Open the web reader at `http://localhost:5002/bible`.

---

## Manual setup (no Docker)

```bash
pip install -r requirements.txt

git clone https://github.com/seven1m/open-bibles bibles

python import_all.py --bibles-dir bibles --only eng-web,eng-kjv,eng-asv

python app.py
```

The API listens on `http://localhost:5000` by default.

---

## Endpoints

### `GET /bible`

Web reader UI. Supports URL params for bookmarkable passages:

```
/bible?ref=John+3&translation=kjv
```

---

### `GET /translations`

Returns all available translations.

```json
{
  "translations": [
    { "identifier": "web", "name": "World English Bible", "language": "English", "language_code": "eng", "license": "Public Domain" },
    { "identifier": "kjv", "name": "King James Version",  "language": "English", "language_code": "eng", "license": "Public Domain" },
    { "identifier": "asv", "name": "American Standard Version (1901)", "language": "English", "language_code": "eng", "license": "Public Domain" }
  ]
}
```

---

### `GET /verse/<book>/<chapter>/<verse>`

Fetch a single verse. `book` accepts full names or common abbreviations (case-insensitive).

| Query param   | Default | Description            |
|---------------|---------|------------------------|
| `translation` | `web`   | Translation identifier |

```
GET /verse/John/3/16
GET /verse/John/3/16?translation=kjv
GET /verse/Ps/23/1
```

```json
{
  "reference": "John 3:16",
  "verses": [
    { "book_id": "JHN", "book_name": "John", "chapter": 3, "verse": 16, "text": "For God so loved the world..." }
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

| Query param   | Default | Description                                       |
|---------------|---------|---------------------------------------------------|
| `ref`         | —       | Reference string (spaces or `+` as word separator)|
| `translation` | `web`   | Translation identifier                            |

Supported formats:

```
GET /passage?ref=John+3:16              # single verse
GET /passage?ref=John+3:16-18           # verse range
GET /passage?ref=John+3:16-4:1          # cross-chapter range
GET /passage?ref=John+3                 # whole chapter
GET /passage?ref=Psalm+23&translation=kjv
```

```json
{
  "reference": "JHN 3:16-18",
  "verses": [
    { "book_id": "JHN", "book_name": "John", "chapter": 3, "verse": 16, "text": "..." },
    { "book_id": "JHN", "book_name": "John", "chapter": 3, "verse": 17, "text": "..." },
    { "book_id": "JHN", "book_name": "John", "chapter": 3, "verse": 18, "text": "..." }
  ],
  "text": "For God so loved the world...",
  "translation_id": "web",
  "translation_name": "World English Bible",
  "translation_note": "Public Domain"
}
```

---

## Adding more translations

All 43 open-licensed translations from [seven1m/open-bibles](https://github.com/seven1m/open-bibles) are supported (OSIS, USFX, and Zefania XML formats). To add them:

```bash
# Add a single translation
docker compose run --rm importer --bibles-dir /bibles --only eng-darby

# Add all available translations
docker compose run --rm importer --bibles-dir /bibles

# Reimport (overwrite existing)
docker compose run --rm importer --bibles-dir /bibles --only eng-web --overwrite
```

Or without Docker:

```bash
python import_all.py --bibles-dir bibles --only eng-darby
python import_all.py --bibles-dir bibles   # all translations
```
