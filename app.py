import os
import re
import json
import html
import sqlite3
import hashlib
import urllib.parse
from datetime import date

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)


def detect_env_key(prefix, default_names, fallback=""):
    """Automatically finds your API key on Render even if named differently or pasted in the Key column."""
    for name in default_names:
        val = os.environ.get(name, "").strip().strip('"').strip("'")
        if val:
            return val
    for k, v in os.environ.items():
        k_clean = k.strip().strip('"').strip("'")
        v_clean = v.strip().strip('"').strip("'")
        if prefix and v_clean.startswith(prefix):
            return v_clean
        if prefix and k_clean.startswith(prefix):
            return k_clean
    return fallback


TMDB_API_KEY = detect_env_key("", ["TMDB_API_KEY", "TMDB_KEY", "TMDB"], "7c7e21b0fe58e5868e262c9bd6b8e7e9")
GROQ_API_KEY = detect_env_key("gsk_", ["GROQ_API_KEY", "GROQ_KEY", "GROQ", "AI_API_KEY", "OPENAI_API_KEY"], "")
OMDB_API_KEY = detect_env_key("", ["OMDB_API_KEY", "OMDB_KEY", "OMDB"], "554ae239")

DB_NAME = "cinemind.db"
TMDB = "https://api.themoviedb.org/3"

GENRES = {
    "action": 28, "adventure": 12, "animation": 16, "comedy": 35, "crime": 80,
    "documentary": 99, "drama": 18, "family": 10751, "fantasy": 14, "history": 36,
    "horror": 27, "music": 10402, "mystery": 9648, "romance": 10749,
    "sci-fi": 878, "science fiction": 878, "thriller": 53, "war": 10752, "western": 37,
}
GENRE_LIST = ", ".join(GENRES.keys())

COUNTRY_DEFAULT_GENRES = {
    "PH": ["drama", "romance", "comedy", "horror"],
    "KR": ["drama", "thriller", "romance", "action"],
    "TH": ["drama", "romance", "comedy", "horror"],
    "JP": ["animation", "fantasy", "sci-fi", "drama"],
    "IN": ["action", "drama", "romance", "comedy"],
    "ES": ["thriller", "crime", "drama"],
    "FR": ["drama", "romance", "comedy"],
    "GB": ["drama", "crime", "mystery"],
    "US": ["action", "sci-fi", "comedy", "drama"]
}

# Strict Pornographic & Erotic Content Blocklist
PORN_BLOCK_WORDS = [
    "porn", "porno", "pornographic", "xxx", "erotic", "erotica", "hentai", "jav",
    "av idol", "sex tape", "playboy", "penthouse", "nude", "nudity", "stripper",
    "prostitute", "prostitution", "brothel", "kama sutra", "bdsm", "fetish",
    "orgasm", "milf", "stepmom", "stepsister", "softcore", "pink film", "vivamax",
    "brazzers", "onlyfans", "emmanuelle", "nymphomaniac", "caligula",
    "365 days", "fifty shades", "scorpio nights", "silip", "uhaw", "laman",
    "boso", "sikretong malupit", "macho dancer", "tubero", "pamasahe",
    "selina's gold", "us x her", "bela luna", "kiskisan", "salitan",
    "lampas langit", "virgin forest", "kaliwaan", "purgatoryo", "doblado",
    "paupahan", "ang babaeng nawawala sa sarili", "kinsenas, katapusan",
    "boy bastos", "palitan", "tag-init", "balinsasayaw", "sugar baby",
    "tayuan", "haslers", "dilig", "kaluskos", "unli life", "totnak", "kantot",
    "libog", "malibog", "pokpok", "parausan", "halinghing", "pagnanasa",
    "angeli khang", "azi acosta", "aj raval", "robb guinto", "christine bermas",
    "ayanna misola", "cara gonzales", "yen durano", "apple dy", "denise esteban"
]

PORN_BLOCK_REGEX = re.compile(
    r"\b(porn|porno|xxx|erotic|erotica|hentai|jav|sex tape|playboy|penthouse|nudity|stripper|prostitute|brothel|bdsm|fetish|orgasm|milf|softcore|pink film|vivamax|brazzers|onlyfans|nymphomaniac|threesome|foreplay|voyeur|voyeurism|adultery|mistress|seductress|lustful|kinky|sexploitation|bomba film|bold star)\b",
    re.I
)

KNOWN_R18_TITLES = {
    "deadpool", "deadpool 2", "deadpool & wolverine", "logan", "joker", "parasite",
    "oldboy", "oppenheimer", "john wick", "saw", "hereditary", "midsommar",
    "the wolf of wall street", "pulp fiction", "fight club", "gone girl",
    "shutter island", "se7en", "american psycho", "saltburn", "the handmaiden",
    "squid game", "the boys", "euphoria", "game of thrones", "breaking bad"
}


def is_safe_non_porn(m):
    if not m or m.get("adult") is True:
        return False
    title = (m.get("title") or m.get("name") or "").lower().strip()
    orig_title = (m.get("original_title") or m.get("original_name") or "").lower().strip()
    overview = (m.get("overview") or "").lower()
    text = f"{title} {orig_title} {overview}"

    if PORN_BLOCK_REGEX.search(text):
        return False
    for bad in PORN_BLOCK_WORDS:
        if title == bad or orig_title == bad or bad in text:
            return False
    if (m.get("vote_count") or 0) < 35 and re.search(r"\b(sex|sexual|nude|naked|seduce|seduction|lust|affair|steamy|intimate|passion|forbidden desire|pleasure)\b", text):
        return False
    return True


def is_genuine_r18(m):
    if not m or not is_safe_non_porn(m):
        return False
    title_l = (m.get("title") or m.get("name") or "").lower().strip()
    if title_l in KNOWN_R18_TITLES:
        return True
    gids = m.get("genre_ids") or []
    overview = (m.get("overview") or "").lower()
    if (27 in gids or 80 in gids or 53 in gids) and re.search(r"\b(murder|serial killer|brutal|blood|gore|cartel|massacre|psychopath|torture|slasher)\b", overview):
        return True
    return False


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, genres TEXT DEFAULT '[]')''')
    try:
        c.execute("ALTER TABLE users ADD COLUMN genres TEXT DEFAULT '[]'")
    except Exception:
        pass
    c.execute('''CREATE TABLE IF NOT EXISTS watchlist (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, movie_id INTEGER NOT NULL, title TEXT NOT NULL, poster TEXT, vote_average REAL, UNIQUE(username, movie_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS favorites (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, movie_id INTEGER NOT NULL, title TEXT NOT NULL, poster TEXT, vote_average REAL, UNIQUE(username, movie_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS interactions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, movie_id INTEGER NOT NULL, title TEXT NOT NULL, action TEXT NOT NULL, vote_average REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()


@app.route("/", methods=["GET"])
def home():
    active_key = GROQ_API_KEY or detect_env_key("gsk_", ["GROQ_API_KEY", "GROQ_KEY", "GROQ"], "")
    return jsonify({
        "status": "CineMind Universal AI Engine Live",
        "version": "22.0",
        "groq_key_detected": bool(active_key)
    })


@app.route("/api/debug-ai", methods=["GET"])
def debug_ai():
    """Diagnostic route to verify Groq API key status on Render."""
    active_key = GROQ_API_KEY or detect_env_key("gsk_", ["GROQ_API_KEY", "GROQ_KEY", "GROQ"], "")
    if not active_key:
        return jsonify({"groq_configured": False, "reason": "No gsk_ key found in Render Environment variables."})
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {active_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": "Return JSON: {\"ok\": true}"}],
                "response_format": {"type": "json_object"}
            },
            timeout=8
        )
        return jsonify({"groq_configured": True, "http_status": r.status_code, "response": r.json()})
    except Exception as e:
        return jsonify({"groq_configured": True, "error": str(e)})


@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")
    genres = data.get("genres") or []
    if not username or len(password) < 6:
        return jsonify({"success": False, "message": "Username required and password must be 6+ characters."}), 400
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("INSERT INTO users (username, password, genres) VALUES (?, ?, ?)",
                     (username, generate_password_hash(password), json.dumps(genres)))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "username": username, "genres": genres, "message": "Account created successfully!"})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Username already exists."}), 400


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")
    conn = sqlite3.connect(DB_NAME)
    row = conn.execute("SELECT password, genres FROM users WHERE username = ?", (username,)).fetchone()
    ok = False
    saved_genres = []
    if row:
        stored = row[0]
        try:
            saved_genres = json.loads(row[1] or "[]")
        except Exception:
            saved_genres = []
        if stored.startswith(("pbkdf2:", "scrypt:")):
            ok = check_password_hash(stored, password)
        elif stored == hashlib.sha256(password.encode()).hexdigest():
            ok = True
            conn.execute("UPDATE users SET password = ? WHERE username = ?",
                         (generate_password_hash(password), username))
            conn.commit()
    conn.close()
    if ok:
        return jsonify({"success": True, "username": username, "genres": saved_genres, "message": "Login successful!"})
    return jsonify({"success": False, "message": "Invalid username or password."}), 401


@app.route("/api/user/library", methods=["GET"])
def get_library():
    username = request.args.get("username", "").strip().lower()
    if not username:
        return jsonify({"watchlist": [], "favorites": [], "genres": []})
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT movie_id, title, poster, vote_average FROM watchlist WHERE username = ?", (username,))
    watchlist = [{"id": r[0], "title": r[1], "poster": r[2], "vote_average": r[3]} for r in c.fetchall()]
    c.execute("SELECT movie_id, title, poster, vote_average FROM favorites WHERE username = ?", (username,))
    favorites = [{"id": r[0], "title": r[1], "poster": r[2], "vote_average": r[3]} for r in c.fetchall()]
    c.execute("SELECT genres FROM users WHERE username = ?", (username,))
    g_row = c.fetchone()
    conn.close()
    saved_genres = []
    if g_row and g_row[0]:
        try:
            saved_genres = json.loads(g_row[0])
        except Exception:
            pass
    return jsonify({"watchlist": watchlist, "favorites": favorites, "genres": saved_genres})


@app.route("/api/user/library/toggle", methods=["POST"])
def toggle_library():
    data = request.get_json() or {}
    username = data.get("username", "").strip().lower()
    lib_type = data.get("type")
    movie = data.get("movie", {})
    if not username or not lib_type or not movie:
        return jsonify({"success": False, "message": "Invalid payload."}), 400
    movie_id = movie.get("id")
    title = movie.get("title") or movie.get("name")
    poster = movie.get("poster") or ""
    vote_average = movie.get("vote_average", 0.0)
    table = "watchlist" if lib_type == "watchlist" else "favorites"
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(f"SELECT id FROM {table} WHERE username = ? AND movie_id = ?", (username, movie_id))
    if c.fetchone():
        c.execute(f"DELETE FROM {table} WHERE username = ? AND movie_id = ?", (username, movie_id))
        action = "removed"
    else:
        c.execute(f"INSERT OR REPLACE INTO {table} (username, movie_id, title, poster, vote_average) VALUES (?, ?, ?, ?, ?)",
                  (username, movie_id, title, poster, vote_average))
        action = "added"
        c.execute("INSERT INTO interactions (username, movie_id, title, action, vote_average) VALUES (?, ?, ?, ?, ?)",
                  (username, movie_id, title, 'like' if lib_type == 'favorites' else 'watched', vote_average))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "action": action})


@app.route("/api/user/insights", methods=["GET"])
def get_insights():
    username = request.args.get("username", "").strip().lower()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT action, vote_average FROM interactions WHERE username = ?", (username,))
    interactions = c.fetchall()
    c.execute("SELECT COUNT(*) FROM favorites WHERE username = ?", (username,))
    total_liked = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM watchlist WHERE username = ?", (username,))
    total_watchlist = c.fetchone()[0]
    conn.close()
    rated = [r[1] for r in interactions if r[1]]
    avg_rating = sum(rated) / len(rated) if rated else 0.0
    return jsonify({
        "username": username or "Guest",
        "total_recommendations_viewed": len(interactions),
        "total_liked": total_liked,
        "total_watchlist": total_watchlist,
        "average_rating_of_interest": round(avg_rating, 2),
        "dominant_mood": "Multi-API Neural Match",
        "genre_distribution": {"Drama": 35, "Sci-Fi": 25, "Romance": 20, "Action": 20}
    })


@app.route("/api/omdb", methods=["GET"])
def omdb_info():
    title = request.args.get("title", "")
    year = request.args.get("year", "")
    if not OMDB_API_KEY or not title:
        return jsonify({})
    try:
        o = requests.get("https://www.omdbapi.com/",
                         params={"apikey": OMDB_API_KEY, "t": title, "y": year}, timeout=4).json()
        if o.get("Response") == "True":
            return jsonify({"imdbRating": o.get("imdbRating"), "runtime": o.get("Runtime"),
                            "director": o.get("Director"), "awards": o.get("Awards")})
    except Exception:
        pass
    return jsonify({})


# ------------------------- UNIVERSAL AI + IMDb/TMDB ID RESOLVER ENGINE -------------------------
PARSE_PROMPT = f"""You are Nova, an encyclopedic AI expert on all world cinema, TV series, K-dramas, Thai/Asian BL (Boys' Love) dramas, anime, Western films, and indie movies.
Analyze the user's latest message, any Web Search Hints provided, and the conversation history.
NEVER suggest pornographic, erotic, softcore, or adult-only films.
Return ONLY a valid JSON object with these exact keys:
{{
  "intent": "plot_search" | "recommend" | "similar_to" | "question" | "chitchat",
  "media_preference": "all" | "movie" | "tv",
  "plot_guesses": [
    {{"title": "Exact Movie or TV Series Title", "year": 2021, "media_type": "movie" | "tv", "why": "1-sentence explanation of how this exact title matches the user's description"}}
  ],
  "genres": [list of matching genres from: {GENRE_LIST}],
  "exclude_genres": [genres the user explicitly does NOT want],
  "year_from": integer or null,
  "year_to": integer or null,
  "min_rating": number 0-10 or null,
  "language": ISO 639-1 code like "ko", "ja", "tl", "th", "es", "fr", "hi" or null,
  "origin_country": ISO 3166-1 code like "KR", "PH", "JP", "TH", "US", "GB", "IN", "FR", "ES", "TW", "CN" or null,
  "sort": "popularity" | "rating" | "newest",
  "mood_keywords": [2-4 specific plot/theme keywords],
  "similar_to": [movie or series titles the user says they liked],
  "exclude_titles": [titles the user wants to avoid],
  "direct_reply": "Your warm, accurate, and specific response! If the user describes a plot, logline, or asks 'what movie/series is about...', name the #1 exact matching title in your first sentence and explain why it matches!"
}}

CRITICAL RULES:
1. Whenever a user describes a plot, premise, logline, character names, or scene (even if the user says 'what movie is about...' when it is actually a TV series/drama like 'Bad Buddy' or 'Not Me'), MUST set "intent": "plot_search" and put your best 5-6 real-world title matches in "plot_guesses" (most accurate #1 first).
2. NEVER put URLs, website names, or domain names inside "title"—only real movie or TV series titles!
"""


def tmdb(path, **params):
    params["api_key"] = TMDB_API_KEY
    params["include_adult"] = "false"
    try:
        r = requests.get(f"{TMDB}{path}", params=params, timeout=6)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def parse_json_safely(raw_text):
    if not raw_text:
        return None
    raw_text = raw_text.strip()
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.I)
    raw_text = re.sub(r"\s*```$", "", raw_text)
    try:
        return json.loads(raw_text)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", raw_text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    return None


def llm_json(system, user, temperature=0.15, timeout=14):
    """
    Calls Groq (llama-3.3-70b-versatile, llama-3.1-8b-instant, gemma2-9b-it)
    and falls back to Pollinations Free AI if needed.
    """
    active_groq_key = GROQ_API_KEY or detect_env_key("gsk_", ["GROQ_API_KEY", "GROQ_KEY", "GROQ"], "")
    if active_groq_key:
        for model_name in ("llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"):
            try:
                res = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {active_groq_key}", "Content-Type": "application/json"},
                    json={
                        "model": model_name,
                        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                        "response_format": {"type": "json_object"},
                        "temperature": temperature,
                    },
                    timeout=timeout,
                )
                if res.status_code == 200:
                    parsed = parse_json_safely(res.json()["choices"][0]["message"]["content"])
                    if isinstance(parsed, dict):
                        return parsed
            except Exception:
                pass

    # Keyless Free AI Fallback
    try:
        res = requests.post(
            "https://text.pollinations.ai/openai",
            headers={"Content-Type": "application/json", "User-Agent": "CineMind/22.0"},
            json={
                "model": "openai",
                "messages": [
                    {"role": "system", "content": system + "\nReturn ONLY valid JSON."},
                    {"role": "user", "content": user}
                ],
                "temperature": temperature,
            },
            timeout=10,
        )
        if res.status_code == 200:
            data = res.json() if res.text.strip().startswith("{") else {}
            if "choices" in data:
                parsed = parse_json_safely(data["choices"][0]["message"]["content"])
            else:
                parsed = parse_json_safely(res.text)
            if isinstance(parsed, dict) and ("plot_guesses" in parsed or "intent" in parsed or "reply" in parsed):
                return parsed
    except Exception:
        pass

    return None


def is_valid_clean_title(title_str):
    """Strictly rejects any URL, breadcrumb, domain name, or search junk from ever being treated as a title!"""
    if not title_str or len(title_str) < 2 or len(title_str) > 65:
        return False
    low = title_str.lower()
    # Reject anything that looks like a URL, domain, or breadcrumb (fixes the 'youtube.comhttps://...' bug!)
    if any(bad in low for bad in [
        "http:", "https:", "www.", ".com", ".org", ".net", ".io", ".tv",
        "›", "://", "youtube", "google", "yahoo", "duckduckgo", "bing",
        "reddit", "quora", "tiktok", "facebook", "instagram", "twitter",
        "top 10", "best ", "list of", "movies like", "watch online", "full movie"
    ]):
        return False
    return True


def clean_extracted_web_title(raw_html_title):
    """
    Removes nested <span> breadcrumbs (which Yahoo/Bing inject inside <a> tags)
    and extracts ONLY the clean movie or TV series title.
    """
    # 1. Strip any nested <span>...</span> or <cite>...</cite> breadcrumb blocks FIRST!
    no_spans = re.sub(r"<(span|cite|div)[^>]*>.*?</\1>", " ", raw_html_title, flags=re.I | re.S)
    t = html.unescape(re.sub(r"<[^>]+>", " ", no_spans))
    # 2. Strip any raw URLs or domain breadcrumbs if still present
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"\b\w+\.(com|org|net|tv|io)\b[^\s]*", " ", t, flags=re.I)
    t = re.sub(r"^.*?›\s*", "", t)
    t = re.sub(r"\s+", " ", t).strip()

    yr_match = re.search(r"\((?:[^\)]*?)((?:19|20)\d{2})(?:[^\)]*?)\)", t)
    year = int(yr_match.group(1)) if yr_match else None
    is_tv = bool(re.search(r"\b(tv series|tv show|series|drama|season|episode|mydramalist|serializd)\b", t, re.I))

    # Strip website suffixes (" - IMDb", " | MyDramaList", etc.)
    t = re.sub(r"\s*[\-\|—:]\s*(IMDb|MyDramaList|Serializd|FanBolt|The Movie Database|TMDB|Wikipedia|Rotten Tomatoes|Letterboxd|JustWatch|MyAsianTV|Netflix|Viki|GagaOOLala|Watch).*$", "", t, flags=re.I)
    t = re.sub(r"\s*\([^\)]*\).*$", "", t).strip()
    t = re.sub(r"^(Watch|Review|Plot of|Where to Watch|Synopsis of)\s+", "", t, flags=re.I).strip()
    t = t.strip(" -|—:\"'›»")

    if not is_valid_clean_title(t):
        return None, None, None
    return t, year, ("tv" if is_tv else None)


def resolve_imdb_or_tmdb_ids_from_html(raw_html):
    """
    Scans search result HTML for direct IMDb IDs (tt1234567) or TMDB URLs (themoviedb.org/movie/123 or /tv/123)
    and resolves the 100% official title & poster directly from TMDB's API!
    """
    resolved = []
    seen = set()

    # 1. Extract direct TMDB URLs (/movie/12345 or /tv/12345)
    for m_type, tid in re.findall(r"themoviedb\.org/(movie|tv)/(\d+)", raw_html, flags=re.I):
        key = f"{m_type.lower()}_{tid}"
        if key not in seen:
            seen.add(key)
            d = tmdb(f"/{m_type.lower()}/{tid}")
            if d and d.get("id") and is_safe_non_porn(d):
                t_name = d.get("title") or d.get("name")
                yr = (d.get("release_date") or d.get("first_air_date") or "")[:4]
                if t_name:
                    resolved.append({
                        "title": t_name,
                        "year": int(yr) if yr.isdigit() else None,
                        "media_type": m_type.lower(),
                        "why": (d.get("overview") or "")[:160]
                    })
        if len(resolved) >= 5:
            return resolved

    # 2. Extract direct IMDb IDs (tt1234567) and resolve via TMDB /find/{imdb_id}
    for imdb_id in re.findall(r"imdb\.com/title/(tt\d{6,10})", raw_html, flags=re.I):
        if imdb_id in seen:
            continue
        seen.add(imdb_id)
        find_res = tmdb(f"/find/{imdb_id}", external_source="imdb_id")
        for m in (find_res.get("movie_results") or []):
            if is_safe_non_porn(m) and m.get("title"):
                yr = (m.get("release_date") or "")[:4]
                resolved.append({
                    "title": m["title"],
                    "year": int(yr) if yr.isdigit() else None,
                    "media_type": "movie",
                    "why": (m.get("overview") or "")[:160]
                })
        for tv in (find_res.get("tv_results") or []):
            if is_safe_non_porn(tv) and tv.get("name"):
                yr = (tv.get("first_air_date") or "")[:4]
                resolved.append({
                    "title": tv["name"],
                    "year": int(yr) if yr.isdigit() else None,
                    "media_type": "tv",
                    "why": (tv.get("overview") or "")[:160]
                })
        if len(resolved) >= 5:
            break

    return resolved


def live_web_plot_search(message):
    """
    Universal Plot-to-Title Web Resolver:
    1) Searches IMDb/TMDB/MDL via DuckDuckGo & Yahoo
    2) Resolves exact IMDb `tt...` and TMDB `/movie|tv/...` IDs via TMDB API first
    3) Sanitizes any heading titles so URLs can NEVER leak into guesses!
    """
    clean = re.sub(
        r"^(what|which)\s+(do\s+you\s+call\s+the\s+|is\s+the\s+)?(movie|film|series|show|drama|bl|boys\s+love\s+series|k-drama|anime)\s+(is\s+)?(about|where|that)\s+",
        "",
        message.strip(),
        flags=re.I
    ).strip()

    is_tv_hint = bool(re.search(r"\b(series|show|drama|bl|boys love|k-drama|kdrama|episodes|season)\b", message, re.I))
    queries_to_try = [
        f'{clean} imdb OR themoviedb OR mydramalist',
        f'"{clean}" movie OR series'
    ]

    guesses = []
    seen_titles = set()
    raw_web_snippets = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    for q_str in queries_to_try:
        if len(guesses) >= 5:
            break

        # 1. Try DuckDuckGo HTML
        try:
            resp = requests.post(
                "https://html.duckduckgo.com/html/",
                data={"q": q_str},
                headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
                timeout=5
            )
            if resp.status_code == 200:
                # First extract exact IMDb / TMDB IDs from the HTML!
                for r_item in resolve_imdb_or_tmdb_ids_from_html(resp.text):
                    if r_item["title"].lower() not in seen_titles:
                        seen_titles.add(r_item["title"].lower())
                        guesses.append(r_item)
                        raw_web_snippets.append(f"{r_item['title']} ({r_item.get('year')}): {r_item.get('why')}")

                r_titles = re.findall(r'<a[^>]*class="result__a"[^>]*>(.*?)</a>', resp.text, flags=re.I | re.S)
                r_snips = re.findall(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', resp.text, flags=re.I | re.S)
                for idx, rt in enumerate(r_titles[:8]):
                    snip = html.unescape(re.sub(r"<[^>]+>", "", r_snips[idx])).strip() if idx < len(r_snips) else ""
                    t_clean, yr, m_type = clean_extracted_web_title(rt)
                    if not t_clean:
                        continue
                    if snip:
                        raw_web_snippets.append(f"{t_clean}: {snip}")
                    if t_clean.lower() not in seen_titles:
                        seen_titles.add(t_clean.lower())
                        guesses.append({
                            "title": t_clean,
                            "year": yr,
                            "media_type": m_type or ("tv" if is_tv_hint else None),
                            "why": snip[:165] if snip else f"Matched to your plot description."
                        })
        except Exception:
            pass

        # 2. Try Yahoo Web Search (with strict span/URL stripping + IMDb/TMDB ID extraction)
        if len(guesses) < 3:
            try:
                y_url = f"https://search.yahoo.com/search?p={urllib.parse.quote(q_str)}"
                y_resp = requests.get(y_url, headers=headers, timeout=5)
                if y_resp.status_code == 200:
                    unquoted_html = urllib.parse.unquote(y_resp.text)
                    for r_item in resolve_imdb_or_tmdb_ids_from_html(unquoted_html):
                        if r_item["title"].lower() not in seen_titles:
                            seen_titles.add(r_item["title"].lower())
                            guesses.append(r_item)
                            raw_web_snippets.append(f"{r_item['title']} ({r_item.get('year')}): {r_item.get('why')}")

                    y_titles = re.findall(r'<h3[^>]*class="[^"]*title[^"]*"[^>]*>.*?<a[^>]*>(.*?)</a>', y_resp.text, flags=re.I | re.S)
                    for rt in y_titles[:8]:
                        t_clean, yr, m_type = clean_extracted_web_title(rt)
                        if not t_clean:
                            continue
                        if t_clean.lower() not in seen_titles:
                            seen_titles.add(t_clean.lower())
                            guesses.append({
                                "title": t_clean,
                                "year": yr,
                                "media_type": m_type or ("tv" if is_tv_hint else None),
                                "why": f"Matched to your plot description."
                            })
            except Exception:
                pass

    return guesses, raw_web_snippets


def smart_local_nlp_parse(message, history, username="Guest", fav_genres=None):
    lower = message.lower()
    genres = []
    origin_country = None
    language = None
    guesses = []
    mood_keywords = []
    similar_to = []
    intent = "recommend"
    direct_reply = None

    country_map = {
        "korean": ("KR", "ko", "South Korean"), "korea": ("KR", "ko", "South Korean"),
        "k-drama": ("KR", "ko", "South Korean"), "kdrama": ("KR", "ko", "South Korean"),
        "japanese": ("JP", "ja", "Japanese"), "japan": ("JP", "ja", "Japanese"), "anime": ("JP", "ja", "Japanese"),
        "filipino": ("PH", "tl", "Filipino"), "pinoy": ("PH", "tl", "Filipino"),
        "philippine": ("PH", "tl", "Philippine"), "philippines": ("PH", "tl", "Philippine"),
        "tagalog": ("PH", "tl", "Filipino"),
        "thai": ("TH", "th", "Thai"), "thailand": ("TH", "th", "Thai"),
        "indian": ("IN", "hi", "Indian"), "india": ("IN", "hi", "Indian"), "bollywood": ("IN", "hi", "Indian"),
        "french": ("FR", "fr", "French"), "france": ("FR", "fr", "French"),
        "spanish": ("ES", "es", "Spanish"), "spain": ("ES", "es", "Spanish"),
        "british": ("GB", "en", "British"), "uk": ("GB", "en", "British"),
    }
    country_label = ""
    for kw, (cc, lang, label) in country_map.items():
        if re.search(rf"\b{re.escape(kw)}\b", lower):
            origin_country = cc
            language = lang
            country_label = label
            break

    if any(w in lower for w in ["romcom", "rom-com", "romantic comedy"]):
        genres.extend(["romance", "comedy"])
    if any(w in lower for w in ["romance", "romantic", "love", "sweet", "heartbreaking", "boys love", "bl", "hate each other"]):
        if "romance" not in genres: genres.append("romance")
    if any(w in lower for w in ["music", "musical", "song", "singing", "band", "concert"]):
        if "music" not in genres: genres.append("music")
    if any(w in lower for w in ["funny", "comedy", "hilarious", "laugh"]):
        if "comedy" not in genres: genres.append("comedy")
    if any(w in lower for w in ["sad", "cry", "tearjerker", "emotional", "family", "legacies", "legacy"]):
        if "drama" not in genres: genres.append("drama")
    if any(w in lower for w in ["sci-fi", "scifi", "science fiction", "space", "future", "alien", "time travel"]):
        if "sci-fi" not in genres: genres.append("sci-fi")
    if any(w in lower for w in ["mind-bending", "twist", "psychological", "suspense", "dark", "thriller", "stuck", "trapped", "survival"]):
        if "thriller" not in genres: genres.append("thriller")
    if any(w in lower for w in ["scary", "horror", "ghost", "creepy", "haunted"]):
        if "horror" not in genres: genres.append("horror")
    if any(w in lower for w in ["action", "explosive", "fight", "blockbuster", "boxing"]):
        if "action" not in genres: genres.append("action")

    for g_name in GENRES.keys():
        if re.search(rf"\b{re.escape(g_name)}\b", lower) and g_name not in genres:
            genres.append(g_name)

    looks_like_plot_or_question = (
        len(lower.split()) >= 5
        or "?" in lower
        or any(p in lower for p in [
            "why", "how", "what", "which", "movie where", "movie about", "film about",
            "series about", "show about", "looking for", "forgot the name",
            "what's that", "whats that", "stuck", "trapped", "infiltrate",
            "relives", "twins", "nose", "raised to hate"
        ])
    )

    if origin_country and not genres and not looks_like_plot_or_question:
        if fav_genres:
            genres = [g.lower() for g in fav_genres if g.lower() in GENRES][:3]
        if not genres:
            genres = COUNTRY_DEFAULT_GENRES.get(origin_country, ["drama", "romance"])

    desc_parts = [p for p in [country_label, "/".join(genres[:3]).title()] if p]
    desc = " ".join(desc_parts) if desc_parts else f"'{message}'"
    direct_reply = f"Here are the top {desc} matches tailored to your request, {username}!"

    return {
        "intent": "plot_search" if looks_like_plot_or_question else intent,
        "plot_guesses": guesses,
        "genres": genres,
        "origin_country": origin_country,
        "language": language,
        "mood_keywords": mood_keywords,
        "similar_to": similar_to,
        "direct_reply": direct_reply
    }


def extract_intent(message, history, username="Guest", fav_genres=None, selected_country=None):
    local_parsed = smart_local_nlp_parse(message, history, username, fav_genres)
    is_plot_query = local_parsed.get("intent") == "plot_search"

    web_guesses, web_snippets = ([], [])
    if is_plot_query:
        web_guesses, web_snippets = live_web_plot_search(message)

    ctx_lines = [f"{'User' if h.get('role') == 'user' else 'Nova'}: {h.get('content')}" for h in (history or [])[-10:] if isinstance(h, dict) and h.get("content")]
    ctx = "\n".join(ctx_lines) if ctx_lines else "No prior messages."
    web_hint_str = "\n".join(web_snippets[:6]) if web_snippets else "None"

    user_prompt = (
        f"User: {username}\n"
        f"Favorite Genres: {', '.join(fav_genres or [])}\n"
        f"Live Web Search Evidence for this query:\n{web_hint_str}\n\n"
        f"Conversation History:\n{ctx}\n\n"
        f"User's Latest Request: {message}"
    )

    llm_parsed = llm_json(PARSE_PROMPT, user_prompt, temperature=0.15)

    if llm_parsed and isinstance(llm_parsed, dict):
        for k in ("origin_country", "language", "genres"):
            if not llm_parsed.get(k) and local_parsed.get(k):
                llm_parsed[k] = local_parsed[k]
        llm_guesses = [
            g for g in (llm_parsed.get("plot_guesses") or [])
            if isinstance(g, dict) and is_valid_clean_title(g.get("title", ""))
        ]
        combined_guesses = list(llm_guesses)
        seen_t = {g["title"].lower() for g in combined_guesses}
        for wg in web_guesses:
            if is_valid_clean_title(wg.get("title", "")) and wg["title"].lower() not in seen_t:
                combined_guesses.append(wg)
                seen_t.add(wg["title"].lower())
        llm_parsed["plot_guesses"] = combined_guesses
        return llm_parsed

    if web_guesses:
        local_parsed["intent"] = "plot_search"
        local_parsed["plot_guesses"] = web_guesses
        # Note: We let chat() generate the final reply from the #1 verified TMDB hit so it never names an unverified web string!
        local_parsed["direct_reply"] = ""

    return local_parsed


def search_tmdb_title(title, year=None, media_hint=None, user_query=""):
    """
    Searches TMDB across BOTH movies AND TV series (/search/multi, /search/tv, /search/movie)
    and scores results by title accuracy + overview word overlap with the user's plot query.
    """
    if not is_valid_clean_title(title):
        return None
    title_clean = title.strip()
    query_words = {
        w for w in re.findall(r"[a-z]{4,}", user_query.lower())
        if w not in {"what", "movie", "series", "about", "where", "that", "with", "from", "their", "they", "have", "this", "call", "film"}
    }

    candidates = []
    for item in tmdb("/search/multi", query=title_clean).get("results", []):
        if item.get("media_type") in ("movie", "tv") and is_safe_non_porn(item) and item.get("poster_path"):
            candidates.append(item)

    if not candidates:
        for ep, m_type in (("/search/tv", "tv"), ("/search/movie", "movie")):
            for item in tmdb(ep, query=title_clean).get("results", []):
                if is_safe_non_porn(item) and item.get("poster_path"):
                    item["media_type"] = m_type
                    candidates.append(item)

    if not candidates:
        return None

    def score_hit(h):
        sc = 0.0
        h_title = (h.get("title") or h.get("name") or "").lower().strip()
        if h_title == title_clean.lower():
            sc += 55.0
        elif title_clean.lower() in h_title or h_title in title_clean.lower():
            sc += 25.0
        if year:
            h_yr = (h.get("release_date") or h.get("first_air_date") or "")[:4]
            if h_yr == str(year):
                sc += 30.0
        if media_hint and h.get("media_type") == media_hint:
            sc += 12.0
        if query_words:
            ov_lower = (h.get("overview") or "").lower()
            overlap = sum(1 for w in query_words if w in ov_lower)
            sc += overlap * 15.0
        sc += min((h.get("popularity") or 0) / 50.0, 5.0)
        return sc

    candidates.sort(key=score_hit, reverse=True)
    return candidates[0]


def keyword_ids(words):
    ids = []
    for w in (words or [])[:4]:
        r = tmdb("/search/keyword", query=w).get("results", [])
        if r:
            ids.append(str(r[0]["id"]))
    return ids


def plot_search(p, raw_message=""):
    results, seen = [], set()
    for idx, g in enumerate((p.get("plot_guesses") or [])[:8]):
        title = g.get("title") if isinstance(g, dict) else str(g)
        year = g.get("year") if isinstance(g, dict) else None
        m_hint = g.get("media_type") if isinstance(g, dict) else p.get("media_preference")
        why = g.get("why") if isinstance(g, dict) else None
        if not is_valid_clean_title(title):
            continue

        chosen = search_tmdb_title(title, year=year, media_hint=m_hint, user_query=raw_message)
        if chosen:
            u_key = f"{chosen.get('media_type', 'movie')}_{chosen['id']}"
            if u_key not in seen:
                seen.add(u_key)
                chosen["_bonus"] = 60.0 - (idx * 5.0)
                chosen["_is_guess"] = True
                if why:
                    chosen["_guess_why"] = html.unescape(str(why))
                results.append(chosen)

    if len(results) < 6:
        kws = keyword_ids(p.get("mood_keywords", []))
        if kws:
            extra = tmdb("/discover/movie", with_keywords="|".join(kws), sort_by="popularity.desc", **{"vote_count.gte": 25}).get("results", [])
            for m in extra:
                u_key = f"movie_{m.get('id')}"
                if is_safe_non_porn(m) and m.get("poster_path") and u_key not in seen:
                    seen.add(u_key)
                    m["media_type"] = "movie"
                    m["_bonus"] = 10.0
                    results.append(m)

    if results and len(results) < 8:
        top_hit = results[0]
        top_type = top_hit.get("media_type", "movie")
        top_title = top_hit.get("title") or top_hit.get("name")
        for m in tmdb(f"/{top_type}/{top_hit['id']}/recommendations").get("results", []):
            u_key = f"{top_type}_{m.get('id')}"
            if is_safe_non_porn(m) and m.get("poster_path") and u_key not in seen:
                seen.add(u_key)
                m["media_type"] = top_type
                m["_bonus"] = 8.0
                m["_guess_why"] = f"Recommended because it shares key themes with {top_title}."
                results.append(m)

    return results


def find_movies(intent, raw_message=""):
    if intent.get("intent") == "plot_search":
        found = plot_search(intent, raw_message=raw_message)
        if found:
            return found

    cands = {}
    target_lang = intent.get("language")
    target_country = (intent.get("origin_country") or "").upper() or None

    def add(movies, bonus=0, why_note=None, enforce_country=False, default_media="movie"):
        for m in movies:
            if not is_safe_non_porn(m):
                continue
            if not m.get("id") or not m.get("poster_path"):
                continue
            if enforce_country and target_lang and m.get("original_language") != target_lang:
                continue
            if target_country and not m.get("origin_country"):
                m["origin_country"] = [target_country]
            m.setdefault("media_type", default_media)
            u_key = f"{m['media_type']}_{m['id']}"
            if u_key not in cands:
                m["_bonus"] = bonus
                if why_note:
                    m["_guess_why"] = html.unescape(str(why_note))
                cands[u_key] = m
            else:
                cands[u_key]["_bonus"] = max(cands[u_key].get("_bonus", 0), bonus)

    for idx, g in enumerate((intent.get("plot_guesses") or [])[:8]):
        title = g.get("title") if isinstance(g, dict) else str(g)
        year = g.get("year") if isinstance(g, dict) else None
        m_hint = g.get("media_type") if isinstance(g, dict) else None
        why = g.get("why") if isinstance(g, dict) else None
        hit = search_tmdb_title(title, year=year, media_hint=m_hint, user_query=raw_message)
        if hit:
            add([hit], bonus=40.0 - (idx * 3.0), why_note=why, default_media=hit.get("media_type", "movie"))

    for t in (intent.get("similar_to") or [])[:2]:
        hit = search_tmdb_title(t, user_query=raw_message)
        if hit:
            m_type = hit.get("media_type", "movie")
            add(tmdb(f"/{m_type}/{hit['id']}/recommendations").get("results", []), bonus=15.0, why_note=f"Recommended based on '{t}'.", default_media=m_type)

    gids = [str(GENRES[g.lower()]) for g in (intent.get("genres") or []) if g.lower() in GENRES]
    xids = [str(GENRES[g.lower()]) for g in intent.get("exclude_genres") or [] if g.lower() in GENRES]

    min_votes = 15 if (target_country or target_lang) else 80
    p = {"include_adult": "false", "vote_count.gte": min_votes, "language": "en-US", "sort_by": "popularity.desc"}
    if gids: p["with_genres"] = "|".join(gids[:3]) if target_country else ",".join(gids[:2])
    if xids: p["without_genres"] = ",".join(xids)
    if target_lang: p["with_original_language"] = target_lang
    if target_country: p["with_origin_country"] = target_country

    for page in (1, 2):
        add(tmdb("/discover/movie", page=page, **p).get("results", []), bonus=10.0, enforce_country=True, default_media="movie")

    if len(cands) < 8 and len(gids) > 1:
        p["with_genres"] = "|".join(gids)
        for page in (1, 2):
            add(tmdb("/discover/movie", page=page, **p).get("results", []), bonus=5.0, enforce_country=True, default_media="movie")

    return list(cands.values())


def get_seen_ids(username):
    if not username or username == "Guest":
        return set()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    ids = set()
    for q in ("SELECT movie_id FROM watchlist WHERE username=?", "SELECT movie_id FROM favorites WHERE username=?"):
        c.execute(q, (username.lower(),))
        ids.update(r[0] for r in c.fetchall())
    conn.close()
    return ids


def norm(t):
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def rank(cands, intent, seen_ids):
    is_plot = intent.get("intent") == "plot_search"
    blocked = {norm(t) for t in (intent.get("exclude_titles") or [])}
    if not is_plot:
        blocked |= {norm(t) for t in (intent.get("similar_to") or [])}
    out = []
    seen_unique = set()
    for m in cands:
        if not is_safe_non_porn(m):
            continue
        u_key = f"{m.get('media_type', 'movie')}_{m['id']}"
        if u_key in seen_unique:
            continue
        seen_unique.add(u_key)
        if not is_plot and not m.get("_is_guess"):
            if m["id"] in seen_ids or norm(m.get("title") or m.get("name")) in blocked:
                continue
        pop = min((m.get("popularity") or 0) / 100, 1.0)
        m["_score"] = (m.get("vote_average") or 0) * 0.7 + pop * 1.5 + m.get("_bonus", 0)
        out.append(m)
    out.sort(key=lambda x: x["_score"], reverse=True)
    top = out[:12]
    if top:
        for idx, m in enumerate(top):
            if m.get("_bonus", 0) >= 50: m["_match"] = 99
            elif m.get("_bonus", 0) >= 30: m["_match"] = max(94, 98 - idx)
            else:
                best = top[0]["_score"] or 1
                m["_match"] = max(82, min(97, int(82 + 15 * (m["_score"] / best))))
    return top


def explain(message, username, movies, intent):
    listing = [{"id": m["id"], "title": m.get("title") or m.get("name"), "year": (m.get("release_date") or m.get("first_air_date") or "")[:4],
                "overview": (m.get("overview") or "")[:200]} for m in movies[:8]]
    system = (
        f"You are Nova, a warm, witty AI cinema & series companion talking to {username}. "
        'Return ONLY JSON: {"reply": "2 engaging sentences directly answering the user and naming the #1 match", '
        '"reasons": {"<id>": "1 specific sentence explaining why this title fits their request"}}. '
        "Only mention titles from the provided list."
    )
    return llm_json(system, f"User Request: {message}\nVerified Titles: {json.dumps(listing)}", temperature=0.2) or {}


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    profile = data.get("profile") or {}
    username = profile.get("name", "Guest")
    fav_genres = profile.get("favorite_genres") or []
    selected_country = (profile.get("origin_country") or "").strip().upper()
    history = data.get("history") or []
    region = (data.get("region") or "").upper() or None

    if not message:
        return jsonify({"reply": f"Hey {username}! Tell me any movie or series plot, question, or mood you're craving.", "movies": []})

    intent = extract_intent(message, history, username, fav_genres, selected_country)
    intent_type = intent.get("intent", "recommend")

    if intent_type in ("chitchat", "question") and not intent.get("plot_guesses") and not intent.get("genres"):
        reply = html.unescape(intent.get("direct_reply") or f"I'm Nova, your AI cinema & series companion, {username}! Describe any movie or series plot and I'll find it.")
        return jsonify({"reply": reply, "movies": [], "intent": intent_type, "success": True})

    if intent_type == "recommend" and not intent.get("genres") and not intent.get("plot_guesses"):
        if fav_genres:
            intent["genres"] = [g.lower() for g in fav_genres[:3]]
        elif intent.get("origin_country"):
            intent["genres"] = COUNTRY_DEFAULT_GENRES.get(intent["origin_country"], ["drama", "romance"])

    if not intent.get("origin_country") and selected_country and intent_type != "plot_search":
        intent["origin_country"] = selected_country

    cands = find_movies(intent, raw_message=message)
    if not cands:
        search_res = tmdb("/search/multi", query=message).get("results", [])
        cands = [m for m in search_res if is_safe_non_porn(m) and m.get("poster_path") and m.get("media_type") in ("movie", "tv")]

    top = rank(cands, intent, get_seen_ids(username))
    if not top and cands:
        top = cands[:12]

    if not top:
        return jsonify({
            "reply": html.unescape(intent.get("direct_reply") or f"I couldn't find an exact match for '{message}', {username}. Try describing another detail or scene!"),
            "movies": [], "intent": intent_type, "success": True
        })

    direct_reply = html.unescape(intent.get("direct_reply") or "")
    reasons = {}
    if not direct_reply or direct_reply.startswith("Here are the top"):
        ex = explain(message, username, top, intent)
        reasons = ex.get("reasons", {}) if isinstance(ex.get("reasons"), dict) else {}
        if ex.get("reply"):
            direct_reply = html.unescape(ex.get("reply"))

    # Always guarantee the reply names the #1 VERIFIED TMDB movie/series (never an unverified web string!)
    if not direct_reply or direct_reply.startswith("Here are the top") or "http" in direct_reply or ".com" in direct_reply:
        top_name = top[0].get("title") or top[0].get("name")
        top_yr = (top[0].get("release_date") or top[0].get("first_air_date") or "")[:4]
        yr_str = f" ({top_yr})" if top_yr else ""
        top_ov = (top[0].get("overview") or "")[:200]
        direct_reply = f"You're looking for '{top_name}'{yr_str}! {top_ov}"

    movies = [{
        "id": m["id"],
        "title": m.get("title") or m.get("name"),
        "media_type": m.get("media_type", "movie"),
        "poster": f"https://image.tmdb.org/t/p/w500{m['poster_path']}",
        "vote_average": m.get("vote_average", 0.0),
        "vote_count": m.get("vote_count", 0),
        "release_date": m.get("release_date") or m.get("first_air_date") or "",
        "overview": m.get("overview", ""),
        "genre_ids": m.get("genre_ids", []),
        "origin_country": m.get("origin_country") or ([intent["origin_country"]] if intent.get("origin_country") else []),
        "original_language": m.get("original_language", ""),
        "r18": is_genuine_r18(m),
        "match": m.get("_match", 96),
        "platforms": [region or "Global"],
        "rationale": html.unescape(reasons.get(str(m["id"])) or m.get("_guess_why") or (m.get("overview") or "")[:140] or f"Matched to your '{message}' query."),
    } for m in top]

    return jsonify({"reply": direct_reply, "movies": movies, "intent": intent_type, "success": True})


@app.route("/trends", methods=["GET"])
def trends():
    return jsonify({
        "ai_forecast": "Super-Nova Multi-LLM + IMDb/TMDB ID Plot-Search Pipeline Online.",
        "trending_genres": ["Multi-LLM Plot & Series Recognition", "IMDb/TMDB Direct ID Plot Resolver", "OMDb Metadata Enrichment"]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
