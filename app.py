import os
import re
import json
import sqlite3
import hashlib
import hmac
import base64
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from functools import wraps

import requests
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024
CORS(app, supports_credentials=True)

TMDB_API_KEY = (os.environ.get("TMDB_API_KEY") or "").strip().strip('"').strip("'")
GROQ_API_KEY = (os.environ.get("GROQ_API_KEY") or "").strip().strip('"').strip("'")
OMDB_API_KEY = (os.environ.get("OMDB_API_KEY") or "").strip().strip('"').strip("'")
DB_NAME = os.environ.get("CINEMIND_DB", "cinemind.db")
TMDB = "https://api.themoviedb.org/3"
IMG = "https://image.tmdb.org/t/p"

TOKEN_MAX_AGE = 60 * 60 * 24 * 30

# --- CONSTANTS & CONFIGURATIONS ---
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
    "BL": _cat([("KinnPorsche", "tv", 2022, "Hit Thai Boys' Love action-romance drama.")]),
    "GL": _cat([("GAP The Series", "tv", 2022, "Thai Girls' Love office romance.")]),
    "SPORTS": _cat([("The Last Dance", "tv", 2020, "NBA championship documentary series.")]),
    "DOC": _cat([("Making a Murderer", "tv", 2015, "Landmark true-crime documentary series.")]),
}

KNOWN_PLOT_PATTERNS = [
    {
        "patterns": ["boxing in toy story", "toy story boxing"],
        "must_have_any": ["toy story", "boxing"],
        "reply": "In Toy Story 2, there is a memorable boxing scene featuring the classic Rock 'Em Sock 'Em Robots inside Al's Toy Barn! Plus, Real Steel (2011) is the robot-boxing movie people often link to it.",
        "guesses": _cat([("Toy Story 2", "movie", 1999, "Features the Rock 'Em Sock 'Em Robots boxing scene.")]),
    },
]

CURATED_KOREAN_ROMCOMS = _cat([("Love Reset", "movie", 2023, "Couple on the verge of divorce both get amnesia.")])

# --- DATABASE & UTILS ---
def get_db_conn():
    conn = sqlite3.connect(DB_NAME, timeout=20.0, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_db():
    conn = getattr(g, "_database", None)
    if conn is None:
        conn = get_db_conn()
        conn.row_factory = sqlite3.Row
        g._database = conn
    return conn

@app.teardown_appcontext
def close_db(error=None):
    conn = g.pop("_database", None)
    if conn is not None:
        conn.close()

def init_db():
    try:
        conn = get_db_conn()
        c = conn.cursor()
        
        # RBAC Roles and ML weights 
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            genres TEXT DEFAULT '[]',
            genre_weights TEXT DEFAULT '{}',
            email TEXT UNIQUE,
            full_name TEXT,
            birth_date TEXT,
            avatar TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            
        for sql in [
            "ALTER TABLE users ADD COLUMN genres TEXT DEFAULT '[]'",
            "ALTER TABLE users ADD COLUMN genre_weights TEXT DEFAULT '{}'",
            "ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'",
            "ALTER TABLE users ADD COLUMN created_at TEXT",
            "ALTER TABLE users ADD COLUMN email TEXT",
            "ALTER TABLE users ADD COLUMN full_name TEXT",
            "ALTER TABLE users ADD COLUMN birth_date TEXT",
            "ALTER TABLE users ADD COLUMN avatar TEXT",
        ]:
            try:
                c.execute(sql)
            except Exception:
                pass
                
        # Audit Logs
        c.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            event_type TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            
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
            
        # Unified User Ratings Table
        c.execute('''CREATE TABLE IF NOT EXISTS user_ratings (
            username TEXT NOT NULL,
            movie_id INTEGER NOT NULL,
            media_type TEXT DEFAULT 'movie',
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            review_body TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (username, movie_id, media_type),
            FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE)''')
            
        conn.commit()
        conn.close()
    except Exception as e:
        print("init_db failed:", e)

def log_audit_event(username, event_type, details=""):
    try:
        ip_addr = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1")
    except RuntimeError:
        ip_addr = "127.0.0.1"
    try:
        conn = get_db_conn()
        conn.execute("INSERT INTO audit_logs (username, event_type, details, ip_address) VALUES (?, ?, ?, ?)",
                     ((username or "guest").lower(), event_type, (details or "")[:300], ip_addr))
        conn.commit()
        conn.close()
    except Exception:
        pass

def load_secret():
    env = (os.environ.get("CINEMIND_SECRET") or "").strip()
    return env if env else "cinemind-permanent-secret-key-12345"

SECRET_KEY = load_secret()

def issue_token(username):
    payload = json.dumps({"u": username, "ts": int(time.time())}).encode("utf-8")
    b64 = base64.urlsafe_b64encode(payload).decode("ascii")
    sig = hmac.new(SECRET_KEY.encode("utf-8"), b64.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{b64}.{sig}"

def current_username():
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

# --- AGE & CONTENT RESTRICTION LOGIC ---
ADULT_AGE = 18
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s]{2,}$")
AVATAR_RE = re.compile(r"^data:image/(jpeg|png|webp);base64,[A-Za-z0-9+/=]+$")
AVATAR_MAX_CHARS = 400_000

def parse_birth_date(value):
    try:
        bd = date.fromisoformat(str(value or "").strip())
    except ValueError:
        return None
    today = date.today()
    return bd if (bd <= today and bd.year >= today.year - 120) else None

def calc_age(bd, today=None):
    today = today or date.today()
    return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))

def load_profile(username):
    conn = get_db_conn()
    try:
        row = conn.execute(
            "SELECT username, email, full_name, birth_date, avatar, created_at, role FROM users WHERE username = ?",
            (username,)).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    bd = parse_birth_date(row[3])
    age = calc_age(bd) if bd else None
    return {"username": row[0], "email": row[1] or "", "full_name": row[2] or "",
            "birth_date": bd.isoformat() if bd else "", "age": age,
            "is_adult": age is not None and age >= ADULT_AGE,
            "has_birth_date": bd is not None, "avatar": row[4] or "", 
            "member_since": row[5] or "", "role": row[6]}

CERT_AGE = {"TV-Y": 0, "TV-Y7": 7, "TV-G": 0, "TV-PG": 10, "TV-14": 14, "TV-MA": 18,
            "G": 0, "U": 0, "PG": 10, "PG-13": 13, "12A": 12, "R": 18, "NC-17": 18, "X": 18,
            "R-13": 13, "R-16": 16, "R-18": 18, "R18": 18, "RESTRICTED": 18}
CERT_COUNTRIES = ("US", "GB", "PH", "AU", "CA")
R18_KEYWORD_RE = re.compile(r"\b(erotic|erotica|sex|nudity|female nudity|male nudity|sexual|softcore|bdsm|"
                            r"adultery|infidelity|seductress|lust|prostitute|stripper|gore|slasher|"
                            r"extreme violence|vivamax|pink film)\b", re.I)
_FACTS_CACHE, _FACTS_LOCK = {}, threading.Lock()

def cert_age(raw):
    c = re.sub(r"\s+", "", str(raw or "")).upper()
    if not c:
        return None
    if c in CERT_AGE:
        return CERT_AGE[c]
    m = re.fullmatch(r"(\d{1,2})\+?", c)
    return int(m.group(1)) if m else None

def title_age_facts(d, media):
    if media == "tv":
        pairs = [(e.get("iso_3166_1"), e.get("rating")) for e in (d.get("content_ratings") or {}).get("results", [])]
    else:
        pairs = [(e.get("iso_3166_1"), next((x.get("certification") for x in e.get("release_dates", []) if x.get("certification")), None))
                 for e in (d.get("release_dates") or {}).get("results", [])]
    req = None
    for cc in CERT_COUNTRIES:
        for country, raw in pairs:
            if country == cc and cert_age(raw) is not None:
                req = cert_age(raw)
                break
        if req is not None:
            break
    kw = d.get("keywords") or {}
    kw_text = " ".join(k.get("name", "") for k in (kw.get("keywords") or kw.get("results") or []))
    companies = " ".join(c.get("name", "") for c in d.get("production_companies") or []).lower()
    titles = {str(d.get(k) or "").lower().strip() for k in ("title", "name", "original_title", "original_name")}
    gids = {x.get("id") for x in d.get("genres") or [] if isinstance(x, dict)}
    if d.get("adult") is True or not is_safe_non_porn(d):
        req = 18
    elif req is None and (titles & KNOWN_R18_TITLES or R18_KEYWORD_RE.search(kw_text) or "vivamax" in companies):
        req = 18
    kid = bool(gids & {10751, 10762, 16}) and not (gids & {27, 80, 53, 10752, 10768})
    return {"req": req, "kid": kid}

def facts_allow(f, ceiling):
    if ceiling >= 999:
        return True
    if f["req"] is not None:
        return f["req"] <= ceiling
    return True if ceiling > 12 else f["kid"]

def title_facts(media, tid):
    media = "tv" if media == "tv" else "movie"
    key = f"{media}_{tid}"
    with _FACTS_LOCK:
        if key in _FACTS_CACHE:
            return _FACTS_CACHE[key]
    d = tmdb(f"/{media}/{tid}", append_to_response="content_ratings,keywords" if media == "tv" else "release_dates,keywords")
    if not d.get("id"):
        return None
    facts = title_age_facts(d, media)
    with _FACTS_LOCK:
        _FACTS_CACHE[key] = facts
    return facts

def viewer_ceiling():
    if hasattr(g, "_ceiling"):
        return g._ceiling
    username = current_username()
    profile = load_profile(username) if username else None
    age = profile["age"] if profile else None
    g._ceiling = 17 if age is None else (999 if age >= 18 else (17 if age >= 13 else 12))
    return g._ceiling

def viewer_is_adult():
    return viewer_ceiling() >= 999

def _media_of(m, default="movie"):
    return "tv" if (m.get("media_type") or default) == "tv" else "movie"

def filter_for_viewer(items, default_media="movie"):
    ceiling = viewer_ceiling()
    if ceiling >= 999:
        return list(items)
    keys = list({(_media_of(m, default_media), m["id"]) for m in items if m.get("id") and not m.get("adult")})
    with ThreadPoolExecutor(max_workers=8) as pool:
        facts = dict(zip(keys, pool.map(lambda k: title_facts(*k), keys)))
    out = []
    for m in items:
        f = facts.get((_media_of(m, default_media), m.get("id")))
        if f and facts_allow(f, ceiling):
            out.append(m)
    return out

MINOR_RULE = ("\nThe viewer is under 18 or age-unverified. NEVER name, describe or recommend R-18/mature "
              "titles (explicit sex, nudity, graphic violence/gore). If asked about one, say it is not "
              "available for their account.")
MINOR_SAFE_REPLY = "That title isn't available for your account. Here are age-appropriate picks instead."

def reply_mentions_restricted(text):
    low = (text or "").lower()
    return any(len(t) >= 5 and re.search(rf"\b{re.escape(t)}\b", low) for t in KNOWN_R18_TITLES)


# --- MACHINE LEARNING MODULES ---
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

def update_user_genre_weights(username, movie_genres, weight_delta):
    conn = get_db_conn()
    row = conn.execute("SELECT genre_weights FROM users WHERE username = ?", (username,)).fetchone()
    try:
        weights = json.loads(row[0] or "{}") if row else {}
    except:
        weights = {}
        
    for g in movie_genres:
        if not g: continue
        current = weights.get(g, 1.0)
        weights[g] = max(0.1, min(4.0, current + weight_delta))
        
    conn.execute("UPDATE users SET genre_weights = ? WHERE username = ?", (json.dumps(weights), username))
    conn.commit()
    conn.close()

def get_collaborative_bonus(username, candidates):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT username, movie_id, vote_average FROM interactions")
    rows = c.fetchall()
    conn.close()
    
    if len(rows) < 5:
        return {m['id']: 0 for m in candidates}
        
    user_item = {}
    target_user_items = set()
    for u, m_id, v in rows:
        rating = float(v) if v else 5.0
        if u not in user_item: user_item[u] = {}
        user_item[u][m_id] = rating
        if u == username: target_user_items.add(m_id)
        
    if username not in user_item:
        return {m['id']: 0 for m in candidates}
        
    similarities = {}
    target_ratings = user_item[username]
    target_norm = np.sqrt(sum(r**2 for r in target_ratings.values()))
    
    for u, ratings in user_item.items():
        if u == username: continue
        dot = sum(target_ratings.get(m, 0) * r for m, r in ratings.items())
        u_norm = np.sqrt(sum(r**2 for r in ratings.values()))
        sim = dot / (target_norm * u_norm) if target_norm * u_norm else 0
        similarities[u] = sim
        
    bonuses = {}
    for m in candidates:
        m_id = m['id']
        if m_id in target_user_items:
            bonuses[m_id] = 0
            continue
        weighted_sum = 0
        sim_sum = 0
        for u, sim in similarities.items():
            if sim > 0 and m_id in user_item[u]:
                weighted_sum += sim * user_item[u][m_id]
                sim_sum += sim
        bonuses[m_id] = (weighted_sum / sim_sum) * 5 if sim_sum > 0 else 0
        
    return bonuses

def tfidf_semantic_search(query, candidates):
    if len(candidates) < 2: return candidates
    docs = [query.lower()]
    for m in candidates:
        text = f"{m.get('title','')} {m.get('name','')} {m.get('overview','')} {m.get('tagline','')} "
        kw = " ".join([k.get('name','') for k in (m.get('keywords', {}).get('keywords', []) or m.get('keywords', {}).get('results', []))])
        docs.append((text + kw).lower())
    
    vec = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = vec.fit_transform(docs)
        sim_scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    except ValueError:
        return candidates
        
    for i, m in enumerate(candidates):
        m['_bonus'] = m.get('_bonus', 0) + float(sim_scores[i]) * 40.0
        
    return sorted(candidates, key=lambda x: x.get('_bonus', 0), reverse=True)


# --- HTTP ENDPOINTS ---
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "CineMind Engine Live", "version": "21.0-Secure",
                    "database_tables": ["users", "watchlist", "favorites", "not_interested", "interactions", "audit_logs", "user_ratings"]})

@app.route("/api/verify", methods=["GET", "POST"])
@require_auth
def verify():
    return jsonify({"success": True, "username": g.username})

@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip().lower()
    password = str(data.get("password", ""))
    raw_genres = clean_genres(data.get("genres"))
    full_name = " ".join(str(data.get("full_name", "")).split())[:60]
    email = str(data.get("email", "")).strip().lower()
    bd = parse_birth_date(data.get("birth_date"))
    
    if not re.match(r"^[a-z0-9_.\-]{3,30}$", username):
        return jsonify({"success": False, "message": "Username must be 3-30 characters: letters, numbers, dots, dashes or underscores."}), 400
    if len(password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters."}), 400
    if not full_name:
        return jsonify({"success": False, "message": "Please enter your full name."}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"success": False, "message": "Please enter a valid email address."}), 400
    if bd is None:
        return jsonify({"success": False, "message": "Please enter a valid date of birth."}), 400
    if len(raw_genres) < 3:
        return jsonify({"success": False, "message": "Please pick at least 3 genres."}), 400
        
    genre_dict = {}
    for gid in raw_genres:
        if gid.isdigit() and int(gid) in GENRE_ID_TO_NAME:
            genre_dict[GENRE_ID_TO_NAME[int(gid)]] = 1.5
        else:
            genre_dict[gid.title()] = 1.5
            
    conn = get_db_conn()
    try:
        conn.execute(
            "INSERT INTO users (username, password, genres, genre_weights, email, full_name, birth_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, generate_password_hash(password), json.dumps(raw_genres), json.dumps(genre_dict), email, full_name, bd.isoformat()))
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        taken = "email" if "email" in str(e).lower() else "username"
        log_audit_event(username, "SIGNUP_DUPLICATE", f"Duplicate {taken} registration attempt")
        return jsonify({"success": False, "message": f"That {taken} is already taken."}), 409
    conn.close()
    
    log_audit_event(username, "USER_SIGNUP", "Account created")
    return jsonify({"success": True, "username": username, "genres": raw_genres,
                    "profile": load_profile(username),
                    "token": issue_token(username), "message": "Account created successfully!"})

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip().lower()
    password = str(data.get("password", ""))
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400
    conn = get_db_conn()
    row = conn.execute("SELECT password, genres, role FROM users WHERE username = ?", (username,)).fetchone()
    ok, saved_genres, user_role = False, [], "user"
    if row:
        stored = row[0] or ""
        user_role = row[2] or "user"
        try:
            saved_genres = clean_genres(json.loads(row[1] or "[]"))
        except Exception:
            saved_genres = []
        if stored.startswith(("pbkdf2:", "scrypt:")):
            ok = check_password_hash(stored, password)
        elif hmac.compare_digest(stored, hashlib.sha256(password.encode()).hexdigest()):
            ok = True 
            conn.execute("UPDATE users SET password = ? WHERE username = ?",
                         (generate_password_hash(password), username))
            conn.commit()
    conn.close()
    if ok:
        log_audit_event(username, "LOGIN_SUCCESS", f"Authenticated with role: {user_role}")
        return jsonify({"success": True, "username": username, "genres": saved_genres,
                        "profile": load_profile(username), "role": user_role,
                        "token": issue_token(username),
                        "message": "Login successful!"})
    log_audit_event(username, "LOGIN_FAILED", "Invalid password attempt")
    return jsonify({"success": False, "message": "Invalid username or password."}), 401

@app.route("/api/admin/audit-logs", methods=["GET"])
@require_auth
def get_audit_logs():
    username = g.username
    conn = get_db_conn()
    row = conn.execute("SELECT role FROM users WHERE username = ?", (username,)).fetchone()
    if not row or row[0] != 'admin':
        conn.close()
        log_audit_event(username, "UNAUTHORIZED_ACCESS", "Attempted to view audit logs")
        return jsonify({"success": False, "message": "Administrator privileges required."}), 403
        
    c = conn.cursor()
    c.execute("SELECT username, event_type, details, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT 40")
    logs = [{"username": r[0], "event_type": r[1], "details": r[2], "timestamp": r[3]} for r in c.fetchall()]
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    conn.close()
    return jsonify({"success": True, "audit_logs": logs, "total_registered_users": total_users})

@app.route("/api/profile", methods=["GET"])
@require_auth
def get_profile():
    return jsonify({"success": True, "profile": load_profile(g.username)})

@app.route("/api/profile", methods=["PUT"])
@require_auth
def update_profile():
    data = request.get_json(silent=True) or {}
    current = load_profile(g.username)
    updates = {}
    if "full_name" in data:
        updates["full_name"] = " ".join(str(data["full_name"]).split())[:60]
    if "email" in data:
        email = str(data["email"]).strip().lower()
        if email and not EMAIL_RE.match(email):
            return jsonify({"success": False, "message": "Please enter a valid email address."}), 400
        updates["email"] = email or None
    if data.get("birth_date"):
        if current["has_birth_date"]:
            if str(data["birth_date"]) != current["birth_date"]:
                return jsonify({"success": False, "message": "Date of birth can't be changed once set."}), 403
        else:
            bd = parse_birth_date(data["birth_date"])
            if bd is None:
                return jsonify({"success": False, "message": "Please enter a valid date of birth."}), 400
            updates["birth_date"] = bd.isoformat()
    if updates:
        conn = get_db_conn()
        try:
            conn.execute(f"UPDATE users SET {', '.join(k + ' = ?' for k in updates)} WHERE username = ?",
                         (*updates.values(), g.username))
            conn.commit()
            log_audit_event(g.username, "PROFILE_UPDATE", f"Updated fields: {list(updates.keys())}")
        except sqlite3.IntegrityError:
            return jsonify({"success": False, "message": "That email is already in use."}), 409
        finally:
            conn.close()
    return jsonify({"success": True, "profile": load_profile(g.username)})

@app.route("/api/profile/avatar", methods=["PUT", "DELETE"])
@require_auth
def profile_avatar():
    avatar = ""
    if request.method == "PUT":
        avatar = str((request.get_json(silent=True) or {}).get("avatar", ""))
        if len(avatar) > AVATAR_MAX_CHARS or not AVATAR_RE.match(avatar):
            return jsonify({"success": False, "message": "Please upload a PNG, JPEG or WebP image."}), 400
    conn = get_db_conn()
    conn.execute("UPDATE users SET avatar = ? WHERE username = ?", (avatar or None, g.username))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "profile": load_profile(g.username)})

@app.route("/api/age/check", methods=["POST"])
def age_check():
    ceiling = viewer_ceiling()
    if ceiling >= 999:
        return jsonify({"success": True, "is_adult": True, "blocked": [], "unknown": []})
    pairs = []
    for it in ((request.get_json(silent=True) or {}).get("items") or [])[:60]:
        try:
            pairs.append(("tv" if it.get("media_type") == "tv" else "movie", int(it.get("id"))))
        except (TypeError, ValueError, AttributeError):
            continue
    with ThreadPoolExecutor(max_workers=8) as pool:
        facts = list(pool.map(lambda p: title_facts(*p), pairs))
    return jsonify({"success": True, "is_adult": False, "ceiling": ceiling,
                    "blocked": [f"{m}_{i}" for (m, i), f in zip(pairs, facts) if f and not facts_allow(f, ceiling)],
                    "unknown": [f"{m}_{i}" for (m, i), f in zip(pairs, facts) if f is None]})

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
        update_user_genre_weights(username, format_exact_genres(movie), -0.1)
    else:
        try:
            c.execute(f"INSERT OR REPLACE INTO {table} (username, movie_id, title, poster, vote_average, media_type) VALUES (?, ?, ?, ?, ?, ?)",
                      (username, movie_id, title, movie.get("poster") or "", movie.get("vote_average", 0.0), movie.get("media_type", "movie")))
            c.execute("INSERT INTO interactions (username, movie_id, title, action, vote_average) VALUES (?, ?, ?, ?, ?)",
                      (username, movie_id, title, 'like' if lib_type == 'favorites' else 'watched', movie.get("vote_average", 0.0)))
            update_user_genre_weights(username, format_exact_genres(movie), 0.2 if lib_type == "favorites" else 0.1)
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({"success": False, "message": "User account not found in database."}), 400
        action = "added"
    conn.commit()
    conn.close()
    log_audit_event(username, f"LIBRARY_{action.upper()}", f"Toggled '{title}' in {table}")
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
        update_user_genre_weights(username, format_exact_genres(movie), -0.3)
    except sqlite3.IntegrityError:
        pass
    conn.close()
    log_audit_event(username, "NOT_INTERESTED_HIDE", f"Eliminated concept '{title}' ({movie_id})")
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
        
    c.execute("SELECT genre_weights FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    
    try:
        weights = json.loads(row[0] or "{}") if row else {}
        top_moods = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:3]
        dominant_mood = " • ".join([k for k,v in top_moods]) if top_moods else "Multi-Condition Neural Match"
    except:
        dominant_mood = "Multi-Condition Neural Match"

    rated = [r[1] for r in inter if r[1]]
    return jsonify({
        "username": username,
        "total_recommendations_viewed": len(inter), "total_liked": counts["favorites"],
        "total_watchlist": counts["watchlist"], "total_not_interested": counts["not_interested"],
        "average_rating_of_interest": round(sum(rated) / len(rated), 2) if rated else 0.0,
        "dominant_mood": dominant_mood,
        "genre_distribution": {"Drama": 30, "Sci-Fi": 22, "BL / GL": 18, "Anime": 15, "Docs & Sports": 15},
    })

# --- RATINGS & REVIEWS ENDPOINTS ---
def get_title_ratings_internal(media_type, movie_id, username):
    conn = get_db_conn()
    c = conn.cursor()
    
    c.execute("SELECT AVG(rating), COUNT(rating) FROM user_ratings WHERE movie_id = ? AND media_type = ?", (movie_id, media_type))
    comm_row = c.fetchone()
    community = {"average": round(comm_row[0], 2), "count": comm_row[1]} if comm_row and comm_row[1] > 0 else None
    
    mine = None
    if username:
        c.execute("SELECT rating, review_body FROM user_ratings WHERE username = ? AND movie_id = ? AND media_type = ?", (username, movie_id, media_type))
        my_row = c.fetchone()
        if my_row:
            mine = {"rating": my_row[0], "review": my_row[1]}
            
    prefs = {"genres": {}, "tags": {}}
    if username:
        r = conn.execute("SELECT genre_weights FROM users WHERE username = ?", (username,)).fetchone()
        try:
            prefs["genres"] = json.loads(r[0] or "{}") if r else {}
        except:
            pass
            
    conn.close()
    return jsonify({"success": True, "community": community, "mine": mine, "preferences": prefs})

@app.route('/api/ratings/mine', methods=['GET'])
@require_auth
def my_ratings():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT movie_id, media_type, rating FROM user_ratings WHERE username = ?", (g.username,))
    rows = c.fetchall()
    conn.close()
    ratings = {f"{r[1]}_{r[0]}": r[2] for r in rows}
    return jsonify({"success": True, "ratings": ratings})

@app.route('/api/me/preferences', methods=['GET'])
@require_auth
def my_preferences():
    conn = get_db_conn()
    row = conn.execute("SELECT genre_weights FROM users WHERE username = ?", (g.username,)).fetchone()
    conn.close()
    weights = {}
    try:
        weights = json.loads(row[0] or "{}") if row else {}
    except:
        pass
    return jsonify({"success": True, "preferences": {"genres": weights, "tags": {}}})

@app.route('/api/ratings/<media_type>/<int:movie_id>', methods=['PUT'])
@require_auth
def save_rating(media_type, movie_id):
    data = request.get_json(silent=True) or {}
    rating = data.get('rating')
    meta = data.get('meta') or {}
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"success": False, "message": "Rating must be an integer between 1 and 5."}), 400
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO user_ratings (username, movie_id, media_type, rating) 
        VALUES (?, ?, ?, ?)
        ON CONFLICT(username, movie_id, media_type) 
        DO UPDATE SET rating = excluded.rating, updated_at = CURRENT_TIMESTAMP
    """, (g.username, movie_id, media_type, rating))
    conn.commit()
    conn.close()
    
    if meta.get("genres"):
        weight_shift = (rating - 3) * 0.1 
        update_user_genre_weights(g.username, meta["genres"], weight_shift)

    return get_title_ratings_internal(media_type, movie_id, g.username)

@app.route('/api/ratings/<media_type>/<int:movie_id>', methods=['DELETE'])
@require_auth
def delete_rating(media_type, movie_id):
    conn = get_db_conn()
    conn.execute("DELETE FROM user_ratings WHERE username = ? AND movie_id = ? AND media_type = ?", 
                 (g.username, movie_id, media_type))
    conn.commit()
    conn.close()
    return get_title_ratings_internal(media_type, movie_id, g.username)

@app.route('/api/titles/<media_type>/<int:movie_id>/ratings', methods=['GET'])
def get_title_ratings(media_type, movie_id):
    username = current_username()
    return get_title_ratings_internal(media_type, movie_id, username)

@app.route('/api/titles/ratings/batch', methods=['POST'])
def community_batch_ratings():
    data = request.get_json(silent=True) or {}
    keys = data.get("keys", [])
    if not keys:
        return jsonify({"communities": {}})
    conn = get_db_conn()
    c = conn.cursor()
    results = {}
    for key in keys:
        try:
            m_type, m_id = key.split('_')
            c.execute("SELECT AVG(rating), COUNT(rating) FROM user_ratings WHERE movie_id = ? AND media_type = ?", (int(m_id), m_type))
            row = c.fetchone()
            if row and row[1] > 0:
                results[key] = {"average": round(row[0], 2), "count": row[1]}
        except:
            continue
    conn.close()
    return jsonify({"communities": results})

@app.route('/api/reviews/<media_type>/<int:movie_id>', methods=['PUT'])
@require_auth
def save_review(media_type, movie_id):
    data = request.get_json(silent=True) or {}
    body = str(data.get('body') or "").strip()[:2000]
    
    if not body:
        return delete_review(media_type, movie_id)
        
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM user_ratings WHERE username = ? AND movie_id = ? AND media_type = ?", (g.username, movie_id, media_type))
    if not c.fetchone():
        c.execute("INSERT INTO user_ratings (username, movie_id, media_type, rating) VALUES (?, ?, ?, 3)", (g.username, movie_id, media_type))
        
    c.execute("UPDATE user_ratings SET review_body = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ? AND movie_id = ? AND media_type = ?",
              (body, g.username, movie_id, media_type))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "body": body})

@app.route('/api/reviews/<media_type>/<int:movie_id>', methods=['DELETE'])
@require_auth
def delete_review(media_type, movie_id):
    conn = get_db_conn()
    conn.execute("UPDATE user_ratings SET review_body = NULL WHERE username = ? AND movie_id = ? AND media_type = ?",
                 (g.username, movie_id, media_type))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/titles/<media_type>/<int:movie_id>/reviews', methods=['GET'])
def list_reviews(media_type, movie_id):
    limit = min(int(request.args.get('limit', 5)), 20)
    offset = int(request.args.get('offset', 0))
    username = current_username()
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("""
        SELECT username, rating, review_body, updated_at 
        FROM user_ratings 
        WHERE movie_id = ? AND media_type = ? AND review_body IS NOT NULL AND review_body != ''
        ORDER BY updated_at DESC
        LIMIT ? OFFSET ?
    """, (movie_id, media_type, limit + 1, offset))
    rows = c.fetchall()
    conn.close()
    has_more = len(rows) > limit
    reviews = []
    for r in rows[:limit]:
        reviews.append({
            "username": r[0],
            "rating": r[1],
            "body": r[2],
            "created_at": r[3],
            "mine": r[0] == username
        })
    return jsonify({"success": True, "reviews": reviews, "has_more": has_more})

# --- DATA FETCHING & DISCOVER ---
def tmdb(path, **params):
    params["api_key"] = TMDB_API_KEY
    params.setdefault("include_adult", "false")
    try:
        r = requests.get(f"{TMDB}{path}", params=params, timeout=6)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}

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
    items, seen, pool = [], set(), []
    for page in (1, 2, 3):
        for m in tmdb(f"/discover/{media}", page=page, **params).get("results", []):
            if m.get("id") in seen or not m.get("poster_path") or not is_safe_non_porn(m):
                continue
            seen.add(m["id"])
            m["media_type"] = media
            pool.append(m)
    for m in filter_for_viewer(pool, media)[:10]:
        item = card(m, media)
        item["rank"] = len(items) + 1
        items.append(item)
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
    items = filter_for_viewer(items)
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
                "similar_to": [], "direct_reply": replies.get(special_cat, "Matched special category.")}
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

def extract_intent(message, history, username="Guest", fav_genres=None, client_guesses=None, minor=False):
    local = smart_local_nlp_parse(message, history, username, fav_genres)
    ctx = "\n".join(f"{'User' if h.get('role') == 'user' else 'Nova'}: {h.get('content')}"
                    for h in (history or [])[-10:] if isinstance(h, dict) and h.get("content")) or "No prior messages."
    llm = groq_json(PARSE_PROMPT + (MINOR_RULE if minor else ""),
                    f"User: {username}\nFavorite Genres: {', '.join(fav_genres or [])}\nHistory:\n{ctx}\n\nLatest Request: {message}")
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

def find_movies(intent, raw_query=""):
    special_cat = intent.get("special_category")
    strict_no_animation = special_cat in ("SPORTS", "DOC") or "documentary" in (intent.get("genres") or [])
    if intent.get("intent") == "plot_search" and not special_cat:
        found = plot_search(intent)
        if found:
            return found
            
        cands_raw = []
        for w in (intent.get("mood_keywords") or raw_query.split())[:3]:
            cands_raw.extend(tmdb("/search/multi", query=w).get("results", []))
        cands_raw = [m for m in cands_raw if m.get("poster_path") and is_safe_non_porn(m) and m.get("media_type") in ("movie", "tv")]
        if cands_raw:
            return tfidf_semantic_search(raw_query, cands_raw)
            
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

def rank(cands, intent, seen_ids, disliked_titles=None, disliked_keywords=None, username=None):
    conn = get_db_conn()
    row = conn.execute("SELECT genre_weights FROM users WHERE username = ?", (username,)).fetchone() if username else None
    conn.close()
    
    user_weights = {}
    try:
        user_weights = json.loads(row[0] or "{}") if row else {}
    except: pass
    
    cf_bonuses = get_collaborative_bonus(username, cands) if username else {}

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
                
        item_genres = format_exact_genres(m)
        genre_dot_product = 0
        for g in item_genres:
            genre_dot_product += user_weights.get(g, 1.0)
        avg_genre_weight = (genre_dot_product / len(item_genres)) if item_genres else 1.0
                
        pop = min((m.get("popularity") or 0) / 100, 1.0)
        cf_score = cf_bonuses.get(m['id'], 0) * 2.0 
        
        m["_score"] = ((m.get("vote_average") or 0) * 0.7 * avg_genre_weight) + (pop * 1.5) + m.get("_bonus", 0) + cf_score
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

def explain(message, username, movies, intent, minor=False):
    listing = [{"id": m["id"], "title": m.get("title") or m.get("name"),
                "year": (m.get("release_date") or m.get("first_air_date") or "")[:4],
                "overview": (m.get("overview") or "")[:200]} for m in movies[:8]]
    system = (f"You are Nova, a flawless AI cinema companion talking to {username}. "
              'CRITICAL: Base your response ONLY on the provided overviews. Do NOT invent plot details. '
              'Return ONLY JSON: {"reply": "2 engaging, 100% accurate sentences", '
              '"reasons": {"<id>": "1 concise sentence confirming the match based strictly on the overview"}}. Only mention listed titles.'
              + (MINOR_RULE if minor else ""))
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

    minor = not viewer_is_adult()
    intent = extract_intent(message, history, username, fav_genres, data.get("client_guesses") or [], minor=minor)
    intent["_media"] = media_filter
    intent_type = intent.get("intent", "recommend")
    
    if intent_type in ("chitchat", "question") and not intent.get("plot_guesses") and not intent.get("genres") and not intent.get("special_category"):
        reply = intent.get("direct_reply") or f"I'm Nova, your AI cinema companion, {username}. Ask me any movie question."
        if minor and reply_mentions_restricted(reply):
            reply = MINOR_SAFE_REPLY
        return jsonify({"reply": reply,
                        "movies": [], "intent": intent_type, "success": True})
                        
    if intent_type == "recommend" and not intent.get("genres") and not intent.get("plot_guesses") and not intent.get("special_category"):
        if fav_genres:
            intent["genres"] = [x.lower() for x in fav_genres[:3]]
        elif intent.get("origin_country"):
            intent["genres"] = COUNTRY_DEFAULT_GENRES.get(intent["origin_country"], ["drama", "romance"])
            
    if not intent.get("origin_country") and selected_country and intent_type != "plot_search" and not intent.get("special_category"):
        intent["origin_country"] = selected_country
        
    cands = find_movies(intent, message)
    
    if not cands and len(message.split()) < 4 and intent_type != "plot_search":
        cands = [m for m in tmdb("/search/multi", query=message).get("results", [])
                 if is_safe_non_porn(m) and m.get("poster_path") and m.get("media_type") in ("movie", "tv")]
                 
    if media_filter:
        cands = [m for m in cands if (m.get("media_type") or "movie") == media_filter]
        
    seen_ids, disliked_keywords = get_seen_and_disliked(username)
    
    real_username = username if username != "Guest" else None
    top = rank(cands, intent, seen_ids, disliked_titles, disliked_keywords, real_username) or cands[:12]
    
    removed = False
    if minor:
        before = len(top)
        top = filter_for_viewer(top)
        removed = len(top) != before
    
    if not top:
        msg = MINOR_SAFE_REPLY if (minor and removed) else (intent.get("direct_reply") or f"I couldn't find a 100% accurate match for that, {username}. Could you give me another detail?")
        if minor and reply_mentions_restricted(msg):
            msg = MINOR_SAFE_REPLY
        return jsonify({"reply": msg,
                        "movies": [], "intent": intent_type, "success": True})
                        
    ex = explain(message, username, top, intent, minor=minor)
    reasons = ex.get("reasons", {}) if isinstance(ex.get("reasons"), dict) else {}
    reply = ex.get("reply") or intent.get("direct_reply") or f"Here are my top matches for '{message}', {username}."
    if minor and (removed or reply_mentions_restricted(reply)):
        reply = MINOR_SAFE_REPLY
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
    return jsonify({"ai_forecast": "Regional charts, ML matrix models, and collaborative filtering online.",
                    "trending_genres": ["Boys' Love (BL) and Girls' Love (GL)", "Real-Life Sports and True-Crime Docs", "Anime"]})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
