import re
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from app import get_current_user, get_db


bp = Blueprint("ratings", __name__)

RATING_SIGNALS = {1: -1.0, 2: -0.5, 3: 0.0, 4: 0.5, 5: 1.0}
SHRINKAGE_K = 3.0
LONE_NEGATIVE_FACTOR = 0.5
MAX_REVIEW_LEN = 2000
MAX_TAGS, MAX_GENRES = 25, 12

GENRE_RE = re.compile(r"^[A-Z0-9_]{1,20}$")
SCHEMA = """
CREATE TABLE IF NOT EXISTS titles (
  title_key TEXT PRIMARY KEY, media_type TEXT NOT NULL CHECK (media_type IN ('movie','tv')),
  tmdb_id INTEGER NOT NULL, country TEXT, language TEXT, year INTEGER, updated_at TEXT);
CREATE TABLE IF NOT EXISTS title_genres (
  title_key TEXT NOT NULL REFERENCES titles(title_key) ON DELETE CASCADE,
  genre_key TEXT NOT NULL, weight REAL NOT NULL CHECK (weight BETWEEN 0 AND 1),
  PRIMARY KEY (title_key, genre_key));
CREATE TABLE IF NOT EXISTS tags (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS title_tags (
  title_key TEXT NOT NULL REFERENCES titles(title_key) ON DELETE CASCADE,
  tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  weight REAL NOT NULL DEFAULT 1.0, PRIMARY KEY (title_key, tag_id));
CREATE TABLE IF NOT EXISTS user_ratings (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title_key TEXT NOT NULL REFERENCES titles(title_key) ON DELETE CASCADE,
  rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
  PRIMARY KEY (user_id, title_key));
CREATE INDEX IF NOT EXISTS idx_ratings_title ON user_ratings(title_key);
CREATE TABLE IF NOT EXISTS user_reviews (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title_key TEXT NOT NULL REFERENCES titles(title_key) ON DELETE CASCADE,
  body TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
  PRIMARY KEY (user_id, title_key));
CREATE INDEX IF NOT EXISTS idx_reviews_title ON user_reviews(title_key, updated_at);
CREATE TABLE IF NOT EXISTS user_genre_preferences (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  genre_key TEXT NOT NULL, weight REAL NOT NULL, PRIMARY KEY (user_id, genre_key));
CREATE TABLE IF NOT EXISTS user_tag_preferences (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  weight REAL NOT NULL, PRIMARY KEY (user_id, tag_id));
"""


def init_ratings_schema(db):
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(SCHEMA)
    db.commit()


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def err(msg, code):
    return jsonify(success=False, message=msg), code


def title_key(media, tmdb_id):
    return f"{media}_{tmdb_id}" if media in ("movie", "tv") and tmdb_id > 0 else None


def clean_tag(value):
    value = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 '&-]", "", str(value).lower())).strip()
    return value if 2 <= len(value) <= 40 else None


def clean_text(value):
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", str(value)).replace("\r\n", "\n")
    return re.sub(r"\n{3,}", "\n\n", value).strip()


def save_title_meta(db, key, media, tmdb_id, meta):
    meta = meta if isinstance(meta, dict) else {}
    country = str(meta.get("country") or "")[:2].upper() or None
    language = str(meta.get("language") or "")[:3].lower() or None
    year_value = meta.get("year")
    year = year_value if type(year_value) is int and 1870 < year_value < 2200 else None
    db.execute(
        """INSERT INTO titles(title_key,media_type,tmdb_id,country,language,year,updated_at)
           VALUES(?,?,?,?,?,?,?) ON CONFLICT(title_key) DO UPDATE SET
           country=COALESCE(excluded.country,country),
           language=COALESCE(excluded.language,language),
           year=COALESCE(excluded.year,year), updated_at=excluded.updated_at""",
        (key, media, tmdb_id, country, language, year, now()),
    )

    raw_genres = meta.get("genres")
    genres = []
    if isinstance(raw_genres, list):
        for genre in raw_genres[:MAX_GENRES]:
            if isinstance(genre, str) and GENRE_RE.fullmatch(genre) and genre not in genres:
                genres.append(genre)
    if genres:
        db.execute("DELETE FROM title_genres WHERE title_key=?", (key,))
        db.executemany(
            "INSERT INTO title_genres VALUES(?,?,?)",
            [(key, genre, round(max(0.3, 1.0 - 0.2 * i), 2)) for i, genre in enumerate(genres)],
        )

    raw_tags = meta.get("tags")
    tags = []
    if isinstance(raw_tags, list):
        for tag in raw_tags[:MAX_TAGS * 2]:
            cleaned = clean_tag(tag) if isinstance(tag, str) else None
            if cleaned and cleaned not in tags:
                tags.append(cleaned)
    for tag in tags[:MAX_TAGS]:
        db.execute("INSERT OR IGNORE INTO tags(name) VALUES(?)", (tag,))
        tag_id = db.execute("SELECT id FROM tags WHERE name=?", (tag,)).fetchone()[0]
        db.execute("INSERT OR REPLACE INTO title_tags VALUES(?,?,1.0)", (key, tag_id))


def _aggregate(rows):
    grouped = {}
    for name, rating, weight in rows:
        grouped.setdefault(name, []).append((RATING_SIGNALS[rating], weight))
    output = {}
    for name, items in grouped.items():
        negative_count = sum(1 for signal, _ in items if signal < 0)
        numerator = denominator = 0.0
        for signal, weight in items:
            if signal < 0 and negative_count < 2:
                signal *= LONE_NEGATIVE_FACTOR
            numerator += signal * weight
            denominator += weight
        output[name] = max(-1.0, min(1.0, round(numerator / (denominator + SHRINKAGE_K), 4)))
    return output


def recompute_preferences(db, user_id):
    genres = _aggregate(
        (row["genre_key"], row["rating"], row["weight"])
        for row in db.execute(
            """SELECT tg.genre_key, r.rating, tg.weight FROM user_ratings r
               JOIN title_genres tg ON tg.title_key = r.title_key WHERE r.user_id=?""",
            (user_id,),
        )
    )
    tags = _aggregate(
        (row["tag_id"], row["rating"], row["weight"])
        for row in db.execute(
            """SELECT tt.tag_id, r.rating, tt.weight FROM user_ratings r
               JOIN title_tags tt ON tt.title_key = r.title_key WHERE r.user_id=?""",
            (user_id,),
        )
    )
    db.execute("DELETE FROM user_genre_preferences WHERE user_id=?", (user_id,))
    db.execute("DELETE FROM user_tag_preferences WHERE user_id=?", (user_id,))
    db.executemany(
        "INSERT INTO user_genre_preferences VALUES(?,?,?)",
        [(user_id, key, weight) for key, weight in genres.items() if abs(weight) >= 0.01],
    )
    db.executemany(
        "INSERT INTO user_tag_preferences VALUES(?,?,?)",
        [(user_id, key, weight) for key, weight in tags.items() if abs(weight) >= 0.01],
    )
    return read_preferences(db, user_id)


def read_preferences(db, user_id):
    genres = {
        row["genre_key"]: row["weight"]
        for row in db.execute(
            "SELECT genre_key, weight FROM user_genre_preferences WHERE user_id=?", (user_id,)
        )
    }
    tags = {
        row["name"]: row["weight"]
        for row in db.execute(
            """SELECT t.name, p.weight FROM user_tag_preferences p JOIN tags t ON t.id=p.tag_id
               WHERE p.user_id=? ORDER BY ABS(p.weight) DESC LIMIT 80""",
            (user_id,),
        )
    }
    return {"genres": genres, "tags": tags}


def community(db, key):
    row = db.execute(
        "SELECT AVG(rating) AS average, COUNT(*) AS count FROM user_ratings WHERE title_key=?",
        (key,),
    ).fetchone()
    return {
        "average": round(row["average"], 2) if row["count"] else None,
        "count": row["count"],
    }


@bp.put("/api/ratings/<media>/<int:tmdb_id>")
def put_rating(media, tmdb_id):
    user = get_current_user()
    if not user:
        return err("Authentication required.", 401)
    key = title_key(media, tmdb_id)
    body = request.get_json(silent=True) or {}
    rating = body.get("rating")
    if not key:
        return err("Invalid title.", 400)
    if type(rating) is not int or rating not in RATING_SIGNALS:
        return err("Rating must be an integer from 1 to 5.", 400)
    db = get_db()
    with db:
        save_title_meta(db, key, media, tmdb_id, body.get("meta"))
        db.execute(
            """INSERT INTO user_ratings(user_id,title_key,rating,created_at,updated_at)
               VALUES(?,?,?,?,?) ON CONFLICT(user_id,title_key)
               DO UPDATE SET rating=excluded.rating, updated_at=excluded.updated_at""",
            (user["id"], key, rating, now(), now()),
        )
        preferences = recompute_preferences(db, user["id"])
    return jsonify(
        success=True, rating=rating, community=community(db, key), preferences=preferences
    )


@bp.delete("/api/ratings/<media>/<int:tmdb_id>")
def delete_rating(media, tmdb_id):
    user = get_current_user()
    if not user:
        return err("Authentication required.", 401)
    key = title_key(media, tmdb_id)
    if not key:
        return err("Invalid title.", 400)
    db = get_db()
    with db:
        db.execute(
            "DELETE FROM user_ratings WHERE user_id=? AND title_key=?", (user["id"], key)
        )
        preferences = recompute_preferences(db, user["id"])
    return jsonify(
        success=True, rating=None, community=community(db, key), preferences=preferences
    )


@bp.get("/api/ratings/mine")
def my_ratings():
    user = get_current_user()
    if not user:
        return err("Authentication required.", 401)
    rows = get_db().execute(
        "SELECT title_key, rating FROM user_ratings WHERE user_id=?", (user["id"],)
    )
    return jsonify(success=True, ratings={row["title_key"]: row["rating"] for row in rows})


@bp.get("/api/me/preferences")
def my_preferences():
    user = get_current_user()
    if not user:
        return err("Authentication required.", 401)
    return jsonify(success=True, preferences=read_preferences(get_db(), user["id"]))


@bp.get("/api/titles/<media>/<int:tmdb_id>/ratings")
def title_ratings(media, tmdb_id):
    key = title_key(media, tmdb_id)
    if not key:
        return err("Invalid title.", 400)
    db, user = get_db(), get_current_user()
    mine = None
    if user:
        rating = db.execute(
            "SELECT rating FROM user_ratings WHERE user_id=? AND title_key=?",
            (user["id"], key),
        ).fetchone()
        review = db.execute(
            "SELECT body FROM user_reviews WHERE user_id=? AND title_key=?",
            (user["id"], key),
        ).fetchone()
        mine = {
            "rating": rating["rating"] if rating else None,
            "review": review["body"] if review else None,
        }
    return jsonify(success=True, community=community(db, key), mine=mine)


@bp.post("/api/titles/ratings/batch")
def community_batch():
    keys = (request.get_json(silent=True) or {}).get("keys")
    if not isinstance(keys, list):
        return err("keys required.", 400)
    db, output = get_db(), {}
    for key in keys[:30]:
        match = re.fullmatch(r"(movie|tv)_(\d{1,9})", key) if isinstance(key, str) else None
        if match:
            output[key] = community(db, key)
    return jsonify(success=True, communities=output)


@bp.get("/api/titles/<media>/<int:tmdb_id>/reviews")
def list_reviews(media, tmdb_id):
    key = title_key(media, tmdb_id)
    if not key:
        return err("Invalid title.", 400)
    limit = max(1, min(request.args.get("limit", 5, type=int), 20))
    offset = max(0, request.args.get("offset", 0, type=int))
    db, user = get_db(), get_current_user()
    total = db.execute(
        "SELECT COUNT(*) FROM user_reviews WHERE title_key=?", (key,)
    ).fetchone()[0]
    rows = db.execute(
        """SELECT v.user_id, u.username, v.body, v.created_at, r.rating
           FROM user_reviews v JOIN users u ON u.id=v.user_id
           LEFT JOIN user_ratings r ON r.user_id=v.user_id AND r.title_key=v.title_key
           WHERE v.title_key=? ORDER BY v.updated_at DESC LIMIT ? OFFSET ?""",
        (key, limit, offset),
    ).fetchall()
    reviews = [
        {
            "username": row["username"],
            "rating": row["rating"],
            "body": row["body"],
            "created_at": row["created_at"],
            "mine": bool(user and user["id"] == row["user_id"]),
        }
        for row in rows
    ]
    return jsonify(
        success=True,
        reviews=reviews,
        total=total,
        has_more=offset + len(rows) < total,
    )


@bp.put("/api/reviews/<media>/<int:tmdb_id>")
def put_review(media, tmdb_id):
    user = get_current_user()
    if not user:
        return err("Authentication required.", 401)
    key = title_key(media, tmdb_id)
    body = (request.get_json(silent=True) or {}).get("body")
    if not key:
        return err("Invalid title.", 400)
    if not isinstance(body, str):
        return err("Review text required.", 400)
    body = clean_text(body)
    if not 1 <= len(body) <= MAX_REVIEW_LEN:
        return err(f"Review must be 1-{MAX_REVIEW_LEN} characters.", 400)
    db = get_db()
    with db:
        db.execute(
            """INSERT OR IGNORE INTO titles(title_key,media_type,tmdb_id,updated_at)
               VALUES(?,?,?,?)""",
            (key, media, tmdb_id, now()),
        )
        db.execute(
            """INSERT INTO user_reviews(user_id,title_key,body,created_at,updated_at)
               VALUES(?,?,?,?,?) ON CONFLICT(user_id,title_key)
               DO UPDATE SET body=excluded.body, updated_at=excluded.updated_at""",
            (user["id"], key, body, now(), now()),
        )
    return jsonify(success=True, body=body)


@bp.delete("/api/reviews/<media>/<int:tmdb_id>")
def delete_review(media, tmdb_id):
    user = get_current_user()
    if not user:
        return err("Authentication required.", 401)
    key = title_key(media, tmdb_id)
    if not key:
        return err("Invalid title.", 400)
    db = get_db()
    with db:
        db.execute(
            "DELETE FROM user_reviews WHERE user_id=? AND title_key=?", (user["id"], key)
        )
    return jsonify(success=True)
