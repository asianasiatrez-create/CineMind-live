import re

TMDB = "https://api.themoviedb.org/3"
GENRES = {
    "action": 28, "adventure": 12, "animation": 16, "comedy": 35, "crime": 80,
    "documentary": 99, "drama": 18, "family": 10751, "fantasy": 14, "history": 36,
    "horror": 27, "music": 10402, "mystery": 9648, "romance": 10749,
    "sci-fi": 878, "science fiction": 878, "thriller": 53, "war": 10752, "western": 37,
}

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

# ---------- Step 1: Groq understands the request ----------
def extract_intent(message, history):
    system = f"""You extract movie preferences. Return ONLY JSON:
{{
 "genres": [],            // from: {", ".join(GENRES.keys())}
 "exclude_genres": [],    // genres the user does NOT want
 "year_from": null, "year_to": null,   // integers
 "min_rating": null,      // 0-10
 "language": null,        // ISO 639-1 code, e.g. "ko", "ja", "fr"
 "sort": "popularity",    // "popularity" | "rating" | "newest"
 "keywords": [],          // themes/plots, e.g. "time travel", "heist"
 "similar_to": [],        // movie titles the user mentions liking
 "exclude_titles": []     // movie titles the user says they've seen or dislike
}}
Use earlier conversation to resolve follow-ups like "something newer" or "not that one"."""
    ctx = "\n".join(f'{h.get("role")}: {h.get("content")}' for h in (history or [])[-6:])
    return groq_json(system, f"Conversation so far:\n{ctx}\n\nLatest request: {message}") or {}

# ---------- Step 2: TMDB finds real candidates ----------
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

def gather_candidates(intent):
    cands = {}  # id -> movie dict (with "_src" bonus)

    def add(movies, bonus=0):
        for m in movies:
            if m.get("id") and m.get("poster_path"):
                m["_bonus"] = max(m.get("_bonus", 0), bonus)
                cands.setdefault(m["id"], m)

    # similar-to titles -> TMDB recommendations
    for t in (intent.get("similar_to") or [])[:2]:
        mid = find_movie_id(t)
        if mid:
            add(tmdb(f"/movie/{mid}/recommendations").get("results", []), bonus=1.0)

    # discover with structured filters
    p = {"include_adult": "false", "vote_count.gte": 150, "language": "en-US"}
    gids = [str(GENRES[g.lower()]) for g in intent.get("genres") or [] if g.lower() in GENRES]
    xids = [str(GENRES[g.lower()]) for g in intent.get("exclude_genres") or [] if g.lower() in GENRES]
    if gids: p["with_genres"] = ",".join(gids)          # AND
    if xids: p["without_genres"] = ",".join(xids)
    if intent.get("language"): p["with_original_language"] = intent["language"]
    if intent.get("year_from"): p["primary_release_date.gte"] = f'{int(intent["year_from"])}-01-01'
    if intent.get("year_to"): p["primary_release_date.lte"] = f'{int(intent["year_to"])}-12-31'
    if intent.get("min_rating"): p["vote_average.gte"] = float(intent["min_rating"])
    kws = keyword_ids(intent.get("keywords"))
    if kws: p["with_keywords"] = "|".join(kws)          # OR

    sort = {"rating": "vote_average.desc", "newest": "primary_release_date.desc"}.get(
        intent.get("sort"), "popularity.desc")
    p["sort_by"] = sort
    if sort == "vote_average.desc":
        p["vote_count.gte"] = 500
    if sort == "primary_release_date.desc":
        p["primary_release_date.lte"] = p.get("primary_release_date.lte", __import__("datetime").date.today().isoformat())

    for page in (1, 2):
        add(tmdb("/discover/movie", page=page, **p).get("results", []))

    # If filters were too strict, relax by dropping keywords
    if len(cands) < 6 and "with_keywords" in p:
        p.pop("with_keywords")
        add(tmdb("/discover/movie", **p).get("results", []))
    return list(cands.values())

# ---------- Step 3: CineHub logic filters + ranks ----------
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
    blocked |= {norm(t) for t in (intent.get("similar_to") or [])}  # don't recommend the seed itself
    out = []
    for m in cands:
        if m["id"] in seen_ids or norm(m.get("title")) in blocked:
            continue
        if (m.get("vote_count") or 0) < 50:
            continue
        pop = min((m.get("popularity") or 0) / 100, 1.0)
        score = (m.get("vote_average") or 0) * 0.7 + pop * 1.5 + m.get("_bonus", 0)
        m["_score"] = score
        out.append(m)
    out.sort(key=lambda x: x["_score"], reverse=True)
    top = out[:8]
    if top:
        best = top[0]["_score"] or 1
        for m in top:
            m["_match"] = max(70, min(99, int(70 + 29 * (m["_score"] / best) ** 2)))
    return top

# ---------- Step 4: Groq explains the REAL results ----------
def explain(message, username, movies):
    listing = [{"id": m["id"], "title": m["title"], "year": (m.get("release_date") or "")[:4],
                "overview": (m.get("overview") or "")[:200]} for m in movies]
    system = f"""You are Nova, a friendly movie assistant talking to {username}.
Return ONLY JSON: {{"reply": "1-2 warm sentences", "reasons": {{"<id>": "one sentence why it fits the request"}}}}
Only mention movies from the provided list. Never invent titles."""
    return groq_json(system, f"Request: {message}\nMovies: {json.dumps(listing)}") or {}

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    username = (data.get("profile") or {}).get("name", "Guest")
    history = data.get("history") or []

    if not message:
        return jsonify({"reply": f"Hey {username}! Tell me what kind of movie you're looking for.", "movies": []})

    intent = extract_intent(message, history)

    cands = gather_candidates(intent)
    if not cands:  # Groq down or filters too strict -> plain TMDB search, then trending
        cands = tmdb("/search/movie", query=message).get("results", []) \
                or tmdb("/trending/movie/week").get("results", [])
        cands = [m for m in cands if m.get("poster_path")]

    top = rank(cands, intent, get_seen_ids(username))
    if not top:
        return jsonify({"reply": "I couldn't find anything new matching that. Try loosening your filters!",
                        "movies": [], "success": True})

    ex = explain(message, username, top)
    reasons = ex.get("reasons", {})
    reply = ex.get("reply") or f"Here are some matches for '{message}', {username}!"

    movies = [{
        "id": m["id"],
        "title": m["title"],
        "poster": f"https://image.tmdb.org/t/p/w500{m['poster_path']}",
        "vote_average": m.get("vote_average", 0.0),
        "vote_count": m.get("vote_count", 0),
        "release_date": m.get("release_date", ""),
        "overview": m.get("overview", ""),
        "match": m["_match"],
        "platforms": ["TMDB"],
        "rationale": reasons.get(str(m["id"])) or "Matches your request based on genre, rating and popularity.",
    } for m in top]

    return jsonify({"reply": reply, "movies": movies, "success": True})
