import os
import re
import json
import sqlite3
import hashlib
from datetime import date

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# Correct environment variable lookups (Name first, fallback key second)
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "7c7e21b0fe58e5868e262c9bd6b8e7e9").strip().strip('"').strip("'")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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").strip().strip('"').strip("'")
OMDB_API_KEY = os.environ.get("OMDB_API_KEY", "554ae239").strip().strip('"').strip("'")

DB_NAME = "cinemind.db"
TMDB = "https://api.themoviedb.org/3"

GENRES = {
    "action": 28, "adventure": 12, "animation": 16, "comedy": 35, "crime": 80,
    "documentary": 99, "drama": 18, "family": 10751, "fantasy": 14, "history": 36,
    "horror": 27, "music": 10402, "mystery": 9648, "romance": 10749,
    "sci-fi": 878, "science fiction": 878, "thriller": 53, "war": 10752, "western": 37,
}
GENRE_LIST = ", ".join(GENRES.keys())


# ------------------------- DATABASE -------------------------
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
    return jsonify({"status": "CineMind Production Engine Live", "version": "11.0"})


# ------------------------- AUTH -------------------------
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


# ------------------------- LIBRARY -------------------------
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


# ------------------------- OMDb (modal verification) -------------------------
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


# ------------------------- NOVA PIPELINE -------------------------
def tmdb(path, **params):
    params["api_key"] = TMDB_API_KEY
    try:
        r = requests.get(f"{TMDB}{path}", params=params, timeout=6)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def groq_json(system, user, timeout=10):
    if not GROQ_API_KEY:
        return None
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "response_format": {"type": "json_object"},
                "temperature": 0.3,
            },
            timeout=timeout,
        )
        if res.status_code == 200:
            return json.loads(res.json()["choices"][0]["message"]["content"])
    except Exception:
        pass
    return None


def extract_intent(message, history):
    system = (
        "You extract movie preferences. Return ONLY a JSON object with these keys:\n"
        '"intent": "recommend" | "similar_to" | "plot_search" | "chitchat" | "question",\n'
        '"plot_guesses": [{"title": "...", "year": 1993}],\n'
        f'"genres": list from [{GENRE_LIST}],\n'
        '"exclude_genres": list of genres the user does NOT want,\n'
        '"year_from": integer or null, "year_to": integer or null,\n'
        '"min_rating": number 0-10 or null,\n'
        '"language": ISO 639-1 code like "ko" or "ja" or "tl", or null,\n'
        '"origin_country": ISO 3166-1 code like "KR", "PH", "JP", "US", or null,\n'
        '"sort": "popularity" or "rating" or "newest",\n'
        '"keywords": list of themes/plots (e.g. "time travel"),\n'
        '"similar_to": list of movie titles the user says they like,\n'
        '"exclude_titles": list of movie titles the user has seen or dislikes.\n'
        "If the user describes a plot, scene, twist, character, or says things like 'what's that movie where...', "
        "use intent plot_search and put 3-6 guesses in plot_guesses."
    )
    ctx = "\n".join(f'{h.get("role")}: {h.get("content")}' for h in (history or [])[-6:] if isinstance(h, dict))
    return groq_json(system, f"Conversation so far:\n{ctx}\n\nLatest request: {message}") or {}


def find_movie_id(title):
    res = tmdb("/search/movie", query=title).get("results", [])
    return res[0]["id"] if res else None


def keyword_ids(words):
    ids = []
    for w in (words or [])[:3]:
        r = tmdb("/search/keyword", query=w).get("results", [])
        if r:
            ids.append(str(r[0]["id"]))
    return ids


def plot_search(p):
    results, seen = [], set()
    for g in p.get("plot_guesses", [])[:6]:
        title, year = g.get("title"), g.get("year")
        if not title:
            continue
        params = {"query": title}
        if year:
            params["year"] = year
        hits = tmdb("/search/movie", **params).get("results", [])
        if not hits and year:
            hits = tmdb("/search/movie", query=title).get("results", [])
        if hits and hits[0]["id"] not in seen:
            seen.add(hits[0]["id"])
            results.append(hits[0])

    if len(results) < 4:
        kws = keyword_ids(p.get("keywords", []))
        if kws:
            extra = tmdb("/discover/movie", with_keywords="|".join(kws),
                         sort_by="popularity.desc", **{"vote_count.gte": 50}).get("results", [])
            for m in extra:
                if m["id"] not in seen:
                    seen.add(m["id"])
                    results.append(m)
    return results


def gather_candidates(intent, region=None):
    if intent.get("intent") == "plot_search":
        found = plot_search(intent)
        if found:
            return found

    cands = {}

    def add(movies, bonus=0):
        for m in movies:
            if m.get("id") and m.get("poster_path"):
                m["_bonus"] = max(m.get("_bonus", 0), bonus)
                cands.setdefault(m["id"], m)

    for t in (intent.get("similar_to") or [])[:2]:
        mid = find_movie_id(t)
        if mid:
            add(tmdb(f"/movie/{mid}/recommendations").get("results", []), bonus=1.0)

    p = {"include_adult": "false", "vote_count.gte": 80, "language": "en-US"}
    gids = [str(GENRES[g.lower()]) for g in intent.get("genres") or [] if g.lower() in GENRES]
    xids = [str(GENRES[g.lower()]) for g in intent.get("exclude_genres") or [] if g.lower() in GENRES]
    if gids: p["with_genres"] = ",".join(gids)
    if xids: p["without_genres"] = ",".join(xids)
    if intent.get("language"): p["with_original_language"] = intent["language"]
    if intent.get("origin_country"): p["with_origin_country"] = intent["origin_country"].upper()
    try:
        if intent.get("year_from"): p["primary_release_date.gte"] = f'{int(intent["year_from"])}-01-01'
        if intent.get("year_to"): p["primary_release_date.lte"] = f'{int(intent["year_to"])}-12-31'
        if intent.get("min_rating"): p["vote_average.gte"] = float(intent["min_rating"])
    except (ValueError, TypeError):
        pass
    kws = keyword_ids(intent.get("keywords"))
    if kws: p["with_keywords"] = "|".join(kws)

    sort = {"rating": "vote_average.desc", "newest": "primary_release_date.desc"}.get(
        intent.get("sort"), "popularity.desc")
    p["sort_by"] = sort
    if sort == "vote_average.desc":
        p["vote_count.gte"] = 300
    if sort == "primary_release_date.desc":
        p["primary_release_date.lte"] = p.get("primary_release_date.lte", date.today().isoformat())

    if region and not intent.get("origin_country"):
        rp = dict(p, watch_region=region, with_watch_monetization_types="flatrate")
        for page in (1, 2):
            add(tmdb("/discover/movie", page=page, **rp).get("results", []), bonus=0.5)

    if len(cands) < 8:
        for page in (1, 2):
            add(tmdb("/discover/movie", page=page, **p).get("results", []))

    if len(cands) < 6 and "with_keywords" in p:
        p.pop("with_keywords")
        add(tmdb("/discover/movie", **p).get("results", []))
    return list(cands.values())


def get_seen_ids(username):
    if not username or username == "Guest":
        return set()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    ids = set()
    for q in ("SELECT movie_id FROM watchlist WHERE username=?",
              "SELECT movie_id FROM favorites WHERE username=?",
              "SELECT movie_id FROM interactions WHERE username=?"):
        c.execute(q, (username.lower(),))
        ids.update(r[0] for r in c.fetchall())
    conn.close()
    return ids


def norm(t):
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def rank(cands, intent, seen_ids):
    blocked = {norm(t) for t in (intent.get("exclude_titles") or [])}
    blocked |= {norm(t) for t in (intent.get("similar_to") or [])}
    out = []
    for m in cands:
        if m["id"] in seen_ids or norm(m.get("title")) in blocked:
            continue
        if (m.get("vote_count") or 0) < 20:
            continue
        pop = min((m.get("popularity") or 0) / 100, 1.0)
        m["_score"] = (m.get("vote_average") or 0) * 0.7 + pop * 1.5 + m.get("_bonus", 0)
        out.append(m)
    out.sort(key=lambda x: x["_score"], reverse=True)
    top = out[:12]
    if top:
        best = top[0]["_score"] or 1
        for m in top:
            m["_match"] = max(75, min(99, int(75 + 24 * (m["_score"] / best) ** 2)))
    return top


def explain(message, username, movies):
    listing = [{"id": m["id"], "title": m["title"], "year": (m.get("release_date") or "")[:4],
                "overview": (m.get("overview") or "")[:200]} for m in movies]
    system = (
        f"You are Nova, a friendly movie assistant talking to {username}. "
        'Return ONLY JSON: {"reply": "1-2 warm sentences", "reasons": {"<id>": "one sentence why it fits"}}. '
        "Only mention movies from the provided list. Never invent titles."
    )
    return groq_json(system, f"Request: {message}\nMovies: {json.dumps(listing)}") or {}


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
        return jsonify({"reply": f"Hey {username}! Tell me what kind of movie you're looking for.", "movies": []})

    intent = extract_intent(message, history)
    if not intent.get("genres") and fav_genres:
        intent["genres"] = [g.lower() for g in fav_genres[:3]]
    if not intent.get("origin_country") and selected_country:
        intent["origin_country"] = selected_country

    cands = gather_candidates(intent, region)

    if not cands or len(cands) < 4:
        search_res = tmdb("/search/movie", query=message).get("results", [])
        trending_res = tmdb("/trending/movie/week").get("results", [])
        cands = search_res + trending_res
        cands = [m for m in cands if m.get("poster_path")]

    top = rank(cands, intent, get_seen_ids(username))
    if not top and cands:
        top = cands[:12]

    if not top:
        return jsonify({"reply": "I couldn't find anything matching that. Try loosening your filters!",
                        "movies": [], "success": True})

    ex = explain(message, username, top)
    reasons = ex.get("reasons", {}) if isinstance(ex.get("reasons"), dict) else {}
    reply = ex.get("reply") or f"Here are some matches for '{message}', {username}!"

    movies = [{
        "id": m["id"],
        "title": m["title"],
        "poster": f"https://image.tmdb.org/t/p/w500{m['poster_path']}",
        "vote_average": m.get("vote_average", 0.0),
        "vote_count": m.get("vote_count", 0),
        "release_date": m.get("release_date", ""),
        "overview": m.get("overview", ""),
        "match": m.get("_match", 95),
        "platforms": [region or "Global"],
        "rationale": reasons.get(str(m["id"])) or f"Dynamic neural match for '{message}'.",
    } for m in top]

    return jsonify({"reply": reply, "movies": movies, "success": True})


@app.route("/trends", methods=["GET"])
def trends():
    return jsonify({
        "ai_forecast": "Groq + TMDB + OMDb pipeline online.",
        "trending_genres": ["Groq Intent Understanding", "TMDB Real-Movie Discovery", "CineHub Personal Ranking"]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
