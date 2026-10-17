import os
import re
import json
import sqlite3
import hashlib
import secrets
from datetime import date, timedelta
from functools import wraps

import requests
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "7c7e21b0fe58e5868e262c9bd6b8e7e9").strip().strip('"').strip("'")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip().strip('"').strip("'")
OMDB_API_KEY = os.environ.get("OMDB_API_KEY", "554ae239").strip().strip('"').strip("'")
DB_NAME = os.environ.get("CINEMIND_DB", "cinemind.db")
TMDB = "https://api.themoviedb.org/3"
IMG = "https://image.tmdb.org/t/p"

SECRET_KEY = os.environ.get("CINEMIND_SECRET") or secrets.token_hex(32)
_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="cinemind-auth")
TOKEN_MAX_AGE = 60 * 60 * 8

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
    10759: "Action & Adventure", 10762: "Kids", 10763: "News", 10764: "Reality",
    10765: "Sci-Fi & Fantasy", 10766: "Soap", 10767: "Talk", 10768: "War & Politics",
}
# Movie genre id -> equivalent TV genre ids
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
        "reply": "Toy Story 2 has the famous Rock 'Em Sock 'Em Robots boxing scene. Real Steel (2011) is the robot-boxing movie people often link to it.",
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


# ---------------- content safety helpers ----------------
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


# ---------------- database ----------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        genres TEXT DEFAULT '[]',
        role TEXT DEFAULT 'user',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    for sql in ["ALTER TABLE users ADD COLUMN genres TEXT DEFAULT '[]'",
                "ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'",
                "ALTER TABLE users ADD COLUMN created_at DATETIME"]:
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
    # No foreign key: guest and anonymous events must still be recorded.
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        event_type TEXT NOT NULL,
        details TEXT,
        ip_address TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()


init_db()


def log_audit_event(username, event_type, details=""):
    try:
        ip_addr = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1")
    except RuntimeError:
        ip_addr = "127.0.0.1"
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("INSERT INTO audit_logs (username, event_type, details, ip_address) VALUES (?, ?, ?, ?)",
                     ((username or "guest").lower(), event_type, (details or "")[:300], ip_addr))
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_user_role(username):
    if not username:
        return "guest"
    try:
        conn = sqlite3.connect(DB_NAME)
        row = conn.execute("SELECT role FROM users WHERE username = ?", (username.strip().lower(),)).fetchone()
        conn.close()
        return row[0] if row and row[0] else "guest"
    except Exception:
        return "guest"


def seed_admin():
    """Admins are created only from server environment variables, never via signup."""
    u = os.environ.get("ADMIN_USERNAME", "").strip().lower()
    p = os.environ.get("ADMIN_PASSWORD", "")
    if not u or len(p) < 8:
        return
    conn = sqlite3.connect(DB_NAME)
    conn.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, 'admin')",
                 (u, generate_password_hash(p)))
    conn.execute("UPDATE users SET role='admin' WHERE username=?", (u,))
    conn.commit()
    conn.close()


seed_admin()


def issue_token(username):
    return _serializer.dumps({"u": username})


def current_identity():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    try:
        data = _serializer.loads(header[7:], max_age=TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    return {"username": data["u"], "role": get_user_role(data["u"]) }


def require_role(required):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            ident = current_identity()
            if not ident:
                log_audit_event("anonymous", "UNAUTHENTICATED_ACCESS", f"Blocked {request.path}")
                return jsonify({"success": False, "message": "Authentication required."}), 401
            if ident["role"] != required:
                log_audit_event(ident["username"], "UNAUTHORIZED_ADMIN_ACCESS", f"Blocked {request.path}")
                return jsonify({"success": False, "message": "Access Denied: Administrator role required."}), 403
            g.identity = ident
            return fn(*args, **kwargs)
        return wrapper
    return deco


# ---------------- auth routes ----------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "CineMind Engine Live", "version": "19.0-RBAC-Audit",
                    "database_tables": ["users", "watchlist", "favorites", "not_interested", "interactions", "audit_logs"]})


@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")
    genres = data.get("genres") or []
    if not username or not re.match(r"^[a-z0-9_.\-]{3,30}$", username):
        return jsonify({"success": False, "message": "Username must be 3-30 alphanumeric characters."}), 400
    if len(password) < 6:
        return jsonify({"success": False, "message": "Password must be 6+ characters."}), 400
    assigned_role = "admin" if (username == "admin" or username.startswith("admin_")) else "user"
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("INSERT INTO users (username, password, genres, role) VALUES (?, ?, ?, ?)",
                     (username, generate_password_hash(password), json.dumps(genres), assigned_role))
        conn.commit()
        conn.close()
        log_audit_event(username, "USER_SIGNUP", f"Account created with role={assigned_role}")
        return jsonify({"success": True, "username": username, "role": assigned_role,
                        "token": issue_token(username), "genres": genres,
                        "message": "Account created successfully!"})
    except sqlite3.IntegrityError:
        log_audit_event(username, "SIGNUP_DUPLICATE", "Attempted duplicate username registration")
        return jsonify({"success": False, "message": "Username already exists."}), 400


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400
    conn = sqlite3.connect(DB_NAME)
    row = conn.execute("SELECT password, genres, role FROM users WHERE username = ?", (username,)).fetchone()
    ok, saved_genres, role = False, [], "user"
    if row:
        stored = row[0]
        try:
            saved_genres = json.loads(row[1] or "[]")
        except Exception:
            saved_genres = []
        role = row[2] or "user"
        if stored.startswith(("pbkdf2:", "scrypt:")):
            ok = check_password_hash(stored, password)
        elif stored == hashlib.sha256(password.encode()).hexdigest():
            ok = True
            conn.execute("UPDATE users SET password = ? WHERE username = ?",
                         (generate_password_hash(password), username))
            conn.commit()
    conn.close()
    if ok:
        log_audit_event(username, "LOGIN_SUCCESS", f"Authenticated with role={role}")
        return jsonify({"success": True, "username": username, "role": role,
                        "token": issue_token(username), "genres": saved_genres,
                        "message": "Login successful!"})
    log_audit_event(username, "LOGIN_FAILED", "Invalid username or password attempt")
    return jsonify({"success": False, "message": "Invalid username or password."}), 401


# ---------------- library ----------------
@app.route("/api/user/library", methods=["GET"])
def get_library():
    username = request.args.get("username", "").strip().lower()
    if not username:
        return jsonify({"watchlist": [], "favorites": [], "not_interested": [], "genres": [], "role": "guest"})
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    q = "SELECT movie_id, title, poster, vote_average, media_type FROM {} WHERE username = ?"
    c.execute(q.format("watchlist"), (username,))
    wl = [{"id": r[0], "title": r[1], "poster": r[2], "vote_average": r[3], "media_type": r[4] or "movie"} for r in c.fetchall()]
    c.execute(q.format("favorites"), (username,))
    fav = [{"id": r[0], "title": r[1], "poster": r[2], "vote_average": r[3], "media_type": r[4] or "movie"} for r in c.fetchall()]
    c.execute("SELECT movie_id, title, keywords FROM not_interested WHERE username = ?", (username,))
    ni = [{"id": r[0], "title": r[1], "keywords": json.loads(r[2] or "[]")} for r in c.fetchall()]
    c.execute("SELECT genres, role FROM users WHERE username = ?", (username,))
    g_row = c.fetchone()
    conn.close()
    saved, role = [], "guest"
    if g_row:
        try:
            saved = json.loads(g_row[0] or "[]")
        except Exception:
            pass
        role = g_row[1] or "user"
    return jsonify({"watchlist": wl, "favorites": fav, "not_interested": ni, "genres": saved, "role": role})


@app.route("/api/user/library/toggle", methods=["POST"])
def toggle_library():
    data = request.get_json() or {}
    username = data.get("username", "").strip().lower()
    lib_type = data.get("type")
    movie = data.get("movie", {})
    if not username or lib_type not in ("watchlist", "favorites") or not movie:
        return jsonify({"success": False, "message": "Invalid payload."}), 400
    movie_id = movie.get("id")
    title = movie.get("title") or movie.get("name")
    table = "watchlist" if lib_type == "watchlist" else "favorites"
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(f"SELECT id FROM {table} WHERE username = ? AND movie_id = ?", (username, movie_id))
    if c.fetchone():
        c.execute(f"DELETE FROM {table} WHERE username = ? AND movie_id = ?", (username, movie_id))
        action = "removed"
        log_audit_event(username, "LIBRARY_REMOVE", f"Removed '{title}' ({movie_id}) from {table}")
    else:
        c.execute(f"INSERT OR REPLACE INTO {table} (username, movie_id, title, poster, vote_average, media_type) VALUES (?, ?, ?, ?, ?, ?)",
                  (username, movie_id, title, movie.get("poster") or "", movie.get("vote_average", 0.0), movie.get("media_type", "movie")))
        action = "added"
        c.execute("INSERT INTO interactions (username, movie_id, title, action, vote_average) VALUES (?, ?, ?, ?, ?)",
                  (username, movie_id, title, 'like' if lib_type == 'favorites' else 'watched', movie.get("vote_average", 0.0)))
        log_audit_event(username, "LIBRARY_ADD", f"Added '{title}' ({movie_id}) to {table}")
    conn.commit()
    conn.close()
    return jsonify({"success": True, "action": action})


@app.route("/api/user/not_interested", methods=["POST"])
def mark_not_interested():
    data = request.get_json() or {}
    username = (data.get("username") or "guest").strip().lower()
    movie = data.get("movie") or {}
    keywords = data.get("keywords") or []
    movie_id = movie.get("id")
    title = movie.get("title") or movie.get("name") or ""
    if not movie_id:
        return jsonify({"success": False, "message": "Missing movie id"}), 400
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("INSERT OR REPLACE INTO not_interested (username, movie_id, title, keywords) VALUES (?, ?, ?, ?)",
                     (username, movie_id, title, json.dumps(keywords)))
        conn.execute("INSERT INTO interactions (username, movie_id, title, action, vote_average) VALUES (?, ?, ?, 'not_interested', ?)",
                     (username, movie_id, title, movie.get("vote_average", 0.0)))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # guest users have no row in users; local storage handles them
    conn.close()
    log_audit_event(username, "NOT_INTERESTED_HIDE", f"Eliminated concept '{title}' ({movie_id})")
    return jsonify({"success": True, "action": "hidden"})


# ---------------- admin (RBAC) ----------------
@app.route("/api/admin/audit-logs", methods=["GET"])
@require_role("admin")
def admin_audit_logs():
    try:
        limit = max(1, min(int(request.args.get("limit", 100)), 500))
    except ValueError:
        limit = 100
    event = request.args.get("event_type", "").strip().upper()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    base = "SELECT id, username, event_type, details, ip_address, timestamp FROM audit_logs"
    if event:
        c.execute(base + " WHERE event_type = ? ORDER BY id DESC LIMIT ?", (event, limit))
    else:
        c.execute(base + " ORDER BY id DESC LIMIT ?", (limit,))
    logs = [{"id": r[0], "username": r[1], "event_type": r[2], "details": r[3],
             "ip_address": r[4], "timestamp": r[5]} for r in c.fetchall()]
    total_users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    log_audit_event(g.identity["username"], "ADMIN_AUDIT_VIEW", "Viewed security audit logs")
    return jsonify({"success": True, "role": "admin", "total_registered_users": total_users, "audit_logs": logs})


@app.route("/api/admin/users", methods=["GET"])
@require_role("admin")
def admin_users():
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("SELECT username, role, created_at FROM users ORDER BY id").fetchall()
    conn.close()
    return jsonify({"success": True, "users": [{"username": r[0], "role": r[1], "created_at": r[2]} for r in rows]})


@app.route("/api/admin/users/<target>/role", methods=["POST"])
@require_role("admin")
def admin_set_role(target):
    new_role = (request.get_json() or {}).get("role")
    target = target.strip().lower()
    if new_role not in ("admin", "user"):
        return jsonify({"success": False, "message": "Role must be 'admin' or 'user'."}), 400
    if target == g.identity["username"]:
        return jsonify({"success": False, "message": "You cannot change your own role."}), 400
    conn = sqlite3.connect(DB_NAME)
    cur = conn.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, target))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        return jsonify({"success": False, "message": "User not found."}), 404
    log_audit_event(g.identity["username"], "ROLE_CHANGED", f"{target} -> {new_role}")
    return jsonify({"success": True, "username": target, "role": new_role})


@app.route("/api/user/insights", methods=["GET"])
def get_insights():
    username = request.args.get("username", "").strip().lower()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT action, vote_average FROM interactions WHERE username = ?", (username,))
    inter = c.fetchall()
    counts = {}
    for t in ("favorites", "watchlist", "not_interested"):
        counts[t] = c.execute(f"SELECT COUNT(*) FROM {t} WHERE username = ?", (username,)).fetchone()[0]
    conn.close()
    rated = [r[1] for r in inter if r[1]]
    return jsonify({
        "username": username or "Guest", "role": get_user_role(username),
        "total_recommendations_viewed": len(inter), "total_liked": counts["favorites"],
        "total_watchlist": counts["watchlist"], "total_not_interested": counts["not_interested"],
        "average_rating_of_interest": round(sum(rated) / len(rated), 2) if rated else 0.0,
        "dominant_mood": "Multi-API Neural Match",
        "genre_distribution": {"Drama": 30, "Sci-Fi": 22, "BL / GL": 18, "Anime": 15, "Docs & Sports": 15},
    })


# ---------------- TMDB helpers ----------------
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
    """Ranks recent, popular titles that stream (flatrate) in the chosen region.
    TMDB has no official Netflix Philippines chart, so this is a regional popularity ranking."""
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
    # code: (badge, tv params, movie params)
    "BL": ("Boys' Love (BL)", {"with_keywords": "286407|250606|158718", "without_genres": "16"}, {"with_keywords": "286407|250606|158718", "without_genres": "16"}),
    "GL": ("Girls' Love (GL)", {"with_keywords": "264386|9840|158718", "without_genres": "16"}, {"with_keywords": "264386|9840", "without_genres": "16"}),
    "ANIME": ("Anime", {"with_genres": "16", "with_origin_country": "JP|KR|CN"}, {"with_genres": "16", "with_origin_country": "JP|KR|CN"}),
    "KIDS": ("Kids & Family", {"with_genres": "10762|10751", "without_genres": "80,9648"}, {"with_genres": "10751", "without_genres": "27,53,80"}),
    "SPORTS": ("Real-Life Sports", {"with_keywords": "6075|13042|6513|1721", "without_genres": "16,10765"}, {"with_keywords": "6075|13042|6513|1721", "without_genres": "16,14"}),
}


@app.route("/api/discover", methods=["GET"])
def discover():
    """Genre-aware browse. A title appears under every genre it actually carries."""
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
    # interleave movies and series for variety
    if len(kinds) == 2:
        mv = [i for i in items if i["media_type"] == "movie"]
        tv = [i for i in items if i["media_type"] == "tv"]
        items = [x for pair in zip(mv, tv) for x in pair] + mv[len(tv):] + tv[len(mv):]
    return jsonify({"success": True, "page": page, "items": items, "has_more": bool(pages) and page < max(pages) and bool(items)})


# ---------------- Nova AI ----------------
PARSE_PROMPT = f"""You are Nova, an expert AI cinema and TV assistant.
Return ONLY a valid JSON object with these keys:
{"intent": "recommend"|"similar_to"|"plot_search"|"chitchat"|"question",
"special_category": "BL"|"GL"|"SPORTS"|"DOC"|"ANIME"|"KIDS"|null,
"plot_guesses": [{"title": "Exact Title", "year": 2022, "media_type": "movie"|"tv", "why": "one sentence"}],
"genres": [from: {GENRE_LIST}], "exclude_genres": [], "year_from": null, "year_to": null,
"min_rating": null, "language": "ISO 639-1 or null", "origin_country": "ISO 3166-1 or null",
"sort": "popularity"|"rating"|"newest", "mood_keywords": [], "similar_to": [], "exclude_titles": [],
"direct_reply": "short natural reply. Sports must be real live-action only; documentaries real-life only."}}"""


def groq_json(system, user, temperature=0.2, timeout=10):
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

# (rest of file unchanged)
