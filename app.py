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

# Environment variables with fallback keys
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
    return jsonify({"status": "CineMind Super-Nova Engine Live", "version": "12.0"})


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


# ------------------------- OMDb (modal & enrichment) -------------------------
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


# ------------------------- SUPER-NOVA AI PIPELINE -------------------------
PARSE_PROMPT = f"""You are Nova, a super-intelligent, warm, and encyclopedic AI cinema expert.
Analyze the user's latest message along with the conversation history and user profile.
Return ONLY a valid JSON object with these exact keys:
{{
  "intent": "recommend" | "similar_to" | "plot_search" | "chitchat" | "question",
  "plot_guesses": [{{"title": "Exact Movie Title", "year": 2019, "why": "1-sentence explanation of how this matches the plot/vibe"}}],
  "genres": [list of matching genres from: {GENRE_LIST}],
  "exclude_genres": [genres the user explicitly does NOT want],
  "year_from": integer or null,
  "year_to": integer or null,
  "min_rating": number 0-10 or null,
  "language": ISO 639-1 code like "ko", "ja", "tl", "es", "fr", "hi" or null,
  "origin_country": ISO 3166-1 code like "KR", "PH", "JP", "US", "GB", "IN", "FR", "ES", "TH" or null,
  "sort": "popularity" | "rating" | "newest",
  "mood_keywords": [2-4 specific plot/theme keywords, e.g. "time loop", "class divide", "amnesia", "heist"],
  "similar_to": [movie titles the user says they liked or wants similar to],
  "exclude_titles": [movie titles the user has already seen, rejected, or wants to avoid],
  "direct_reply": "Your natural, witty, intelligent conversational response. If intent is chitchat or question, answer fully here. If intent is plot_search, name your top guess enthusiastically and explain why!"
}}

CRITICAL RULES:
1. If the user describes a plot, scene, twist, character, or says things like 'what's that movie where...', 'I forgot the name', 'movie about a guy who...', or gives a specific premise like 'a poor family who infiltrates a rich household', MUST use intent "plot_search". Put your best 4-6 guesses of the actual movie in "plot_guesses" (most likely first, e.g. Parasite (2019), with exact release year), and fill "mood_keywords" with 2-4 plot keywords (e.g. 'time loop', 'amnesia', 'heist').
2. Even for "recommend" or "similar_to" intents (e.g. 'Korean romcom', 'sad movies that will make me cry', 'movies like Interstellar'), ALWAYS populate "plot_guesses" with 4-6 of the absolute best real-world movies that fit the exact request so our engine can verify them on TMDB alongside discovery filters!
3. Use the conversation history to resolve follow-ups! If the user says 'something darker', 'more like the first one', 'only from the 90s', or 'no horror', update the filters and guesses based on earlier messages.
"""


def tmdb(path, **params):
    params["api_key"] = TMDB_API_KEY
    try:
        r = requests.get(f"{TMDB}{path}", params=params, timeout=6)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def groq_json(system, user, temperature=0.25, timeout=12):
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
                "temperature": temperature,
            },
            timeout=timeout,
        )
        if res.status_code == 200:
            return json.loads(res.json()["choices"][0]["message"]["content"])
    except Exception:
        pass
    return None


def get_user_library_titles(username):
    if not username or username == "Guest":
        return [], []
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT title FROM favorites WHERE username=? LIMIT 10", (username.lower(),))
    favs = [r[0] for r in c.fetchall()]
    c.execute("SELECT title FROM watchlist WHERE username=? LIMIT 10", (username.lower(),))
    watch = [r[0] for r in c.fetchall()]
    conn.close()
    return favs, watch


def extract_intent(message, history, username="Guest", fav_genres=None, selected_country=None):
    favs, watch = get_user_library_titles(username)
    ctx_lines = []
    for h in (history or [])[-10:]:
        if isinstance(h, dict) and h.get("content"):
            role = "User" if h.get("role") == "user" else "Nova"
            ctx_lines.append(f"{role}: {h.get('content')}")
    ctx = "\n".join(ctx_lines) if ctx_lines else "No prior messages in this session."

    profile_note = (
        f"User Name: {username}\n"
        f"User's Calibrated Favorite Genres: {', '.join(fav_genres or []) or 'None specified'}\n"
        f"User's Favorited Movies: {', '.join(favs) or 'None yet'}\n"
        f"User's Watchlist: {', '.join(watch) or 'None yet'}\n"
        f"Active Country Filter: {selected_country or 'All Countries'}"
    )

    user_prompt = f"{profile_note}\n\nConversation Memory:\n{ctx}\n\nUser's Latest Message: {message}"
    parsed = groq_json(PARSE_PROMPT, user_prompt, temperature=0.2) or {}

    # Fallback heuristic if Groq key is rate-limited or unreachable
    if not parsed:
        lower_msg = message.lower()
        looks_plot = len(message.split()) >= 5 or any(w in lower_msg for w in ["where", "about a", "forgot", "relives", "infiltrates", "family", "guy who", "girl who"])
        parsed = {
            "intent": "plot_search" if looks_plot else "recommend",
            "plot_guesses": [],
            "genres": [g for g in GENRES.keys() if g in lower_msg],
            "mood_keywords": [message],
            "direct_reply": f"Here are the top matches I found for '{message}', {username}!"
        }
    return parsed


def find_movie_id(title):
    res = tmdb("/search/movie", query=title).get("results", [])
    return res[0]["id"] if res else None


def keyword_ids(words):
    ids = []
    for w in (words or [])[:4]:
        r = tmdb("/search/keyword", query=w).get("results", [])
        if r:
            ids.append(str(r[0]["id"]))
    return ids


def plot_search(p):
    results, seen = [], set()

    # 1) Verify the LLM's exact guesses on TMDB (preserve order with decaying priority bonus)
    guesses = p.get("plot_guesses") or []
    for idx, g in enumerate(guesses[:6]):
        title = g.get("title") if isinstance(g, dict) else str(g)
        year = g.get("year") if isinstance(g, dict) else None
        why = g.get("why") if isinstance(g, dict) else None
        if not title:
            continue
        params = {"query": title}
        if year:
            params["year"] = year
        hits = tmdb("/search/movie", **params).get("results", [])
        if not hits and year:
            hits = tmdb("/search/movie", query=title).get("results", [])
        if hits:
            best_hit = hits[0]
            if best_hit.get("id") and best_hit.get("poster_path") and best_hit["id"] not in seen:
                seen.add(best_hit["id"])
                # Massive bonus so #1 LLM guess stays #1!
                best_hit["_bonus"] = 50.0 - (idx * 5.0)
                best_hit["_is_guess"] = True
                if why:
                    best_hit["_guess_why"] = why
                results.append(best_hit)

    # 2) Backup: match on mood_keywords / keywords
    kws = keyword_ids(p.get("mood_keywords") or p.get("keywords") or [])
    if len(results) < 8 and kws:
        extra = tmdb("/discover/movie", with_keywords="|".join(kws),
                     sort_by="popularity.desc", **{"vote_count.gte": 50}).get("results", [])
        for m in extra:
            if m.get("id") and m.get("poster_path") and m["id"] not in seen:
                seen.add(m["id"])
                m["_bonus"] = 5.0
                results.append(m)

    # 3) If still few results, pull TMDB recommendations from the #1 verified movie (e.g., movies similar to Parasite)
    if results and len(results) < 8:
        top_id = results[0]["id"]
        sim = tmdb(f"/movie/{top_id}/recommendations").get("results", [])
        for m in sim:
            if m.get("id") and m.get("poster_path") and m["id"] not in seen:
                seen.add(m["id"])
                m["_bonus"] = 8.0
                m["_guess_why"] = f"Thematically similar to {results[0].get('title')}."
                results.append(m)

    return results


def gather_candidates(intent, region=None):
    # If it's a plot search, prioritize plot_search() directly
    if intent.get("intent") == "plot_search":
        found = plot_search(intent)
        if found:
            return found

    cands = {}

    def add(movies, bonus=0, why_note=None):
        for m in movies:
            if m.get("id") and m.get("poster_path"):
                if m["id"] not in cands:
                    m["_bonus"] = bonus
                    if why_note:
                        m["_guess_why"] = why_note
                    cands[m["id"]] = m
                else:
                    cands[m["id"]]["_bonus"] = max(cands[m["id"]].get("_bonus", 0), bonus)

    # Always verify Groq's specific title suggestions first so Nova's exact picks appear at the top!
    for idx, g in enumerate((intent.get("plot_guesses") or [])[:6]):
        title = g.get("title") if isinstance(g, dict) else str(g)
        year = g.get("year") if isinstance(g, dict) else None
        why = g.get("why") if isinstance(g, dict) else None
        if not title:
            continue
        params = {"query": title}
        if year:
            params["year"] = year
        hits = tmdb("/search/movie", **params).get("results", [])
        if not hits and year:
            hits = tmdb("/search/movie", query=title).get("results", [])
        if hits:
            add([hits[0]], bonus=25.0 - (idx * 2.0), why_note=why)

    for t in (intent.get("similar_to") or [])[:2]:
        mid = find_movie_id(t)
        if mid:
            add(tmdb(f"/movie/{mid}/recommendations").get("results", []), bonus=10.0,
                why_note=f"Recommended because you liked {t}.")

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

    kws = keyword_ids(intent.get("mood_keywords") or intent.get("keywords"))
    if kws: p["with_keywords"] = "|".join(kws)

    sort = {"rating": "vote_average.desc", "newest": "primary_release_date.desc"}.get(
        intent.get("sort"), "popularity.desc")
    p["sort_by"] = sort
    if sort == "vote_average.desc":
        p["vote_count.gte"] = 300
    if sort == "primary_release_date.desc":
        p["primary_release_date.lte"] = p.get("primary_release_date.lte", date.today().isoformat())

    if region and not intent.get("origin_country") and not intent.get("language"):
        rp = dict(p, watch_region=region, with_watch_monetization_types="flatrate")
        for page in (1, 2):
            add(tmdb("/discover/movie", page=page, **rp).get("results", []), bonus=1.5)

    for page in (1, 2):
        add(tmdb("/discover/movie", page=page, **p).get("results", []))

    if len(cands) < 8 and "with_keywords" in p:
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
    is_plot = intent.get("intent") == "plot_search"
    blocked = {norm(t) for t in (intent.get("exclude_titles") or [])}
    if not is_plot:
        blocked |= {norm(t) for t in (intent.get("similar_to") or [])}

    out = []
    for m in cands:
        # Never hide the movie the user is specifically trying to identify in plot_search!
        if not is_plot and not m.get("_is_guess"):
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
        for idx, m in enumerate(top):
            if m.get("_bonus", 0) >= 45:
                m["_match"] = 99
            elif m.get("_bonus", 0) >= 20:
                m["_match"] = max(92, 98 - idx)
            else:
                best = top[0]["_score"] or 1
                m["_match"] = max(78, min(97, int(78 + 19 * (m["_score"] / best))))
    return top


def explain(message, username, movies, intent):
    listing = [{"id": m["id"], "title": m["title"], "year": (m.get("release_date") or "")[:4],
                "overview": (m.get("overview") or "")[:220]} for m in movies[:8]]
    intent_type = intent.get("intent", "recommend")
    system = (
        f"You are Nova, a super-intelligent, warm, and witty AI cinema companion talking to {username}. "
        f"The user's intent was '{intent_type}'. "
        'Return ONLY JSON: {"reply": "2-3 engaging, specific sentences directly answering the user, naming the #1 movie match and explaining why it fits", '
        '"reasons": {"<id>": "1 specific sentence explaining why this movie matches their exact request"}}. '
        "Only mention movies from the provided list. Never invent titles."
    )
    return groq_json(system, f"User Request: {message}\nVerified Movies Found: {json.dumps(listing)}", temperature=0.35) or {}


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
        return jsonify({"reply": f"Hey {username}! Tell me a plot, mood, or vibe you're craving.", "movies": []})

    intent = extract_intent(message, history, username, fav_genres, selected_country)
    intent_type = intent.get("intent", "recommend")

    # Handle pure chitchat or general film questions gracefully
    if intent_type in ("chitchat", "question") and not intent.get("plot_guesses") and not intent.get("genres"):
        reply = intent.get("direct_reply") or f"I'm Nova, your neural cinema companion, {username}! Ask me to identify any movie from a vague plot or describe your mood for tailored recommendations."
        return jsonify({"reply": reply, "movies": [], "intent": intent_type, "success": True})

    # Blend user's calibrated genres only when they haven't specified a genre or plot search
    if intent_type == "recommend" and not intent.get("genres") and not intent.get("plot_guesses") and fav_genres:
        intent["genres"] = [g.lower() for g in fav_genres[:3]]
    if not intent.get("origin_country") and selected_country and intent_type != "plot_search":
        intent["origin_country"] = selected_country

    cands = gather_candidates(intent, region)

    if not cands:
        search_res = tmdb("/search/movie", query=message).get("results", [])
        trending_res = tmdb("/trending/movie/week").get("results", [])
        cands = [m for m in (search_res + trending_res) if m.get("poster_path")]

    top = rank(cands, intent, get_seen_ids(username))
    if not top and cands:
        top = cands[:12]

    if not top:
        return jsonify({
            "reply": intent.get("direct_reply") or "I couldn't find an exact match for that filter combination. Try describing the plot or loosening a filter!",
            "movies": [],
            "intent": intent_type,
            "success": True
        })

    ex = explain(message, username, top, intent)
    reasons = ex.get("reasons", {}) if isinstance(ex.get("reasons"), dict) else {}
    reply = ex.get("reply") or intent.get("direct_reply") or f"Here are my top neural matches for '{message}', {username}!"

    movies = [{
        "id": m["id"],
        "title": m["title"],
        "poster": f"https://image.tmdb.org/t/p/w500{m['poster_path']}",
        "vote_average": m.get("vote_average", 0.0),
        "vote_count": m.get("vote_count", 0),
        "release_date": m.get("release_date", ""),
        "overview": m.get("overview", ""),
        "match": m.get("_match", 96),
        "platforms": [region or "Global"],
        "rationale": reasons.get(str(m["id"])) or m.get("_guess_why") or f"Curated by Nova AI for '{message}'.",
    } for m in top]

    return jsonify({"reply": reply, "movies": movies, "intent": intent_type, "success": True})


@app.route("/trends", methods=["GET"])
def trends():
    return jsonify({
        "ai_forecast": "Super-Nova Multi-API Memory & Plot-Search Pipeline Online.",
        "trending_genres": ["Groq Plot & Intent Recognition", "TMDB Candidate Verification", "OMDb Metadata Enrichment"]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
