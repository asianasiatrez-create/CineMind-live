import os
import re
import json
import sqlite3
import hashlib
import hmac
import base64
import time
from datetime import date, timedelta
from functools import wraps

import requests
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

TMDB_API_KEY = (os.environ.get("TMDB_API_KEY") or "").strip().strip('"').strip("'")
GROQ_API_KEY = (os.environ.get("GROQ_API_KEY") or "").strip().strip('"').strip("'")
OMDB_API_KEY = (os.environ.get("OMDB_API_KEY") or "").strip().strip('"').strip("'")
DB_NAME = os.environ.get("CINEMIND_DB", "cinemind.db")
TMDB = "https://api.themoviedb.org/3"
IMG = "https://image.tmdb.org/t/p"

TOKEN_MAX_AGE = 60 * 60 * 24 * 30

GENRES = {
    "action": 28, "adventure": 12, "animation": 16, "comedy": 35, "crime": 80,
    "documentary": 99, "documentaries": 99, "drama": 18, "family": 10751,
    "kids": 10751, "kids & family": 10751, "fantasy": 14, "history": 36,
    "horror": 27, "music": 10402, "mystery": 9648, "romance": 10749,
    "sci-fi": 878, "science fiction": 878, "thriller": 53, "war": 10752, "western": 37,
}
GENRE_ID_TO_NAME = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Kids & Family", 14: "Fantasy",
    36: "History", 27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance",
    878: "Sci-Fi", 53: "Thriller", 10752: "War", 37: "Western",
    10759: "Action & Adventure", 10762: "Kids", 10765: "Sci-Fi & Fantasy", 10768: "War & Politics",
}
MOVIE_TO_TV = {
    "28": "10759", "12": "10759", "16": "16", "35": "35", "80": "80", "99": "99",
    "18": "18", "10751": "10751|10762", "14": "10765", "27": "9648", "9648": "9648",
    "10749": "18", "878": "10765", "53": "9648|80", "10752": "10768", "37": "37",
}
SPECIAL_CATEGORIES = ["bl", "boys love", "girls love", "gl", "anime", "kids", "sports", "documentary"]
GENRE_LIST = ", ".join(list(GENRES.keys()) + SPECIAL_CATEGORIES)

COUNTRY_DEFAULT_GENRES = {
    "PH": ["drama", "romance", "comedy", "horror"], "KR": ["drama", "thriller", "romance", "action"],
    "TH": ["horror", "romance", "action", "comedy"], "JP": ["animation", "fantasy", "sci-fi", "drama"],
    "CN": ["drama", "fantasy", "action", "animation"], "TW": ["romance", "drama", "comedy"],
    "IN": ["action", "drama", "romance", "comedy"], "ES": ["thriller", "crime", "drama"],
    "FR": ["drama", "romance", "comedy"], "GB": ["drama", "crime", "mystery"],
    "US": ["action", "sci-fi", "comedy", "drama"],
}

PORN_BLOCK_WORDS = [
    "porn", "porno", "pornographic", "xxx", "erotic", "erotica", "hentai", "jav",
    "av idol", "sex tape", "playboy", "penthouse", "stripper", "prostitute",
    "brothel", "bdsm", "fetish", "orgasm", "milf", "softcore", "pink film",
    "vivamax", "brazzers", "onlyfans", "nymphomaniac", "365 days", "fifty shades",
    "scorpio nights", "silip", "uhaw", "laman", "pamasahe", "selina's gold",
    "us x her", "bela luna", "kiskisan", "salitan", "lampas langit", "virgin forest",
    "kaliwaan", "purgatoryo", "doblado", "paupahan", "boy bastos", "palitan",
    "tag-init", "sugar baby", "tayuan", "haslers", "dilig", "kaluskos",
]
KNOWN_R18_TITLES = {
    "deadpool", "deadpool 2", "deadpool & wolverine", "logan", "joker", "parasite",
    "oldboy", "oppenheimer", "john wick", "saw", "hereditary", "midsommar",
    "the wolf of wall street", "pulp fiction", "fight club", "gone girl",
    "shutter island", "se7en", "american psycho", "saltburn", "the handmaiden",
    "squid game", "the boys", "euphoria", "game of thrones", "breaking bad",
    "dexter", "monster: the jeffrey dahmer story",
}

def _cat(rows):
    return [{"title": t, "media_type": m, "year": y, "why": w} for (t, m, y, w) in rows]

CURATED_SPECIAL_CATALOG = {
    "BL": _cat([
        ("KinnPorsche", "tv", 2022, "Hit Thai Boys' Love action-romance drama."),
        ("2gether: The Series", "tv", 2020, "Iconic Thai Boys' Love campus romance."),
        ("Bad Buddy", "tv", 2021, "Beloved Thai Boys' Love enemies-to-lovers series."),
        ("Semantic Error", "tv", 2022, "Acclaimed Korean Boys' Love campus romance."),
        ("Cherry Magic! Thirty Years of Virginity Can Make You a Wizard?!", "tv", 2020, "Japanese Boys' Love romantic comedy."),
        ("The Eighth Sense", "tv", 2023, "Emotional Korean Boys' Love drama."),
        ("I Told Sunset About You", "tv", 2020, "Acclaimed coming-of-age Thai BL drama."),
        ("Moonlight Chicken", "tv", 2023, "Award-winning Thai Boys' Love series."),
        ("Last Twilight", "tv", 2023, "Moving Thai BL romance series."),
        ("Young Royals", "tv", 2021, "Royal boarding school Boys' Love drama."),
        ("Heartstopper", "tv", 2022, "Sweet Boys' Love teen romance."),
        ("Red, White & Royal Blue", "movie", 2023, "Boys' Love romantic comedy film."),
        ("Your Name Engraved Herein", "movie", 2020, "Taiwanese Boys' Love romantic drama."),
    ]),
    "GL": _cat([
        ("GAP The Series", "tv", 2022, "Thai Girls' Love office romance."),
        ("The Secret of Us", "tv", 2024, "Thai Girls' Love romantic drama."),
        ("23.5", "tv", 2024, "Thai Girls' Love high school rom-com."),
        ("Pluto", "tv", 2024, "Thai Girls' Love mystery-romance."),
        ("Blank The Series", "tv", 2024, "Popular Thai Girls' Love romance."),
        ("Affair", "tv", 2024, "Trending Thai Girls' Love drama."),
        ("The Loyal Pin", "tv", 2024, "Period Thai Girls' Love romance."),
        ("Uranus 2324", "movie", 2024, "Sci-fi Thai Girls' Love movie."),
        ("The Handmaiden", "movie", 2016, "Korean Girls' Love psychological thriller."),
        ("Portrait of a Lady on Fire", "movie", 2019, "Girls' Love historical romance."),
        ("Carol", "movie", 2015, "Classic Girls' Love romantic drama."),
        ("Bottoms", "movie", 2023, "Queer Girls' Love comedy."),
    ]),
    "SPORTS": _cat([
        ("FIFA Uncovered", "tv", 2022, "Real-life FIFA football documentary series."),
        ("Formula 1: Drive to Survive", "tv", 2019, "Real-life Formula 1 racing series."),
        ("The Last Dance", "tv", 2020, "NBA championship documentary series."),
        ("Beckham", "tv", 2023, "Real-life football legend series."),
        ("WWE Raw", "tv", 1993, "Live-action pro wrestling show."),
        ("Mr. McMahon", "tv", 2024, "Real-life WWE docuseries."),
        ("Quarterback", "tv", 2023, "Real-life NFL series."),
        ("Rush", "movie", 2013, "Live-action Formula 1 drama."),
        ("Ford v Ferrari", "movie", 2019, "Live-action Le Mans racing drama."),
        ("Creed", "movie", 2015, "Live-action championship boxing film."),
        ("King Richard", "movie", 2021, "True story of Venus and Serena Williams."),
        ("Moneyball", "movie", 2011, "True-story baseball drama."),
        ("The Iron Claw", "movie", 2023, "True-story pro wrestling drama."),
    ]),
    "DOC": _cat([
        ("Conversations with a Killer: The Jeffrey Dahmer Tapes", "tv", 2022, "True-crime documentary series."),
        ("Night Stalker: The Hunt for a Serial Killer", "tv", 2021, "True-crime documentary series."),
        ("Don't F**k with Cats: Hunting an Internet Killer", "tv", 2019, "Investigative true-crime series."),
        ("Making a Murderer", "tv", 2015, "Landmark true-crime documentary series."),
        ("Our Planet", "tv", 2019, "Landmark nature documentary series."),
        ("The Tinder Swindler", "movie", 2022, "Investigative true-crime documentary."),
        ("American Murder: The Family Next Door", "movie", 2020, "True-crime documentary film."),
        ("Girl in the Picture", "movie", 2022, "True-crime mystery documentary."),
        ("13th", "movie", 2016, "Oscar-nominated historical documentary."),
    ]),
}

KNOWN_PLOT_PATTERNS = [
    {
        "patterns": ["boxing in toy story", "toy story boxing", "rock em sock em", "rock 'em sock 'em"],
        "must_have_any": ["toy story", "boxing"],
        "reply": "In Toy Story 2, there is a memorable boxing scene featuring the classic Rock 'Em Sock 'Em Robots inside Al's Toy Barn! Plus, Real Steel (2011) is the robot-boxing movie people often link to it.",
        "guesses": _cat([
            ("Toy Story", "movie", 1995, "The original Pixar classic."),
            ("Toy Story 2", "movie", 1999, "Features the Rock 'Em Sock 'Em Robots boxing scene."),
            ("Toy Story 3", "movie", 2010, "Woody and Buzz face Sunnyside Daycare."),
            ("Toy Story 4", "movie", 2019, "Road trip with Forky."),
            ("Real Steel", "movie", 2011, "Robot-boxing movie."),
        ]),
    },
    {
        "patterns": ["high pole", "tv tower", "radio tower", "two girls", "stuck on top", "climbs a tower", "stuck on a tower", "tall tower"],
        "must_have_any": ["pole", "tower", "stuck", "climb"],
        "reply": "You're likely thinking of 'Fall' (2022): two friends climb a 2,000-foot radio tower and get stranded. Here are similar survival thrillers:",
        "guesses": _cat([
            ("Fall", "movie", 2022, "Two friends trapped atop a tall radio tower."),
            ("47 Meters Down", "movie", 2017, "Sisters trapped in a shark cage."),
            ("The Shallows", "movie", 2016, "Surfer stranded near a great white."),
            ("127 Hours", "movie", 2010, "Climber trapped under a boulder."),
            ("Frozen", "movie", 2010, "Friends stuck on a ski chairlift."),
        ]),
    },
    {
        "patterns": ["poor family", "rich household", "rich family", "infiltrate", "wealthy family", "pose as tutor"],
        "must_have_any": ["poor", "rich", "infiltrate", "wealthy", "household"],
        "reply": "That sounds like 'Parasite' (2019). Here it is with similar class-divide thrillers:",
        "guesses": _cat([
            ("Parasite", "movie", 2019, "The Kim family infiltrates a wealthy household."),
            ("Saltburn", "movie", 2023, "A student infiltrates an aristocratic family."),
            ("The Handmaiden", "movie", 2016, "A con plot around a wealthy heiress."),
            ("Knives Out", "movie", 2019, "Mystery in a wealthy family."),
            ("Us", "movie", 2019, "Suspense about duality and privilege."),
        ]),
    },
    {
        "patterns": ["relives the same day", "same day over", "time loop", "repeating the same day", "every time he dies"],
        "must_have_any": ["relives", "loop", "same day", "repeating"],
        "reply": "That time-loop premise matches 'Groundhog Day', 'Palm Springs' and 'Edge of Tomorrow'.",
        "guesses": _cat([
            ("Groundhog Day", "movie", 1993, "The definitive time-loop movie."),
            ("Palm Springs", "movie", 2020, "Wedding guests stuck in a loop."),
            ("Edge of Tomorrow", "movie", 2014, "A soldier relives a battle each time he dies."),
            ("Happy Death Day", "movie", 2017, "Relive your murder until you solve it."),
            ("Source Code", "movie", 2011, "Relive an 8-minute train explosion."),
        ]),
    },
]

CURATED_KOREAN_ROMCOMS = _cat([
    ("Love Reset", "movie", 2023, "Couple on the verge of divorce both get amnesia."),
    ("20th Century Girl", "movie", 2022, "Nostalgic Korean teen romance."),
    ("My Sassy Girl", "movie", 2001, "The iconic Korean romantic comedy."),
    ("Business Proposal", "tv", 2022, "Blind date with the company CEO."),
    ("Lovely Runner", "tv", 2024, "Time-slip romantic comedy."),
    ("King the Land", "tv", 2023, "Charming Korean romantic comedy."),
])

def is_safe_non_porn(m):
    if not m or m.get("adult") is True:
        return False
    text = f"{m.get('title') or ''} {m.get('name') or ''} {m.get('original_title') or ''} {m.get('overview') or ''}".lower()
    return not any(bad in text for bad in PORN_BLOCK_WORDS)

def is_animated_or_cartoon(m):
    if not m:
        return False
    gids = m.get("genre_ids") or [x.get("id") for x in (m.get("genres") or []) if isinstance(x, dict)]
    if 16 in gids:
        return True
    text = f"{m.get('title') or ''} {m.get('name') or ''} {m.get('overview') or ''}".lower()
    return bool(re.search(r"\b(anime|animated|cartoon|pixar|dreamworks|studio ghibli|spongebob|looney tunes)\b", text))

def is_genuine_r18(m):
    if not m or not is_safe_non_porn(m):
        return False
    title_l = (m.get("title") or m.get("name") or "").lower().strip()
    if title_l in KNOWN_R18_TITLES:
        return True
    gids = m.get("genre_ids") or []
    overview = (m.get("overview") or "").lower()
    return bool(any(x in gids for x in (27, 80, 53, 99)) and re.search(
        r"\b(murder|serial killer|brutal|blood|gore|cartel|massacre|psychopath|torture|slasher|cannibal|dahmer)\b",
        f"{title_l} {overview}"))

def format_exact_genres(m, custom_badge=None):
    names = []
    if custom_badge:
        names.append(custom_badge)
    for x in (m.get("genres") or []):
        if isinstance(x, dict) and x.get("name") and x["name"] not in names:
            names.append(x["name"])
    for gid in (m.get("genre_ids") or []):
        label = GENRE_ID_TO_NAME.get(int(gid))
        if label and label not in names:
            names.append(label)
    lang = (m.get("original_language") or "").lower()
    if "Animation" in names and lang in ("ja", "ko", "zh") and "Anime" not in names:
        names.insert(0, "Anime")
    return names if names else ["Drama"]

def get_db_conn():
    conn = sqlite3.connect(DB_NAME, timeout=15.0)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    try:
        conn = get_db_conn()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            genres TEXT DEFAULT '[]',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        for sql in [
            "ALTER TABLE users ADD COLUMN genres TEXT DEFAULT '[]'",
            "ALTER TABLE users ADD COLUMN created_at TEXT"
        ]:
            try:
                c.execute(sql)
            except Exception:
                pass
        for table in ("watchlist", "favorites"):
            c.execute(f'''CREATE TABLE IF NOT EXISTS {table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                movie_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                poster TEXT,
                vote_average REAL,
                media_type TEXT DEFAULT 'movie',
                UNIQUE(username, movie_id),
                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE)''')
            try:
                c.execute(f"ALTER TABLE {table} ADD COLUMN media_type TEXT DEFAULT 'movie'")
            except Exception:
                pass
        c.execute('''CREATE TABLE IF NOT EXISTS not_interested (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            movie_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            keywords TEXT DEFAULT '[]',
            UNIQUE(username, movie_id),
            FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE)''')
        c.execute('''CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            movie_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            action TEXT NOT NULL,
            vote_average REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE)''')
        conn.commit()
        conn.close()
    except Exception as e:
        print("init_db failed:", e)

init_db()

GENRE_KEY_RE = re.compile(r"^(\d{1,6}|[A-Z_]{2,20})$")

def clean_genres(raw):
    if not isinstance(raw, list):
        return []
    out = []
    for item in raw:
        value = str(item).strip()
        if GENRE_KEY_RE.match(value) and value not in out:
            out.append(value)
    return out[:30]

def load_secret():
    env = (os.environ.get("CINEMIND_SECRET") or "").strip()
    if env:
        return env
    conn = get_db_conn()
    conn.execute("CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    conn.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('token_secret', ?)",
                 (base64.urlsafe_b64encode(os.urandom(48)).decode("ascii"),))
    conn.commit()
    secret = conn.execute("SELECT value FROM app_settings WHERE key = 'token_secret'").fetchone()[0]
    conn.close()
    return secret

SECRET_KEY = load_secret()

def issue_token(username):
    payload = json.dumps({"u": username, "ts": int(time.time())}).encode("utf-8")
    b64 = base64.urlsafe_b64encode(payload).decode("ascii")
    sig = hmac.new(SECRET_KEY.encode("utf-8"), b64.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{b64}.{sig}"

def current_username():
    """Username from a valid, unexpired Bearer token whose account still exists, otherwise None."""
    try:
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return None
        token = header[7:].strip()
        b64, sig = token.rsplit(".", 1)
        expected = hmac.new(SECRET_KEY.encode("utf-8"), b64.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        data = json.loads(base64.urlsafe_b64decode(b64.encode("ascii")).decode("utf-8"))
        if time.time() - data.get("ts", 0) > TOKEN_MAX_AGE:
            return None
        username = str(data["u"]).strip().lower()
        conn = get_db_conn()
        row = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        return username if row else None
    except Exception:
        return None

def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        username = current_username()
        if not username:
            return jsonify({"success": False, "message": "Please log in again."}), 401
        g.username = username
        return fn(*args, **kwargs)
    return wrapper

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "CineMind Engine Live", "version": "20.1-Secure",
                    "database_tables": ["users", "watchlist", "favorites", "not_interested", "interactions"]})

@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip().lower()
    password = str(data.get("password", ""))
    genres = clean_genres(data.get("genres"))
    if not re.match(r"^[a-z0-9_.\-]{3,30}$", username):
        return jsonify({"success": False, "message": "Username must be 3-30 characters: letters, numbers, dots, dashes or underscores."}), 400
    if len(password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters."}), 400
    if len(genres) < 3:
        return jsonify({"success": False, "message": "Please pick at least 3 genres."}), 400
    conn = get_db_conn()
    try:
        conn.execute("INSERT INTO users (username, password, genres) VALUES (?, ?, ?)",
                     (username, generate_password_hash(password), json.dumps(genres)))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "message": "That username is already taken."}), 409
    conn.close()
    return jsonify({"success": True, "username": username, "genres": genres,
                    "token": issue_token(username), "message": "Account created successfully!"})

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip().lower()
    password = str(data.get("password", ""))
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400
    conn = get_db_conn()
    row = conn.execute("SELECT password, genres FROM users WHERE username = ?", (username,)).fetchone()
    ok, saved_genres = False, []
    if row:
        stored = row[0] or ""
        try:
            saved_genres = clean_genres(json.loads(row[1] or "[]"))
        except Exception:
            saved_genres = []
        if stored.startswith(("pbkdf2:", "scrypt:")):
            ok = check_password_hash(stored, password)
        elif hmac.compare_digest(stored, hashlib.sha256(password.encode()).hexdigest()):
            ok = True  # Upgrade old SHA-256 accounts to a salted hash.
            conn.execute("UPDATE users SET password = ? WHERE username = ?",
                         (generate_password_hash(password), username))
            conn.commit()
    conn.close()
    if ok:
        return jsonify({"success": True, "username": username, "genres": saved_genres,
                        "token": issue_token(username),
                        "message": "Login successful!"})
    return jsonify({"success": False, "message": "Invalid username or password."}), 401

@app.route("/api/me", methods=["GET"])
@require_auth
def me():
    conn = get_db_conn()
    row = conn.execute("SELECT genres FROM users WHERE username = ?", (g.username,)).fetchone()
    conn.close()
    try:
        genres = clean_genres(json.loads((row[0] if row else "[]") or "[]"))
    except Exception:
        genres = []
    return jsonify({"success": True, "username": g.username, "genres": genres})

@app.route("/api/user/genres", methods=["POST"])
@require_auth
def save_genres():
    data = request.get_json(silent=True) or {}
    genres = clean_genres(data.get("genres"))
    if len(genres) < 3:
        return jsonify({"success": False, "message": "Please keep at least 3 genres selected."}), 400
    conn = get_db_conn()
    conn.execute("UPDATE users SET genres = ? WHERE username = ?", (json.dumps(genres), g.username))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "genres": genres})

@app.route("/api/user/library", methods=["GET"])
@require_auth
def get_library():
    username = g.username
    conn = get_db_conn()
    c = conn.cursor()
    q = "SELECT movie_id, title, poster, vote_average, media_type FROM {} WHERE username = ?"
    c.execute(q.format("watchlist"), (username,))
    wl = [{"id": r[0], "title": r[1], "poster": r[2], "vote_average": r[3], "media_type": r[4] or "movie"} for r in c.fetchall()]
    c.execute(q.format("favorites"), (username,))
    fav = [{"id": r[0], "title": r[1], "poster": r[2], "vote_average": r[3], "media_type": r[4] or "movie"} for r in c.fetchall()]
    c.execute("SELECT movie_id, title, keywords FROM not_interested WHERE username = ?", (username,))
    ni = [{"id": r[0], "title": r[1], "keywords": json.loads(r[2] or "[]")} for r in c.fetchall()]
    c.execute("SELECT genres FROM users WHERE username = ?", (username,))
    g_row = c.fetchone()
    conn.close()
    saved = []
    if g_row:
        try:
            saved = json.loads(g_row[0] or "[]")
        except Exception:
            pass
    return jsonify({"watchlist": wl, "favorites": fav, "not_interested": ni, "genres": saved})

@app.route("/api/user/library/toggle", methods=["POST"])
@require_auth
def toggle_library():
    data = request.get_json(silent=True) or {}
    username = g.username
    lib_type = data.get("type")
    movie = data.get("movie", {})
    if lib_type not in ("watchlist", "favorites") or not movie:
        return jsonify({"success": False, "message": "Invalid payload."}), 400
    movie_id = movie.get("id")
    title = movie.get("title") or movie.get("name")
    table = "watchlist" if lib_type == "watchlist" else "favorites"
    conn = get_db_conn()
    c = conn.cursor()
    c.execute(f"SELECT id FROM {table} WHERE username = ? AND movie_id = ?", (username, movie_id))
    if c.fetchone():
        c.execute(f"DELETE FROM {table} WHERE username = ? AND movie_id = ?", (username, movie_id))
        action = "removed"
    else:
        try:
            c.execute(f"INSERT OR REPLACE INTO {table} (username, movie_id, title, poster, vote_average, media_type) VALUES (?, ?, ?, ?, ?, ?)",
                      (username, movie_id, title, movie.get("poster") or "", movie.get("vote_average", 0.0), movie.get("media_type", "movie")))
            c.execute("INSERT INTO interactions (username, movie_id, title, action, vote_average) VALUES (?, ?, ?, ?, ?)",
                      (username, movie_id, title, 'like' if lib_type == 'favorites' else 'watched', movie.get("vote_average", 0.0)))
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({"success": False, "message": "User account not found in database."}), 400
        action = "added"
    conn.commit()
    conn.close()
    return jsonify({"success": True, "action": action})

@app.route("/api/user/not_interested", methods=["POST"])
@require_auth
def mark_not_interested():
    data = request.get_json(silent=True) or {}
    username = g.username
    movie = data.get("movie") or {}
    keywords = data.get("keywords") or []
    movie_id = movie.get("id")
    title = movie.get("title") or movie.get("name") or ""
    if not movie_id:
        return jsonify({"success": False, "message": "Missing movie id"}), 400
    conn = get_db_conn()
    try:
        conn.execute("INSERT OR REPLACE INTO not_interested (username, movie_id, title, keywords) VALUES (?, ?, ?, ?)",
                     (username, movie_id, title, json.dumps(keywords)))
        conn.execute("INSERT INTO interactions (username, movie_id, title, action, vote_average) VALUES (?, ?, ?, 'not_interested', ?)",
                     (username, movie_id, title, movie.get("vote_average", 0.0)))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()
    return jsonify({"success": True, "action": "hidden"})

@app.route("/api/user/insights", methods=["GET"])
@require_auth
def get_insights():
    username = g.username
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT action, vote_average FROM interactions WHERE username = ?", (username,))
    inter = c.fetchall()
    counts = {}
    for t in ("favorites", "watchlist", "not_interested"):
        counts[t] = c.execute(f"SELECT COUNT(*) FROM {t} WHERE username = ?", (username,)).fetchone()[0]
    conn.close()
    rated = [r[1] for r in inter if r[1]]
    return jsonify({
        "username": username,
        "total_recommendations_viewed": len(inter), "total_liked": counts["favorites"],
        "total_watchlist": counts["watchlist"], "total_not_interested": counts["not_interested"],
        "average_rating_of_interest": round(sum(rated) / len(rated), 2) if rated else 0.0,
        "dominant_mood": "Multi-API Neural Match",
        "genre_distribution": {"Drama": 30, "Sci-Fi": 22, "BL / GL": 18, "Anime": 15, "Docs & Sports": 15},
    })

def tmdb(path, **params):
    params["api_key"] = TMDB_API_KEY
    params.setdefault("include_adult", "false")
    try:
        r = requests.get(f"{TMDB}{path}", params=params, timeout=6)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}

def card(m, media, badge=None):
    return {
        "id": m["id"], "title": m.get("title") or m.get("name"), "media_type": media,
        "poster": f"{IMG}/w500{m['poster_path']}", "vote_average": m.get("vote_average", 0),
        "overview": m.get("overview", ""), "genre_ids": m.get("genre_ids", []),
        "exact_genres": format_exact_genres(m, badge),
        "release_date": m.get("release_date") or m.get("first_air_date") or "",
        "original_language": m.get("original_language", ""),
        "origin_country": m.get("origin_country") or [], "r18": is_genuine_r18(m),
    }

@app.route("/api/omdb", methods=["GET"])
def omdb_info():
    title, year = request.args.get("title", ""), request.args.get("year", "")
    if not OMDB_API_KEY or not title:
        return jsonify({})
    try:
        o = requests.get("https://www.omdbapi.com/", params={"apikey": OMDB_API_KEY, "t": title, "y": year}, timeout=4).json()
        if o.get("Response") == "True":
            return jsonify({k.lower(): o.get(k) for k in ("imdbRating", "Runtime", "Director", "Writer", "Actors", "Genre", "Awards")})
    except Exception:
        pass
    return jsonify({})

CREW_GROUPS = {
    "directors": {"Director"},
    "writers": {"Writer", "Screenplay", "Story", "Novel", "Characters", "Teleplay"},
    "producers": {"Producer", "Executive Producer", "Co-Producer"},
    "crew": {"Original Music Composer", "Director of Photography", "Editor", "Production Design", "Costume Design"},
}

def _photo(path):
    return f"{IMG}/w185{path}" if path else None

@app.route("/api/credits", methods=["GET"])
def movie_credits():
    movie_id = request.args.get("id")
    media_type = "tv" if request.args.get("media_type") == "tv" else "movie"
    region = (request.args.get("region") or "PH").upper()[:2]
    if not movie_id:
        return jsonify({})
    d = tmdb(f"/{media_type}/{movie_id}", append_to_response="credits,watch/providers")
    if not d:
        return jsonify({})
    credits = d.get("credits") or {}
    cast = [{"id": c.get("id"), "name": c.get("name"), "character": c.get("character") or "Role not listed",
             "photo": _photo(c.get("profile_path"))}
            for c in (credits.get("cast") or [])[:30] if c.get("name")]
    out = {k: [] for k in CREW_GROUPS}
    seen = set()
    for c in credits.get("crew") or []:
        for group, jobs in CREW_GROUPS.items():
            key = (group, c.get("id"), c.get("job"))
            if c.get("job") in jobs and key not in seen:
                seen.add(key)
                out[group].append({"id": c.get("id"), "name": c.get("name"), "job": c.get("job"),
                                   "photo": _photo(c.get("profile_path"))})
    if not out["directors"]:
        out["directors"] = [{"id": c.get("id"), "name": c.get("name"), "job": "Creator",
                             "photo": _photo(c.get("profile_path"))} for c in (d.get("created_by") or [])]
    prov = ((d.get("watch/providers") or {}).get("results") or {}).get(region) or {}
    providers = [p.get("provider_name") for p in (prov.get("flatrate") or [])]
    return jsonify({
        "id": d.get("id"),
        "title": d.get("title") or d.get("name"),
        "tagline": d.get("tagline", ""),
        "runtime": d.get("runtime") or (d.get("episode_run_time") or [None])[0],
        "genres": [x.get("name") for x in (d.get("genres") or []) if x.get("name")],
        "providers": providers,
        "cast": cast, "directors": out["directors"][:3], "writers": out["writers"][:6],
        "producers": out["producers"][:6], "crew": out["crew"][:8],
    })

@app.route("/api/top10", methods=["GET"])
def top10():
    region = (request.args.get("region") or "PH").upper()[:2]
    media = "tv" if request.args.get("media") == "tv" else "movie"
    provider = request.args.get("provider", "")
    since = (date.today() - timedelta(days=270)).isoformat()
    params = {"watch_region": region, "with_watch_monetization_types": "flatrate",
              "sort_by": "popularity.desc", "vote_count.gte": 30}
    params["first_air_date.gte" if media == "tv" else "primary_release_date.gte"] = since
    if provider:
        params["with_watch_providers"] = provider
    items, seen = [], set()
    for page in (1, 2, 3):
        for m in tmdb(f"/discover/{media}", page=page, **params).get("results", []):
            if m.get("id") in seen or not m.get("poster_path") or not is_safe_non_porn(m):
                continue
            seen.add(m["id"])
            item = card(m, media)
            item["rank"] = len(items) + 1
            items.append(item)
            if len(items) == 10:
                return jsonify({"success": True, "region": region, "items": items})
    return jsonify({"success": True, "region": region, "items": items})

SPECIAL_DISCOVER = {
    "BL": ("Boys' Love (BL)", {"with_keywords": "286407|250606|158718", "without_genres": "16"}, {"with_keywords": "286407|250606|158718", "without_genres": "16"}),
    "GL": ("Girls' Love (GL)", {"with_keywords": "264386|9840|158718", "without_genres": "16"}, {"with_keywords": "264386|9840", "without_genres": "16"}),
    "ANIME": ("Anime", {"with_genres": "16", "with_origin_country": "JP|KR|CN"}, {"with_genres": "16", "with_origin_country": "JP|KR|CN"}),
    "KIDS": ("Kids & Family", {"with_genres": "10762|10751", "without_genres": "80,9648"}, {"with_genres": "10751", "without_genres": "27,53,80"}),
    "SPORTS": ("Real-Life Sports", {"with_keywords": "6075|13042|6513|1721", "without_genres": "16,10765"}, {"with_keywords": "6075|13042|6513|1721", "without_genres": "16,14"}),
}

@app.route("/api/discover", methods=["GET"])
def discover():
    genre = request.args.get("genre", "")
    media = request.args.get("media", "all")
    country = request.args.get("country", "").upper()[:2]
    provider = request.args.get("provider", "")
    region = (request.args.get("region") or "PH").upper()[:2]
    try:
        page = max(1, min(int(request.args.get("page", 1)), 500))
    except ValueError:
        page = 1
    kinds = ["movie", "tv"] if media == "all" else [media if media in ("movie", "tv") else "movie"]
    items, pages = [], []
    for kind in kinds:
        p = {"sort_by": "popularity.desc", "vote_count.gte": 40, "page": page, "language": "en-US"}
        badge = None
        if genre in SPECIAL_DISCOVER:
            badge, tvp, mvp = SPECIAL_DISCOVER[genre]
            p.update(tvp if kind == "tv" else mvp)
            p["vote_count.gte"] = 5
        elif genre.isdigit():
            p["with_genres"] = MOVIE_TO_TV.get(genre, genre) if kind == "tv" else genre
        if country and "with_origin_country" not in p:
            p["with_origin_country"] = country
            p["vote_count.gte"] = 5
        if provider:
            p["with_watch_providers"] = provider
            p["watch_region"] = region
            p["with_watch_monetization_types"] = "flatrate"
        data = tmdb(f"/discover/{kind}", **p)
        pages.append(data.get("total_pages", 0))
        for m in data.get("results", []):
            if not m.get("poster_path") or not is_safe_non_porn(m):
                continue
            if genre in ("SPORTS",) and is_animated_or_cartoon(m):
                continue
            items.append(card(m, kind, badge))
    if len(kinds) == 2:
        mv = [i for i in items if i["media_type"] == "movie"]
        tv = [i for i in items if i["media_type"] == "tv"]
        items = [x for pair in zip(mv, tv) for x in pair] + mv[len(tv):] + tv[len(mv):]
    return jsonify({"success": True, "page": page, "items": items, "has_more": bool(pages) and page < max(pages) and bool(items)})

PARSE_PROMPT = f"""You are Nova, a flawless, highly accurate AI cinema and TV expert.
CRITICAL RULES FOR 100% ACCURACY:
1. ZERO HALLUCINATIONS: If the user describes a plot, identify the EXACT real-world title in "plot_guesses". Do NOT invent or guess blindly. If unsure, leave "plot_guesses" empty.
2. STRICT CATEGORIES: "SPORTS" = real-life live-action only. "DOC" = true-life documentary only.

Return ONLY a valid JSON object with these keys:
{{"intent": "recommend"|"similar_to"|"plot_search"|"chitchat"|"question",
"special_category": "BL"|"GL"|"SPORTS"|"DOC"|"ANIME"|"KIDS"|null,
"plot_guesses": [{{"title": "Exact Title", "year": 2022, "media_type": "movie"|"tv", "why": "1-sentence verification."}}],
"genres": [from: {GENRE_LIST}], "exclude_genres": [], "year_from": null, "year_to": null,
"min_rating": null, "language": "ISO 639-1 or null", "origin_country": "ISO 3166-1 or null",
"sort": "popularity"|"rating"|"newest", "mood_keywords": [], "similar_to": [], "exclude_titles": [],
"direct_reply": "A concise, engaging, and 100% factually accurate response."}}"""

def groq_json(system, user, temperature=0.1, timeout=10):
    if not GROQ_API_KEY:
        return None
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile",
                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                  "response_format": {"type": "json_object"}, "temperature": temperature},
            timeout=timeout)
        if res.status_code == 200:
            return json.loads(res.json()["choices"][0]["message"]["content"])
    except Exception:
        pass
    return None

def detect_special_category(text=""):
    lower = (text or "").lower()
    if re.search(r"\b(boys love|boy's love|boys' love|bl series|bl drama|thai bl|korean bl|japanese bl|yaoi)\b", lower):
        return "BL"
    if re.search(r"\b(girls love|girl's love|girls' love|gl series|gl drama|thai gl|sapphic|lesbian|freenbecky|lingorm|yuri)\b", lower):
        return "GL"
    if re.search(r"\b(fifa|wwe|formula 1|f1|ufc|nba|nfl|real sports|real life sports|sports documentary|boxing|wrestling|football|basketball)\b", lower) and "toy story" not in lower:
        return "SPORTS"
    if re.search(r"\b(documentary|documentaries|docuseries|true crime|jeffrey dahmer|dahmer|tinder swindler|making a murderer)\b", lower):
        return "DOC"
    if re.search(r"\b(anime|japanese animation|korean animation|chinese animation|donghua|shonen|studio ghibli|makoto shinkai)\b", lower):
        return "ANIME"
    if re.search(r"\b(kids|children|family movie|pixar|disney animated|dreamworks|cartoon)\b", lower):
        return "KIDS"
    return None

def deep_plot_detective(message):
    lower = message.lower()
    for rule in KNOWN_PLOT_PATTERNS:
        if any(w in lower for w in rule["must_have_any"]):
            score = sum(2 if pat in lower else 0 for pat in rule["patterns"])
            hits = sum(1 for w in rule["must_have_any"] if w in lower)
            if score >= 2 or hits >= 2:
                return rule["guesses"], rule["reply"]
    guesses, snippet_answer = [], None
    try:
        clean_q = re.sub(r"\b(why|how|what|who|when|is|there|in|i am|i'm|looking for a|looking for|what is the|what's that|movie where|movie about|film where|film about|series where|show where|a|an|the|were|was|from|really)\b", " ", lower)
        clean_q = re.sub(r"\s+", " ", clean_q).strip()
        if len(clean_q) >= 3:
            wiki = requests.get("https://en.wikipedia.org/w/api.php",
                                params={"action": "query", "list": "search", "srsearch": f"{clean_q} film OR television series", "srlimit": 8, "format": "json"},
                                headers={"User-Agent": "CineMindCapstone/1.0"}, timeout=4).json()
            for item in wiki.get("query", {}).get("search", []):
                w_title = item.get("title", "")
                snippet = re.sub(r"<[^>]+>", "", item.get("snippet", "")).strip()
                if any(s in w_title.lower() for s in ["list of", "category:", "disambiguation", "awards", "filmography"]):
                    continue
                snippet_answer = snippet_answer or snippet
                m_year = re.search(r"\((\d{4})\s*[^\)]*(film|series|TV)\)", w_title, re.I)
                clean_title = re.sub(r"\s*\([^\)]*\)\s*", "", w_title).strip()
                if clean_title and len(clean_title) < 65:
                    guesses.append({"title": clean_title, "year": int(m_year.group(1)) if m_year else None,
                                    "media_type": "tv" if re.search(r"series|TV", w_title, re.I) else "movie",
                                    "why": (snippet[:140] + "...") if snippet else f"Matched to '{clean_q}'."})
                if len(guesses) >= 5:
                    break
    except Exception:
        pass
    if guesses:
        top = guesses[0]
        yr = f" ({top['year']})" if top.get("year") else ""
        if snippet_answer and any(w in lower for w in ["why", "how", "what", "who", "explain"]):
            return guesses, f"Regarding '{top['title']}'{yr}: {snippet_answer}. Here are matching titles:"
        return guesses, f"The top match is '{top['title']}'{yr}. Here are the closest titles:"
    return [], None

COUNTRY_MAP = {
    "korean": ("KR", "ko", "South Korean"), "korea": ("KR", "ko", "South Korean"),
    "k-drama": ("KR", "ko", "South Korean"), "kdrama": ("KR", "ko", "South Korean"),
    "japanese": ("JP", "ja", "Japanese"), "japan": ("JP", "ja", "Japanese"),
    "filipino": ("PH", "tl", "Filipino"), "pinoy": ("PH", "tl", "Filipino"),
    "philippine": ("PH", "tl", "Philippine"), "philippines": ("PH", "tl", "Philippine"),
    "tagalog": ("PH", "tl", "Filipino"), "thai": ("TH", "th", "Thai"), "thailand": ("TH", "th", "Thai"),
    "taiwanese": ("TW", "zh", "Taiwanese"), "taiwan": ("TW", "zh", "Taiwanese"),
    "chinese": ("CN", "zh", "Chinese"), "china": ("CN", "zh", "Chinese"),
    "indian": ("IN", "hi", "Indian"), "india": ("IN", "hi", "Indian"), "bollywood": ("IN", "hi", "Indian"),
    "french": ("FR", "fr", "French"), "france": ("FR", "fr", "French"),
    "spanish": ("ES", "es", "Spanish"), "spain": ("ES", "es", "Spanish"),
    "british": ("GB", "en", "British"), "uk": ("GB", "en", "British"),
}

MOOD_GENRES = [
    (["romcom", "rom-com", "romantic comedy"], ["romance", "comedy"]),
    (["romance", "romantic", "love", "sweet", "heartbreaking"], ["romance"]),
    (["funny", "comedy", "hilarious", "laugh"], ["comedy"]),
    (["sad", "cry", "tearjerker", "emotional"], ["drama"]),
    (["sci-fi", "scifi", "science fiction", "space", "future", "alien", "time travel"], ["sci-fi"]),
    (["mind-bending", "twist", "psychological", "suspense", "dark", "thriller", "stuck", "trapped", "survival"], ["thriller"]),
    (["scary", "horror", "ghost", "creepy", "haunted"], ["horror"]),
    (["action", "explosive", "fight", "blockbuster"], ["action"]),
]

def smart_local_nlp_parse(message, history, username="Guest", fav_genres=None):
    lower = message.lower()
    genres, origin_country, language, country_label = [], None, None, ""
    special_cat = detect_special_category(message)
    for kw, (cc, lang, label) in COUNTRY_MAP.items():
        if re.search(rf"\b{re.escape(kw)}\b", lower):
            origin_country, language, country_label = cc, lang, label
            break
    if special_cat in CURATED_SPECIAL_CATALOG:
        replies = {
            "BL": f"Here are top Boys' Love (BL) series and movies for you, {username}.",
            "GL": f"Here are top Girls' Love (GL) series and films for you, {username}.",
            "SPORTS": f"Here are real-life, live-action sports titles for you, {username}. No cartoons.",
            "DOC": f"Here are gripping real-life documentaries for you, {username}.",
        }
        return {"intent": "recommend", "special_category": special_cat,
                "plot_guesses": list(CURATED_SPECIAL_CATALOG[special_cat]), "genres": genres,
                "origin_country": origin_country, "language": language, "mood_keywords": [],
                "similar_to": [], "direct_reply": replies[special_cat]}
    for words, gs in MOOD_GENRES:
        if any(w in lower for w in words):
            for gname in gs:
                if gname not in genres:
                    genres.append(gname)
    for gname in GENRES:
        if re.search(rf"\b{re.escape(gname)}\b", lower) and gname not in genres:
            genres.append(gname)
    if origin_country and not genres:
        if fav_genres:
            genres = [x.lower() for x in fav_genres if x.lower() in GENRES][:3]
        if not genres:
            genres = COUNTRY_DEFAULT_GENRES.get(origin_country, ["drama", "romance"])
    looks_like_plot = (not origin_country and not special_cat and (
        len(lower.split()) >= 4 or "?" in lower or any(p in lower for p in ["why", "how", "what", "movie where", "movie about", "stuck", "trapped", "infiltrate", "relives", "boxing"])))
    if looks_like_plot:
        guesses, reply = deep_plot_detective(message)
        if guesses:
            return {"intent": "plot_search", "special_category": None, "plot_guesses": guesses,
                    "genres": genres, "mood_keywords": [], "direct_reply": reply}
    guesses, direct_reply = [], None
    if origin_country == "KR" and "romance" in genres:
        guesses = CURATED_KOREAN_ROMCOMS
        direct_reply = f"Here are the sweetest Korean romantic comedies for you, {username}."
    if not direct_reply:
        desc = " ".join(p for p in [country_label, "/".join(genres[:3]).title()] if p) or f"'{message}'"
        direct_reply = f"Here are the top {desc} recommendations for you, {username}."
    return {"intent": "plot_search" if looks_like_plot else "recommend", "special_category": special_cat,
            "plot_guesses": guesses, "genres": genres, "origin_country": origin_country,
            "language": language, "mood_keywords": [], "similar_to": [], "direct_reply": direct_reply}

def extract_intent(message, history, username="Guest", fav_genres=None, client_guesses=None):
    local = smart_local_nlp_parse(message, history, username, fav_genres)
    ctx = "\n".join(f"{'User' if h.get('role') == 'user' else 'Nova'}: {h.get('content')}"
                    for h in (history or [])[-10:] if isinstance(h, dict) and h.get("content")) or "No prior messages."
    llm = groq_json(PARSE_PROMPT, f"User: {username}\nFavorite Genres: {', '.join(fav_genres or [])}\nHistory:\n{ctx}\n\nLatest Request: {message}")
    merged = llm if isinstance(llm, dict) else local
    for k in ("origin_country", "language", "genres", "special_category"):
        if not merged.get(k) and local.get(k):
            merged[k] = local[k]
    combined = []
    for gg in (local.get("plot_guesses") or []) + (merged.get("plot_guesses") or []) + (client_guesses or []):
        if isinstance(gg, dict) and gg.get("title") and not any(e.get("title", "").lower() == gg["title"].lower() for e in combined):
            combined.append(gg)
    merged["plot_guesses"] = combined
    return merged

def search_tmdb_title(title, year=None, preferred_media=None):
    order = [preferred_media, "tv" if preferred_media == "movie" else "movie"] if preferred_media in ("movie", "tv") else ["movie", "tv"]
    for m_type in order:
        params = {"query": title}
        if year and m_type == "movie":
            params["year"] = year
        elif year and m_type == "tv":
            params["first_air_date_year"] = year
        hits = tmdb(f"/search/{m_type}", **params).get("results", [])
        if not hits and year:
            hits = tmdb(f"/search/{m_type}", query=title).get("results", [])
        hits = [h for h in hits if is_safe_non_porn(h) and h.get("poster_path")]
        if hits:
            # Force 100% accuracy: Check for exact text match first before defaulting to popularity
            exact = next((h for h in hits if (h.get("title") or h.get("name") or "").lower() == title.lower()), None)
            if not exact:
                exact = hits[0]
            exact["media_type"] = m_type
            return exact
    return None

def find_movie_id(title):
    hit = search_tmdb_title(title)
    return (hit["id"], hit.get("media_type", "movie")) if hit else (None, "movie")

def keyword_ids(words):
    ids = []
    for w in (words or [])[:4]:
        r = tmdb("/search/keyword", query=w).get("results", [])
        if r:
            ids.append(str(r[0]["id"]))
    return ids

def plot_search(p):
    results, seen = [], set()
    for idx, gg in enumerate((p.get("plot_guesses") or [])[:10]):
        title = gg.get("title") if isinstance(gg, dict) else str(gg)
        if not title:
            continue
        chosen = search_tmdb_title(title, gg.get("year") if isinstance(gg, dict) else None, gg.get("media_type") if isinstance(gg, dict) else None)
        if chosen:
            key = f"{chosen['media_type']}_{chosen['id']}"
            if key not in seen:
                seen.add(key)
                chosen["_bonus"] = 50.0 - idx * 3.5
                chosen["_is_guess"] = True
                if isinstance(gg, dict) and gg.get("why"):
                    chosen["_guess_why"] = gg["why"]
                results.append(chosen)
    if len(results) < 6:
        kws = keyword_ids(p.get("mood_keywords", []))
        if kws:
            for m in tmdb("/discover/movie", with_keywords="|".join(kws), sort_by="popularity.desc", **{"vote_count.gte": 40}).get("results", []):
                if is_safe_non_porn(m) and m.get("poster_path") and f"movie_{m['id']}" not in seen:
                    m["media_type"] = "movie"
                    seen.add(f"movie_{m['id']}")
                    m["_bonus"] = 10.0
                    results.append(m)
    if results and len(results) < 8:
        top_item = results[0]
        tm = top_item.get("media_type", "movie")
        for m in tmdb(f"/{tm}/{top_item['id']}/recommendations").get("results", []):
            if is_safe_non_porn(m) and m.get("poster_path") and f"{tm}_{m['id']}" not in seen:
                m["media_type"] = tm
                seen.add(f"{tm}_{m['id']}")
                m["_bonus"] = 8.0
                m["_guess_why"] = f"Shares key themes with {top_item.get('title') or top_item.get('name')}."
                results.append(m)
    return results

def find_movies(intent):
    special_cat = intent.get("special_category")
    strict_no_animation = special_cat in ("SPORTS", "DOC") or "documentary" in (intent.get("genres") or [])
    if intent.get("intent") == "plot_search" and not special_cat:
        found = plot_search(intent)
        if found:
            return found
    cands = {}
    target_lang = intent.get("language")
    target_country = (intent.get("origin_country") or "").upper() or None
    badge = {"BL": "Boys' Love (BL)", "GL": "Girls' Love (GL)", "SPORTS": "Real-Life Sports",
             "DOC": "Documentary", "ANIME": "Anime", "KIDS": "Kids & Family"}.get(special_cat)

    def add(movies, bonus=0, why_note=None, enforce_country=False, default_media="movie"):
        for m in movies:
            if not is_safe_non_porn(m) or not m.get("id") or not m.get("poster_path"):
                continue
            if strict_no_animation and is_animated_or_cartoon(m):
                continue
            m_type = m.get("media_type") or default_media
            m["media_type"] = m_type
            if badge:
                m["_customGenreBadge"] = badge
            if enforce_country and target_lang and m.get("original_language") != target_lang:
                continue
            if target_country and not m.get("origin_country"):
                m["origin_country"] = [target_country]
            key = f"{m_type}_{m['id']}"
            if key not in cands:
                m["_bonus"] = bonus
                if why_note:
                    m["_guess_why"] = why_note
                cands[key] = m
            else:
                cands[key]["_bonus"] = max(cands[key].get("_bonus", 0), bonus)

    for idx, gg in enumerate((intent.get("plot_guesses") or [])[:12]):
        if not isinstance(gg, dict) or not gg.get("title"):
            continue
        hit = search_tmdb_title(gg["title"], gg.get("year"), gg.get("media_type"))
        if hit:
            add([hit], bonus=45.0 - idx * 2.0, why_note=gg.get("why"), default_media=hit.get("media_type", "movie"))

    if special_cat in SPECIAL_DISCOVER:
        _, tvp, mvp = SPECIAL_DISCOVER[special_cat]
        add(tmdb("/discover/tv", sort_by="popularity.desc", **tvp).get("results", []), bonus=20.0, default_media="tv")
        add(tmdb("/discover/movie", sort_by="popularity.desc", **mvp).get("results", []), bonus=18.0, default_media="movie")
    elif special_cat == "DOC":
        add(tmdb("/discover/tv", with_genres="99", without_genres="16,10762", sort_by="popularity.desc").get("results", []), bonus=22.0, default_media="tv")
        add(tmdb("/discover/movie", with_genres="99", without_genres="16,10751", sort_by="popularity.desc").get("results", []), bonus=20.0, default_media="movie")

    for t in (intent.get("similar_to") or [])[:2]:
        mid, m_type = find_movie_id(t)
        if mid:
            add(tmdb(f"/{m_type}/{mid}/recommendations").get("results", []), bonus=15.0, why_note=f"Recommended based on '{t}'.", default_media=m_type)

    if not special_cat:
        gids = [str(GENRES[x.lower()]) for x in (intent.get("genres") or []) if x.lower() in GENRES]
        xids = [str(GENRES[x.lower()]) for x in (intent.get("exclude_genres") or []) if x.lower() in GENRES]
        if strict_no_animation and "16" not in xids:
            xids.append("16")
        p = {"include_adult": "false", "vote_count.gte": 10 if (target_country or target_lang) else 80,
             "language": "en-US", "sort_by": "popularity.desc"}
        if gids:
            p["with_genres"] = "|".join(gids[:3]) if target_country else ",".join(gids[:2])
        if xids:
            p["without_genres"] = ",".join(xids)
        if target_lang:
            p["with_original_language"] = target_lang
        if target_country:
            p["with_origin_country"] = target_country
        if intent.get("_media") != "tv":
            for page in (1, 2):
                add(tmdb("/discover/movie", page=page, **p).get("results", []), bonus=10.0, enforce_country=True)
        if target_country or intent.get("_media") == "tv":
            tv_p = dict(p)
            if gids:
                tv_p["with_genres"] = "|".join(MOVIE_TO_TV.get(x, x) for x in gids[:3])
            add(tmdb("/discover/tv", page=1, **tv_p).get("results", []), bonus=10.0, enforce_country=True, default_media="tv")
    return list(cands.values())

def get_seen_and_disliked(username):
    if not username:
        return set(), set()
    conn = get_db_conn()
    c = conn.cursor()
    ids, kws = set(), set()
    u = username.lower()
    for q in ("SELECT movie_id FROM watchlist WHERE username=?", "SELECT movie_id FROM favorites WHERE username=?", "SELECT movie_id FROM not_interested WHERE username=?"):
        c.execute(q, (u,))
        ids.update(r[0] for r in c.fetchall())
    c.execute("SELECT keywords FROM not_interested WHERE username=?", (u,))
    for row in c.fetchall():
        try:
            for kw in json.loads(row[0] or "[]"):
                if len(kw) > 3:
                    kws.add(kw.lower())
        except Exception:
            pass
    conn.close()
    return ids, kws

def norm(t):
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())

def rank(cands, intent, seen_ids, disliked_titles=None, disliked_keywords=None):
    is_plot = intent.get("intent") == "plot_search"
    blocked = {norm(t) for t in (intent.get("exclude_titles") or [])}
    if disliked_titles:
        blocked |= {norm(t) for t in disliked_titles}
    if not is_plot:
        blocked |= {norm(t) for t in (intent.get("similar_to") or [])}
    out, seen_unique = [], set()
    for m in cands:
        if not is_safe_non_porn(m):
            continue
        key = f"{m.get('media_type', 'movie')}_{m['id']}"
        if key in seen_unique:
            continue
        seen_unique.add(key)
        if norm(m.get("title") or m.get("name")) in blocked:
            continue
        if not is_plot and not m.get("_is_guess") and m["id"] in seen_ids:
            continue
        if disliked_keywords:
            blob = f"{m.get('title') or ''} {m.get('name') or ''} {m.get('overview') or ''}".lower()
            if sum(1 for kw in disliked_keywords if kw in blob) >= 2:
                continue
        pop = min((m.get("popularity") or 0) / 100, 1.0)
        m["_score"] = (m.get("vote_average") or 0) * 0.7 + pop * 1.5 + m.get("_bonus", 0)
        out.append(m)
    out.sort(key=lambda x: x["_score"], reverse=True)
    top = out[:12]
    for idx, m in enumerate(top):
        if m.get("_bonus", 0) >= 40:
            m["_match"] = 99
        elif m.get("_bonus", 0) >= 25:
            m["_match"] = max(94, 98 - idx)
        else:
            best = top[0]["_score"] or 1
            m["_match"] = max(82, min(97, int(82 + 15 * (m["_score"] / best))))
    return top

def explain(message, username, movies, intent):
    listing = [{"id": m["id"], "title": m.get("title") or m.get("name"),
                "year": (m.get("release_date") or m.get("first_air_date") or "")[:4],
                "overview": (m.get("overview") or "")[:200]} for m in movies[:8]]
    system = (f"You are Nova, a flawless AI cinema companion talking to {username}. "
              'CRITICAL: Base your response ONLY on the provided overviews. Do NOT invent plot details. '
              'Return ONLY JSON: {"reply": "2 engaging, 100% accurate sentences", '
              '"reasons": {"<id>": "1 concise sentence confirming the match based strictly on the overview"}}. Only mention listed titles.')
    return groq_json(system, f"User Request: {message}\nTitles: {json.dumps(listing)}", temperature=0.1) or {}

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    profile = data.get("profile") or {}
    username = profile.get("name", "Guest")
    fav_genres = profile.get("favorite_genres") or []
    disliked_titles = profile.get("not_interested_titles") or profile.get("disliked_titles") or []
    selected_country = (profile.get("origin_country") or "").strip().upper()
    history = data.get("history") or []
    region = (data.get("region") or "").upper() or None
    media_filter = data.get("media") if data.get("media") in ("movie", "tv") else None
    
    if not message:
        return jsonify({"reply": f"Hey {username}! Tell me a plot, mood, genre or country.", "movies": []})
        
    intent = extract_intent(message, history, username, fav_genres, data.get("client_guesses") or [])
    intent["_media"] = media_filter
    intent_type = intent.get("intent", "recommend")
    
    if intent_type in ("chitchat", "question") and not intent.get("plot_guesses") and not intent.get("genres") and not intent.get("special_category"):
        return jsonify({"reply": intent.get("direct_reply") or f"I'm Nova, your AI cinema companion, {username}. Ask me any movie question.",
                        "movies": [], "intent": intent_type, "success": True})
                        
    if intent_type == "recommend" and not intent.get("genres") and not intent.get("plot_guesses") and not intent.get("special_category"):
        if fav_genres:
            intent["genres"] = [x.lower() for x in fav_genres[:3]]
        elif intent.get("origin_country"):
            intent["genres"] = COUNTRY_DEFAULT_GENRES.get(intent["origin_country"], ["drama", "romance"])
            
    if not intent.get("origin_country") and selected_country and intent_type != "plot_search" and not intent.get("special_category"):
        intent["origin_country"] = selected_country
        
    cands = find_movies(intent)
    
    # FIX NOVA ACCURACY: Only use TMDB multi-search fallback for short titles. 
    # Do NOT use it for long plot queries (prevents garbage results).
    if not cands and len(message.split()) < 4 and intent_type != "plot_search":
        cands = [m for m in tmdb("/search/multi", query=message).get("results", [])
                 if is_safe_non_porn(m) and m.get("poster_path") and m.get("media_type") in ("movie", "tv")]
                 
    if media_filter:
        cands = [m for m in cands if (m.get("media_type") or "movie") == media_filter]
        
    seen_ids, disliked_keywords = get_seen_and_disliked(username)
    top = rank(cands, intent, seen_ids, disliked_titles, disliked_keywords) or cands[:12]
    
    if not top:
        return jsonify({"reply": intent.get("direct_reply") or f"I couldn't find a 100% accurate match for that, {username}. Could you give me another detail?",
                        "movies": [], "intent": intent_type, "success": True})
                        
    ex = explain(message, username, top, intent)
    reasons = ex.get("reasons", {}) if isinstance(ex.get("reasons"), dict) else {}
    reply = ex.get("reply") or intent.get("direct_reply") or f"Here are my top matches for '{message}', {username}."
    movies = []
    
    for m in top:
        c = card(m, m.get("media_type", "movie"), m.get("_customGenreBadge"))
        c.update({"vote_count": m.get("vote_count", 0), "match": m.get("_match", 96),
                  "platforms": [region or "Global"],
                  "rationale": reasons.get(str(m["id"])) or m.get("_guess_why") or f"Matched to your request."})
        movies.append(c)
        
    return jsonify({"reply": reply, "movies": movies, "intent": intent_type, "success": True})

@app.route("/trends", methods=["GET"])
def trends():
    return jsonify({"ai_forecast": "Regional charts, genre-accurate browsing online.",
                    "trending_genres": ["Boys' Love (BL) and Girls' Love (GL)", "Real-Life Sports and True-Crime Docs", "Anime"]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
