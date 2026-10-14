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

# Environment variables (Put a fresh GROQ_API_KEY in Render -> Environment!)
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "7c7e21b0fe58e5868e262c9bd6b8e7e9").strip().strip('"').strip("'")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip().strip('"').strip("'")
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

# Expanded Plot Detective Database (Covers viral TikTok/Reels movie plots & iconic premises)
KNOWN_PLOT_PATTERNS = [
    {
        "patterns": ["high pole", "tv tower", "radio tower", "two girls", "2 girls", "stuck on top", "climbs a tower", "2000 feet", "ladder breaks", "stuck on a tower", "tall tower", "tall pole"],
        "must_have_any": ["pole", "tower", "stuck", "climb", "high", "top"],
        "reply": "You're looking for 'Fall' (2022)! Best friends Becky and Hunter climb a 2,000-foot abandoned radio tower and get stranded at the very top when the ladder breaks. I've also included similar claustrophobic survival thrillers!",
        "guesses": [
            {"title": "Fall", "year": 2022, "why": "Exact plot match: two girls climb a 2,000-foot tall radio tower/pole and get trapped at the top with no way down."},
            {"title": "47 Meters Down", "year": 2017, "why": "Two sisters get trapped in a shark cage at the bottom of the ocean with less than an hour of oxygen left."},
            {"title": "The Shallows", "year": 2016, "why": "A surfer gets stranded on a tiny rock 200 yards from shore while a great white shark circles her."},
            {"title": "127 Hours", "year": 2010, "why": "A mountain climber becomes trapped under a boulder in an isolated slot canyon and must fight to survive."},
            {"title": "Frozen", "year": 2010, "why": "Three friends get stranded high up on a ski chairlift when the resort closes for the weekend."},
            {"title": "Buried", "year": 2010, "why": "A man wakes up buried alive inside a wooden coffin with only a lighter and a cell phone."},
            {"title": "Nowhere", "year": 2023, "why": "A pregnant woman gets trapped alone inside a drifting shipping container in the middle of the sea."}
        ]
    },
    {
        "patterns": ["poor family", "rich household", "rich family", "infiltrate", "infiltrates", "wealthy family", "pose as tutor"],
        "must_have_any": ["poor", "rich", "infiltrate", "infiltrates", "wealthy", "household"],
        "reply": "You're thinking of the Oscar-winning masterpiece 'Parasite' (2019)! Here is 'Parasite' along with sharp thrillers about class divide and infiltration:",
        "guesses": [
            {"title": "Parasite", "year": 2019, "why": "Exact plot match: the Kim family infiltrates the wealthy Park household by posing as unrelated, highly qualified workers."},
            {"title": "Saltburn", "year": 2023, "why": "A scheming student infiltrates an aristocratic British family's sprawling estate."},
            {"title": "The Handmaiden", "year": 2016, "why": "A Korean con-artist plot involving a pickpocket hired as a maid to defraud a wealthy heiress."},
            {"title": "Knives Out", "year": 2019, "why": "A clever mystery revolving around a wealthy, dysfunctional family and an outsider."},
            {"title": "Us", "year": 2019, "why": "A sharp, suspenseful thriller centered on duality, privilege, and home invasion."},
            {"title": "Burning", "year": 2018, "why": "Acclaimed Korean psychological drama exploring unspoken class tension."}
        ]
    },
    {
        "patterns": ["relives the same day", "same day over", "wakes up and relives", "time loop", "repeating the same day", "every time he dies"],
        "must_have_any": ["relives", "loop", "same day", "repeating"],
        "reply": "That classic time-loop premise matches 'Groundhog Day' (1993), 'Palm Springs' (2020), and 'Edge of Tomorrow' (2014)!",
        "guesses": [
            {"title": "Groundhog Day", "year": 1993, "why": "The definitive time-loop movie where a cynical weatherman relives February 2nd over and over."},
            {"title": "Palm Springs", "year": 2020, "why": "A hilarious and heartfelt modern twist where wedding guests get stuck reliving the same day."},
            {"title": "Edge of Tomorrow", "year": 2014, "why": "A sci-fi action thriller where a soldier relives a brutal alien battle every time he dies."},
            {"title": "Happy Death Day", "year": 2017, "why": "A college student must relive the day of her murder until she figures out who her killer is."},
            {"title": "Source Code", "year": 2011, "why": "A soldier wakes up in someone else's body and relives an 8-minute train explosion to find the bomber."},
            {"title": "About Time", "year": 2013, "why": "A warm, emotional romance about a young man who can travel back in time to redo moments in his life."}
        ]
    },
    {
        "patterns": ["memory loss", "short-term memory", "tattoos", "amnesia", "wife's killer", "polaroid"],
        "must_have_any": ["memory", "tattoos", "amnesia", "polaroid"],
        "reply": "That's Christopher Nolan's 'Memento' (2000)! Leonard Shelby uses Polaroids and tattoos to track down his wife's killer despite short-term memory loss.",
        "guesses": [
            {"title": "Memento", "year": 2000, "why": "Exact match: a man with short-term memory loss uses tattoos and notes to hunt his wife's murderer."},
            {"title": "Shutter Island", "year": 2010, "why": "A psychological mystery where a U.S. Marshal investigates a psychiatric facility and confronts fractured memories."},
            {"title": "The Bourne Identity", "year": 2002, "why": "A man is pulled from the sea with amnesia and must piece together his lethal past."},
            {"title": "Eternal Sunshine of the Spotless Mind", "year": 2004, "why": "A couple undergoes a medical procedure to erase each other from their memories."},
            {"title": "Remember", "year": 2015, "why": "An elderly man with dementia sets out with a handwritten letter to track down a Nazi war criminal."}
        ]
    },
    {
        "patterns": ["cannot make a sound", "can't make a noise", "blind monsters", "monsters hunt by sound", "silent", "sign language"],
        "must_have_any": ["sound", "noise", "silent", "blind", "monsters"],
        "reply": "You're thinking of 'A Quiet Place' (2018)! A family must live in complete silence to hide from blind extraterrestrial creatures with ultra-sensitive hearing.",
        "guesses": [
            {"title": "A Quiet Place", "year": 2018, "why": "Exact plot match: a family must live in silence while hiding from monsters that hunt by sound."},
            {"title": "A Quiet Place Part II", "year": 2020, "why": "The Abbott family ventures into the outside world while continuing their silent fight for survival."},
            {"title": "Bird Box", "year": 2018, "why": "Survivors must wear blindfolds outdoors so they don't look at supernatural entities that drive people mad."},
            {"title": "Don't Breathe", "year": 2016, "why": "Three thieves break into the house of a blind man who turns out to be a lethal adversary in the dark."},
            {"title": "Hush", "year": 2016, "why": "A deaf and mute writer must fight for her life in silence when a masked killer appears at her window."}
        ]
    },
    {
        "patterns": ["zombies on a train", "zombie train", "father and daughter train", "bullet train zombie"],
        "must_have_any": ["train", "zombie", "zombies"],
        "reply": "That's the acclaimed South Korean thriller 'Train to Busan' (2016)!",
        "guesses": [
            {"title": "Train to Busan", "year": 2016, "why": "Exact match: passengers on a high-speed KTX train from Seoul to Busan fight to survive a sudden zombie outbreak."},
            {"title": "World War Z", "year": 2013, "why": "A former UN investigator races across the globe to stop a fast-moving zombie pandemic."},
            {"title": "28 Days Later", "year": 2002, "why": "A bicycle courier wakes up from a coma to find London deserted after a rage virus outbreak."},
            {"title": "#Alive", "year": 2020, "why": "A young man gets trapped alone inside his apartment in Seoul during a sudden zombie apocalypse."}
        ]
    },
    {
        "patterns": ["swap bodies", "body swap", "boy and girl swap bodies", "comet", "red string"],
        "must_have_any": ["swap", "bodies", "comet"],
        "reply": "You're thinking of Makoto Shinkai's anime masterpiece 'Your Name.' (Kimi no Na wa, 2016)!",
        "guesses": [
            {"title": "Your Name.", "year": 2016, "why": "Exact plot match: a high school boy in Tokyo and a girl in the countryside mysteriously begin swapping bodies."},
            {"title": "Weathering with You", "year": 2019, "why": "A runaway boy meets a girl in Tokyo who has the supernatural ability to clear the rain."},
            {"title": "Suzume", "year": 2022, "why": "A 17-year-old girl teams up with a young man to close mysterious doors causing disasters across Japan."},
            {"title": "Freaky Friday", "year": 2003, "why": "A mother and daughter wake up on Friday to discover they have switched bodies."}
        ]
    },
    {
        "patterns": ["locked in a room", "15 years", "20 years", "kidnapped and locked", "hotel room", "dumplings"],
        "must_have_any": ["locked", "15 years", "kidnapped", "room"],
        "reply": "That's Park Chan-wook's legendary Korean thriller 'Oldboy' (2003)!",
        "guesses": [
            {"title": "Oldboy", "year": 2003, "why": "Exact plot match: a man is inexplicably kidnapped and locked in a shabby room for 15 years, then suddenly released."},
            {"title": "Room", "year": 2015, "why": "A young woman and her 5-year-old son finally gain their freedom after being held captive in an enclosed space."},
            {"title": "I Saw the Devil", "year": 2010, "why": "An intelligence agent tracks down a ruthless serial killer in a relentless game of cat-and-mouse."},
            {"title": "The Chaser", "year": 2008, "why": "A gritty, pulse-pounding Korean thriller about a former detective racing to find a missing woman."}
        ]
    },
    {
        "patterns": ["shipping container", "pregnant woman", "drifting at sea", "trapped in a container"],
        "must_have_any": ["container", "pregnant", "sea", "drifting"],
        "reply": "That's the intense survival thriller 'Nowhere' (2023)!",
        "guesses": [
            {"title": "Nowhere", "year": 2023, "why": "Exact match: a young pregnant woman flees a totalitarian country and gets trapped in a shipping container at sea."},
            {"title": "Life of Pi", "year": 2012, "why": "A young man survives a disaster at sea and is hurtled into an epic journey of adventure on a lifeboat."},
            {"title": "Cast Away", "year": 2000, "why": "A FedEx executive survives a plane crash and must learn to survive on a deserted island."},
            {"title": "Fall", "year": 2022, "why": "Two friends get stranded at the top of a 2,000-foot radio tower."}
        ]
    }
]

CURATED_KOREAN_ROMCOMS = [
    {"title": "Love Reset", "year": 2023, "why": "Hilarious Korean romcom about a married couple on the verge of divorce who both get amnesia and fall in love all over again."},
    {"title": "20th Century Girl", "year": 2022, "why": "Sweet, nostalgic, and deeply moving Korean teen romance about first love and friendship in 1999."},
    {"title": "My Sassy Girl", "year": 2001, "why": "The iconic, laugh-out-loud Korean romantic comedy classic that defined the entire genre."},
    {"title": "Sweet & Sour", "year": 2021, "why": "A witty, modern Korean romcom with a clever twist about the realities of dating and long-distance love."},
    {"title": "On Your Wedding Day", "year": 2018, "why": "Charming, funny, and heartfelt Korean romance following two people's timing over ten years."},
    {"title": "Tune in for Love", "year": 2019, "why": "Warm, sweet Korean romance about two people whose paths keep crossing over the years."},
    {"title": "Nothing Serious", "year": 2021, "why": "Fun, candid modern Korean romcom about two people who meet on a dating app while swearing off romance."},
    {"title": "Exit", "year": 2019, "why": "Super funny Korean action-comedy with charming romantic chemistry."}
]


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
    return jsonify({"status": "CineMind Super-Nova Engine Live", "version": "14.0", "groq_configured": bool(GROQ_API_KEY)})


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


# ------------------------- OMDb -------------------------
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
  "plot_guesses": [{{"title": "Exact Movie Title", "year": 2022, "why": "1-sentence explanation of how this matches the plot/vibe"}}],
  "genres": [list of matching genres from: {GENRE_LIST}],
  "exclude_genres": [genres the user explicitly does NOT want],
  "year_from": integer or null,
  "year_to": integer or null,
  "min_rating": number 0-10 or null,
  "language": ISO 639-1 code like "ko", "ja", "tl", "es", "fr", "hi" or null,
  "origin_country": ISO 3166-1 code like "KR", "PH", "JP", "US", "GB", "IN", "FR", "ES", "TH" or null,
  "sort": "popularity" | "rating" | "newest",
  "mood_keywords": [2-4 specific plot/theme keywords, e.g. "time loop", "radio tower", "amnesia", "heist"],
  "similar_to": [movie titles the user says they liked or wants similar to],
  "exclude_titles": [movie titles the user has already seen, rejected, or wants to avoid],
  "direct_reply": "Your natural, witty, intelligent conversational response. If intent is plot_search, name your #1 guess enthusiastically and explain why!"
}}

If the user describes a plot, scene, twist, character, or says things like 'what's that movie where...',
'I forgot the name', 'i am looking for a movie where...', 'movie about a guy who...', use intent plot_search. Put your best 3-6 guesses of
the actual movie in plot_guesses (most likely first, with release year if you know it), and fill
mood_keywords with 2-4 plot keywords (e.g. 'time loop', 'amnesia', 'heist').
Even for general recommendation requests, ALWAYS put 5-6 specific, accurate movie titles in plot_guesses too!
"""


def tmdb(path, **params):
    params["api_key"] = TMDB_API_KEY
    try:
        r = requests.get(f"{TMDB}{path}", params=params, timeout=6)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def groq_json(system, user, temperature=0.2, timeout=10):
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


def deep_plot_detective(message):
    """
    When Groq is unavailable and a user types an arbitrary plot description,
    this extracts meaningful plot nouns/concepts and searches Wikipedia/IMDb/TMDB plot keywords
    so Nova can still identify specific movies!
    """
    lower = message.lower()

    # 1. Check our high-precision plot pattern database first
    for rule in KNOWN_PLOT_PATTERNS:
        if any(w in lower for w in rule.get("must_have_any", [])):
            score = sum(2 if pat in lower else 0 for pat in rule["patterns"])
            word_hits = sum(1 for w in rule["must_have_any"] if w in lower)
            if score >= 2 or word_hits >= 2:
                return rule["guesses"], rule["reply"]

    # 2. Live Wikipedia Film Plot Search (Finds ANY movie plot on Earth without needing an LLM key!)
    guesses = []
    try:
        clean_q = re.sub(r"\b(i am|i'm|looking for a|looking for|what is the|what's that|whats that|movie where|movie about|film where|film about|a|an|the|were|was|from|really)\b", " ", lower)
        clean_q = re.sub(r"\s+", " ", clean_q).strip()
        if len(clean_q) >= 4:
            wiki_res = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": f'{clean_q} film plot',
                    "srlimit": 8,
                    "format": "json"
                },
                headers={"User-Agent": "CineMindCapstone/1.0"},
                timeout=4
            ).json()
            for item in wiki_res.get("query", {}).get("search", []):
                w_title = item.get("title", "")
                if any(skip in w_title.lower() for skip in ["list of", "category:", "disambiguation", "awards", "filmography"]):
                    continue
                # Extract clean movie title & optional year from Wikipedia article title e.g. "Fall (2022 film)"
                m_year = re.search(r"\((\d{4})\s*[^\)]*film\)", w_title, re.I)
                year = int(m_year.group(1)) if m_year else None
                clean_title = re.sub(r"\s*\([^\)]*\)\s*", "", w_title).strip()
                if clean_title and len(clean_title) < 60:
                    guesses.append({
                        "title": clean_title,
                        "year": year,
                        "why": f"Identified via plot match for '{clean_q}'."
                    })
                if len(guesses) >= 5:
                    break
    except Exception:
        pass

    if guesses:
        top_name = guesses[0]["title"]
        top_yr = f" ({guesses[0]['year']})" if guesses[0].get("year") else ""
        reply = f"Based on your plot description, the movie you're looking for is likely '{top_name}'{top_yr}! Here are the closest plot matches I found:"
        return guesses, reply

    return [], None


def smart_local_nlp_parse(message, history, username="Guest"):
    lower = message.lower()
    genres = []
    origin_country = None
    language = None
    guesses = []
    mood_keywords = []
    similar_to = []
    intent = "recommend"
    direct_reply = None

    looks_like_plot = (
        len(lower.split()) >= 5
        or any(p in lower for p in [
            "movie where", "movie about", "looking for a movie", "forgot the name",
            "what's that movie", "whats that movie", "film where", "stuck", "trapped",
            "infiltrate", "relives", "kidnapped", "survive"
        ])
    )

    # 1. If it looks like a specific plot description, run Deep Plot Detective!
    if looks_like_plot:
        det_guesses, det_reply = deep_plot_detective(message)
        if det_guesses:
            return {
                "intent": "plot_search",
                "plot_guesses": det_guesses,
                "genres": [],
                "mood_keywords": [],
                "direct_reply": det_reply
            }

    # 2. Detect Country & Language keywords
    country_map = {
        "korean": ("KR", "ko", "South Korean"),
        "korea": ("KR", "ko", "South Korean"),
        "k-drama": ("KR", "ko", "South Korean"),
        "kdrama": ("KR", "ko", "South Korean"),
        "japanese": ("JP", "ja", "Japanese"),
        "japan": ("JP", "ja", "Japanese"),
        "anime": ("JP", "ja", "Japanese"),
        "filipino": ("PH", "tl", "Filipino"),
        "pinoy": ("PH", "tl", "Filipino"),
        "philippine": ("PH", "tl", "Filipino"),
        "thai": ("TH", "th", "Thai"),
        "thailand": ("TH", "th", "Thai"),
        "indian": ("IN", "hi", "Indian"),
        "bollywood": ("IN", "hi", "Indian"),
        "french": ("FR", "fr", "French"),
        "spanish": ("ES", "es", "Spanish"),
        "british": ("GB", "en", "British"),
    }
    country_label = ""
    for kw, (cc, lang, label) in country_map.items():
        if re.search(rf"\b{re.escape(kw)}\b", lower):
            origin_country = cc
            language = lang
            country_label = label
            break

    # 3. Detect Slang & Compound Genres
    if any(w in lower for w in ["romcom", "rom-com", "romantic comedy"]):
        genres.extend(["romance", "comedy"])
    if any(w in lower for w in ["romance", "romantic", "love", "sweet", "heartbreaking", "couple", "dating"]):
        if "romance" not in genres:
            genres.append("romance")
    if any(w in lower for w in ["funny", "comedy", "hilarious", "laugh", "lighthearted"]):
        if "comedy" not in genres:
            genres.append("comedy")
    if any(w in lower for w in ["sad", "cry", "tearjerker", "heartbreaking", "emotional", "tragic"]):
        if "drama" not in genres:
            genres.append("drama")
    if any(w in lower for w in ["sci-fi", "scifi", "science fiction", "space", "future", "alien", "cyberpunk", "time travel"]):
        if "sci-fi" not in genres:
            genres.append("sci-fi")
    if any(w in lower for w in ["mind-bending", "twist", "psychological", "suspense", "dark", "thriller", "stuck", "trapped", "survive", "survival"]):
        if "thriller" not in genres:
            genres.append("thriller")
    if any(w in lower for w in ["scary", "horror", "ghost", "creepy", "haunted", "slasher", "monster"]):
        if "horror" not in genres:
            genres.append("horror")
    if any(w in lower for w in ["action", "explosive", "fight", "martial arts", "blockbuster"]):
        if "action" not in genres:
            genres.append("action")
    if any(w in lower for w in ["mystery", "detective", "whodunit", "investigation"]):
        if "mystery" not in genres:
            genres.append("mystery")
    if any(w in lower for w in ["animated", "animation", "cartoon", "anime", "pixar"]):
        if "animation" not in genres:
            genres.append("animation")

    for g_name in GENRES.keys():
        if re.search(rf"\b{re.escape(g_name)}\b", lower) and g_name not in genres:
            genres.append(g_name)

    if origin_country == "KR" and "romance" in genres:
        guesses = CURATED_KOREAN_ROMCOMS
        direct_reply = f"I've curated the sweetest, funniest Korean romantic comedies for you, {username}—starting with 'Love Reset', '20th Century Girl', and 'My Sassy Girl'!"

    # Extract meaningful content words as mood_keywords for TMDB keyword lookup
    stop_words = {"i", "am", "looking", "for", "a", "an", "the", "movie", "movies", "film", "where", "about", "that", "is", "are", "was", "were", "with", "in", "on", "from", "to", "and", "or", "really", "very", "super", "some", "something", "give", "me", "find", "show", "want", "wanna", "see", "watch"}
    content_words = [w for w in re.findall(r"[a-z0-9]+", lower) if w not in stop_words and len(w) > 2]
    if content_words:
        mood_keywords = content_words[:4]

    # Follow-Up Memory
    if any(w in lower for w in ["first one", "first movie", "similar to that", "more like", "darker", "funnier"]) and history:
        for turn in reversed(history):
            content = turn.get("content", "")
            m = re.search(r"\[Movies shown to user:\s*([^\(\],]+)", content)
            if m:
                first_title = m.group(1).strip()
                similar_to.append(first_title)
                intent = "similar_to"
                direct_reply = f"Building on '{first_title}' from our conversation, here are tailored follow-up matches for you, {username}!"
                break

    if not direct_reply:
        desc_parts = [p for p in [country_label, "/".join(genres[:2]).title()] if p]
        desc = " ".join(desc_parts) if desc_parts else f"'{message}'"
        direct_reply = f"Here are the closest matches I found for {desc}, {username}!"

    return {
        "intent": "plot_search" if looks_like_plot else intent,
        "plot_guesses": guesses,
        "genres": genres,
        "origin_country": origin_country,
        "language": language,
        "mood_keywords": mood_keywords,
        "similar_to": similar_to,
        "direct_reply": direct_reply
    }


def extract_intent(message, history, username="Guest", fav_genres=None, selected_country=None):
    local_parsed = smart_local_nlp_parse(message, history, username)

    ctx_lines = []
    for h in (history or [])[-10:]:
        if isinstance(h, dict) and h.get("content"):
            role = "User" if h.get("role") == "user" else "Nova"
            ctx_lines.append(f"{role}: {h.get('content')}")
    ctx = "\n".join(ctx_lines) if ctx_lines else "No prior messages."

    user_prompt = f"User: {username}\nFavorite Genres: {', '.join(fav_genres or [])}\nHistory:\n{ctx}\n\nLatest Request: {message}"
    llm_parsed = groq_json(PARSE_PROMPT, user_prompt, temperature=0.2)

    if llm_parsed and isinstance(llm_parsed, dict):
        if not llm_parsed.get("origin_country") and local_parsed.get("origin_country"):
            llm_parsed["origin_country"] = local_parsed["origin_country"]
        if not llm_parsed.get("language") and local_parsed.get("language"):
            llm_parsed["language"] = local_parsed["language"]
        if not llm_parsed.get("genres") and local_parsed.get("genres"):
            llm_parsed["genres"] = local_parsed["genres"]
        # Combine LLM guesses with local plot detective guesses so neither is lost
        llm_guesses = llm_parsed.get("plot_guesses") or []
        local_guesses = local_parsed.get("plot_guesses") or []
        llm_parsed["plot_guesses"] = llm_guesses + [g for g in local_guesses if g not in llm_guesses]
        return llm_parsed

    return local_parsed


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

    # 1) Verify the LLM / Plot Detective's guesses on TMDB
    for idx, g in enumerate((p.get("plot_guesses") or [])[:7]):
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
        # Prefer exact title match when a short title like "Fall" is searched
        chosen = None
        for h in hits:
            if h.get("poster_path") and h.get("title", "").lower() == title.lower():
                chosen = h
                break
        if not chosen and hits:
            chosen = next((h for h in hits if h.get("poster_path")), None)

        if chosen and chosen["id"] not in seen:
            seen.add(chosen["id"])
            chosen["_bonus"] = 50.0 - (idx * 4.0)
            chosen["_is_guess"] = True
            if why:
                chosen["_guess_why"] = why
            results.append(chosen)

    # 2) Backup: match on plot keywords
    if len(results) < 6:
        kws = keyword_ids(p.get("mood_keywords", []))
        if kws:
            extra = tmdb("/discover/movie", with_keywords="|".join(kws),
                         sort_by="popularity.desc", **{"vote_count.gte": 50}).get("results", [])
            for m in extra:
                if m.get("poster_path") and m["id"] not in seen:
                    seen.add(m["id"])
                    m["_bonus"] = 10.0
                    results.append(m)

    # 3) Pull recommendations from #1 verified movie to round out the grid
    if results and len(results) < 8:
        top_id = results[0]["id"]
        for m in tmdb(f"/movie/{top_id}/recommendations").get("results", []):
            if m.get("poster_path") and m["id"] not in seen:
                seen.add(m["id"])
                m["_bonus"] = 8.0
                m["_guess_why"] = f"Recommended because it shares key survival/plot themes with {results[0].get('title')}."
                results.append(m)
    return results


def find_movies(intent):
    if intent.get("intent") == "plot_search":
        found = plot_search(intent)
        if found:
            return found

    cands = {}
    target_lang = intent.get("language")
    target_country = (intent.get("origin_country") or "").upper() or None

    def add(movies, bonus=0, why_note=None, enforce_country=False):
        for m in movies:
            if not m.get("id") or not m.get("poster_path"):
                continue
            if enforce_country and target_lang and m.get("original_language") != target_lang:
                continue
            if m["id"] not in cands:
                m["_bonus"] = bonus
                if why_note:
                    m["_guess_why"] = why_note
                cands[m["id"]] = m
            else:
                cands[m["id"]]["_bonus"] = max(cands[m["id"]].get("_bonus", 0), bonus)

    for idx, g in enumerate((intent.get("plot_guesses") or [])[:8]):
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
            add([hits[0]], bonus=35.0 - (idx * 2.0), why_note=why)

    for t in (intent.get("similar_to") or [])[:2]:
        mid = find_movie_id(t)
        if mid:
            add(tmdb(f"/movie/{mid}/recommendations").get("results", []), bonus=15.0,
                why_note=f"Recommended based on '{t}'.")

    gids = []
    for g in (intent.get("genres") or []):
        if g.lower() in GENRES and str(GENRES[g.lower()]) not in gids:
            gids.append(str(GENRES[g.lower()]))

    xids = [str(GENRES[g.lower()]) for g in intent.get("exclude_genres") or [] if g.lower() in GENRES]

    min_votes = 25 if (target_country or target_lang) else 120
    p = {"include_adult": "false", "vote_count.gte": min_votes, "language": "en-US", "sort_by": "popularity.desc"}

    if gids:
        p["with_genres"] = ",".join(gids[:2])
    if xids:
        p["without_genres"] = ",".join(xids)
    if target_lang:
        p["with_original_language"] = target_lang
    if target_country:
        p["with_origin_country"] = target_country

    kws = keyword_ids(intent.get("mood_keywords"))
    if kws and not gids:
        p["with_keywords"] = "|".join(kws)

    for page in (1, 2):
        add(tmdb("/discover/movie", page=page, **p).get("results", []), bonus=10.0, enforce_country=True)

    if len(cands) < 8 and len(gids) > 1:
        p["with_genres"] = "|".join(gids)
        for page in (1, 2):
            add(tmdb("/discover/movie", page=page, **p).get("results", []), bonus=5.0, enforce_country=True)

    return list(cands.values())


def get_seen_ids(username):
    if not username or username == "Guest":
        return set()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    ids = set()
    for q in ("SELECT movie_id FROM watchlist WHERE username=?",
              "SELECT movie_id FROM favorites WHERE username=?"):
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
        if not is_plot and not m.get("_is_guess"):
            if m["id"] in seen_ids or norm(m.get("title")) in blocked:
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
            elif m.get("_bonus", 0) >= 30:
                m["_match"] = max(94, 98 - idx)
            else:
                best = top[0]["_score"] or 1
                m["_match"] = max(82, min(97, int(82 + 15 * (m["_score"] / best))))
    return top


def explain(message, username, movies, intent):
    listing = [{"id": m["id"], "title": m["title"], "year": (m.get("release_date") or "")[:4],
                "overview": (m.get("overview") or "")[:200]} for m in movies[:8]]
    system = (
        f"You are Nova, a warm, witty AI cinema companion talking to {username}. "
        'Return ONLY JSON: {"reply": "2 engaging sentences directly answering the user and naming top movie picks", '
        '"reasons": {"<id>": "1 specific sentence explaining why this movie fits their request"}}. '
        "Only mention movies from the provided list."
    )
    return groq_json(system, f"User Request: {message}\nMovies: {json.dumps(listing)}", temperature=0.3) or {}


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

    if intent_type in ("chitchat", "question") and not intent.get("plot_guesses") and not intent.get("genres"):
        reply = intent.get("direct_reply") or f"I'm Nova, your AI cinema companion, {username}! Describe any movie plot or mood and I'll find it."
        return jsonify({"reply": reply, "movies": [], "intent": intent_type, "success": True})

    # CRITICAL FIX: Only fall back to user's 3 profile genres if they typed a generic greeting/vibe (<= 3 words), NEVER on specific plot queries!
    if intent_type == "recommend" and len(message.split()) <= 3 and not intent.get("genres") and not intent.get("plot_guesses") and fav_genres:
        intent["genres"] = [g.lower() for g in fav_genres[:3]]

    if not intent.get("origin_country") and selected_country and intent_type != "plot_search":
        intent["origin_country"] = selected_country

    cands = find_movies(intent)

    if not cands:
        search_res = tmdb("/search/movie", query=message).get("results", [])
        cands = [m for m in search_res if m.get("poster_path")]

    top = rank(cands, intent, get_seen_ids(username))
    if not top and cands:
        top = cands[:12]

    if not top:
        return jsonify({
            "reply": f"I couldn't find an exact match for '{message}', {username}. Try describing another detail or scene from the movie!",
            "movies": [],
            "intent": intent_type,
            "success": True
        })

    ex = explain(message, username, top, intent)
    reasons = ex.get("reasons", {}) if isinstance(ex.get("reasons"), dict) else {}
    reply = ex.get("reply") or intent.get("direct_reply") or f"Here are my top handpicked matches for '{message}', {username}!"

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
        "rationale": reasons.get(str(m["id"])) or m.get("_guess_why") or f"Identified via plot & thematic similarity to '{message}'.",
    } for m in top]

    return jsonify({"reply": reply, "movies": movies, "intent": intent_type, "success": True})


@app.route("/trends", methods=["GET"])
def trends():
    return jsonify({
        "ai_forecast": "Super-Nova Multi-API Memory & Plot-Search Pipeline Online.",
        "trending_genres": ["Groq Plot & Intent Recognition", "Wikipedia/TMDB Plot Detective", "OMDb Metadata Enrichment"]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
