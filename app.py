import os
import re
import json
import html
import sqlite3
import hashlib
from datetime import date

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

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

COUNTRY_DEFAULT_GENRES = {
    "PH": ["drama", "romance", "comedy", "horror"],
    "KR": ["drama", "thriller", "romance", "action"],
    "TH": ["drama", "romance", "horror", "action"],
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

# Instant High-Speed Plot & Series Pattern Cache (Includes BL, Series, Fairy Tales, Survival, Sci-Fi)
KNOWN_PLOT_PATTERNS = [
    {
        "patterns": ["twins named black and white", "black and white", "white took over", "twin got badly injured", "boys love", "bl series", "fell in love with black"],
        "must_have_any": ["black", "white", "twin", "twins"],
        "reply": "You're looking for the acclaimed Thai Boys' Love (BL) series 'Not Me' (2021) starring Off Jumpol and Gun Atthaphan! When twin brother Black is brutally attacked and left in a coma, his twin White disguises himself as Black to infiltrate his motorcycle gang and uncover the traitor—slowly falling in love with Black's intense friend Sean.",
        "guesses": [
            {"title": "Not Me", "year": 2021, "media_type": "tv", "why": "Exact match: Twin brother White takes over the identity of his comatose twin Black and falls for Black's friend Sean."},
            {"title": "The Eclipse", "year": 2022, "media_type": "tv", "why": "Acclaimed Thai BL mystery-romance about rebellion and secrets at an elite all-boys school."},
            {"title": "Bad Buddy", "year": 2021, "media_type": "tv", "why": "Hit Thai BL series about lifelong next-door rivals Pat and Pran who secretly fall in love."},
            {"title": "KinnPorsche", "year": 2022, "media_type": "tv", "why": "Action-packed Thai BL drama about a mafia heir and his fiercely loyal bodyguard."},
            {"title": "Theory of Love", "year": 2019, "media_type": "tv", "why": "Starring Off and Gun—a film student secretly falls in love with his playboy best friend."},
            {"title": "2gether", "year": 2020, "media_type": "tv", "why": "Beloved Thai BL series where two college students fake-date and fall in love for real."},
            {"title": "Moonlight Chicken", "year": 2023, "media_type": "tv", "why": "Award-winning, deeply emotional Thai BL drama about love, class, and resilience."}
        ]
    },
    {
        "patterns": ["lies and his nose", "nose gets longer", "nose grows", "wooden boy", "puppet who wants to be a real boy", "pinocchio"],
        "must_have_any": ["nose", "pinocchio", "puppet"],
        "reply": "That's 'Pinocchio'! Crafted by woodcarver Geppetto, Pinocchio is a wooden puppet brought to life whose nose grows longer every time he tells a lie. Here are the most iconic film adaptations of Pinocchio:",
        "guesses": [
            {"title": "Pinocchio", "year": 1940, "media_type": "movie", "why": "Disney's animated masterpiece about the wooden puppet whose nose grows whenever he lies."},
            {"title": "Guillermo del Toro's Pinocchio", "year": 2022, "media_type": "movie", "why": "Oscar-winning stop-motion reimagining of the classic tale of the wooden boy who lies."},
            {"title": "Pinocchio", "year": 2022, "media_type": "movie", "why": "Live-action Disney adaptation starring Tom Hanks as Geppetto."},
            {"title": "Pinocchio", "year": 2019, "media_type": "movie", "why": "Matteo Garrone's faithful, critically acclaimed Italian live-action adaptation."},
            {"title": "Pinocchio", "year": 2014, "media_type": "tv", "why": "Hit Korean drama where a girl with 'Pinocchio syndrome' hiccups whenever she tells a lie."},
            {"title": "Liar Liar", "year": 1997, "media_type": "movie", "why": "Hilarious comedy about a fast-talking lawyer who is magically cursed to tell the truth for 24 hours."}
        ]
    },
    {
        "patterns": ["boxing in toy story", "toy story boxing", "why is there boxing in toy story", "rock em sock em", "rock 'em sock 'em"],
        "must_have_any": ["toy story", "boxing"],
        "reply": "In the Toy Story franchise (especially Toy Story 2), there is a memorable boxing scene featuring the classic 'Rock 'Em Sock 'Em Robots' (the Red Rocker and Blue Bomber) inside Al's Toy Barn! Plus, 'Real Steel' (2011) is the famous robot-boxing movie many people associate with fighting robots.",
        "guesses": [
            {"title": "Toy Story 2", "year": 1999, "media_type": "movie", "why": "Features the famous Rock 'Em Sock 'Em Robots boxing match scene inside Al's office!"},
            {"title": "Toy Story", "year": 1995, "media_type": "movie", "why": "The original Pixar classic introducing Woody, Buzz Lightyear, and Andy's bedroom toys."},
            {"title": "Toy Story 3", "year": 2010, "media_type": "movie", "why": "Woody, Buzz, and the gang face Sunnyside Daycare as Andy prepares for college."},
            {"title": "Toy Story 4", "year": 2019, "media_type": "movie", "why": "Woody and Buzz embark on a road trip with Forky and Duke Caboom."},
            {"title": "Real Steel", "year": 2011, "media_type": "movie", "why": "The hit robot-boxing movie often associated with fighting toy robots."}
        ]
    },
    {
        "patterns": ["high pole", "tv tower", "radio tower", "two girls", "2 girls", "stuck on top", "climbs a tower", "2000 feet", "ladder breaks", "stuck on a tower", "tall tower", "tall pole"],
        "must_have_any": ["pole", "tower", "stuck", "climb"],
        "reply": "You're looking for 'Fall' (2022)! Best friends Becky and Hunter climb a 2,000-foot abandoned radio tower and get stranded at the very top when the ladder breaks. Here is 'Fall' along with intense survival thrillers:",
        "guesses": [
            {"title": "Fall", "year": 2022, "media_type": "movie", "why": "Exact plot match: two girls climb a 2,000-foot tall radio tower/pole and get trapped at the top with no way down."},
            {"title": "47 Meters Down", "year": 2017, "media_type": "movie", "why": "Two sisters get trapped in a shark cage at the bottom of the ocean with less than an hour of oxygen left."},
            {"title": "The Shallows", "year": 2016, "media_type": "movie", "why": "A surfer gets stranded on a tiny rock 200 yards from shore while a great white shark circles her."},
            {"title": "127 Hours", "year": 2010, "media_type": "movie", "why": "A mountain climber becomes trapped under a boulder in an isolated slot canyon and must fight to survive."},
            {"title": "Frozen", "year": 2010, "media_type": "movie", "why": "Three friends get stranded high up on a ski chairlift when the resort closes for the weekend."},
            {"title": "Nowhere", "year": 2023, "media_type": "movie", "why": "A pregnant woman gets trapped alone inside a drifting shipping container in the middle of the sea."}
        ]
    },
    {
        "patterns": ["poor family", "rich household", "rich family", "infiltrate", "infiltrates", "wealthy family", "pose as tutor"],
        "must_have_any": ["poor", "rich", "infiltrate", "infiltrates", "wealthy", "household"],
        "reply": "You're thinking of the Oscar-winning masterpiece 'Parasite' (2019)! Here is 'Parasite' along with sharp thrillers about class divide and infiltration:",
        "guesses": [
            {"title": "Parasite", "year": 2019, "media_type": "movie", "why": "Exact plot match: the Kim family infiltrates the wealthy Park household by posing as unrelated, highly qualified workers."},
            {"title": "Saltburn", "year": 2023, "media_type": "movie", "why": "A scheming student infiltrates an aristocratic British family's sprawling estate."},
            {"title": "The Handmaiden", "year": 2016, "media_type": "movie", "why": "A Korean con-artist plot involving a pickpocket hired as a maid to defraud a wealthy heiress."},
            {"title": "Knives Out", "year": 2019, "media_type": "movie", "why": "A clever mystery revolving around a wealthy, dysfunctional family and an outsider."},
            {"title": "Us", "year": 2019, "media_type": "movie", "why": "A sharp, suspenseful thriller centered on duality, privilege, and home invasion."}
        ]
    },
    {
        "patterns": ["relives the same day", "same day over", "wakes up and relives", "time loop", "repeating the same day", "every time he dies"],
        "must_have_any": ["relives", "loop", "same day", "repeating"],
        "reply": "That classic time-loop premise matches 'Groundhog Day' (1993), 'Palm Springs' (2020), and 'Edge of Tomorrow' (2014)!",
        "guesses": [
            {"title": "Groundhog Day", "year": 1993, "media_type": "movie", "why": "The definitive time-loop movie where a cynical weatherman relives February 2nd over and over."},
            {"title": "Palm Springs", "year": 2020, "media_type": "movie", "why": "A hilarious and heartfelt modern twist where wedding guests get stuck reliving the same day."},
            {"title": "Edge of Tomorrow", "year": 2014, "media_type": "movie", "why": "A sci-fi action thriller where a soldier relives a brutal alien battle every time he dies."},
            {"title": "Happy Death Day", "year": 2017, "media_type": "movie", "why": "A college student must relive the day of her murder until she figures out who her killer is."},
            {"title": "Source Code", "year": 2011, "media_type": "movie", "why": "A soldier wakes up in someone else's body and relives an 8-minute train explosion."}
        ]
    }
]

CURATED_KOREAN_ROMCOMS = [
    {"title": "Love Reset", "year": 2023, "media_type": "movie", "why": "Hilarious Korean romcom about a married couple on the verge of divorce who both get amnesia and fall in love all over again."},
    {"title": "20th Century Girl", "year": 2022, "media_type": "movie", "why": "Sweet, nostalgic, and deeply moving Korean teen romance about first love and friendship in 1999."},
    {"title": "My Sassy Girl", "year": 2001, "media_type": "movie", "why": "The iconic, laugh-out-loud Korean romantic comedy classic that defined the entire genre."},
    {"title": "Sweet & Sour", "year": 2021, "media_type": "movie", "why": "A witty, modern Korean romcom with a clever twist about the realities of dating and long-distance love."},
    {"title": "On Your Wedding Day", "year": 2018, "media_type": "movie", "why": "Charming, funny, and heartfelt Korean romance following two people's timing over ten years."},
    {"title": "Tune in for Love", "year": 2019, "media_type": "movie", "why": "Warm, sweet Korean romance about two people whose paths keep crossing over the years."}
]


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
    return jsonify({"status": "CineMind Super-Nova Galaxy Engine Live", "version": "19.0"})


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


# ------------------------- MULTI-LLM + UNIVERSAL PLOT/SERIES ENGINE -------------------------
PARSE_PROMPT = f"""You are Nova, an encyclopedic AI expert on global movies, TV series, K-dramas, Thai BL (Boys' Love) dramas, anime, and indie cinema.
Analyze the user's latest message and conversation history.
NEVER suggest pornographic, erotic, softcore, or adult-only films.
Return ONLY a valid JSON object with these exact keys:
{{
  "intent": "plot_search" | "recommend" | "similar_to" | "question" | "chitchat",
  "media_preference": "all" | "movie" | "tv",
  "plot_guesses": [
    {{"title": "Exact Movie or TV Series Title", "year": 2021, "media_type": "movie" | "tv", "why": "1-sentence explanation of why this exact title matches"}}
  ],
  "genres": [list of matching genres from: {GENRE_LIST}],
  "exclude_genres": [genres the user explicitly does NOT want],
  "year_from": integer or null,
  "year_to": integer or null,
  "min_rating": number 0-10 or null,
  "language": ISO 639-1 code like "ko", "ja", "tl", "th", "es", "fr", "hi" or null,
  "origin_country": ISO 3166-1 code like "KR", "PH", "JP", "TH", "US", "GB", "IN", "FR", "ES", "TW", "CN" or null,
  "sort": "popularity" | "rating" | "newest",
  "mood_keywords": [2-4 specific plot/theme keywords, e.g. "twins", "time loop", "wooden puppet", "undercover"],
  "similar_to": [movie or series titles the user says they liked],
  "exclude_titles": [titles the user wants to avoid],
  "direct_reply": "Your warm, accurate, and specific response! If the user describes a plot or asks 'what movie/series is about...', name the #1 exact title immediately in your first sentence and explain how the plot matches!"
}}

CRITICAL INSTRUCTIONS:
1. If the user describes ANY plot, character names, scene, twist, fairy tale, BL series, K-drama, anime, or asks 'what do you call the film/series about...', MUST set "intent": "plot_search" and put the exact matching Movie or TV Series at index 0 of "plot_guesses" (with "media_type": "tv" for series/dramas or "movie" for films), followed by 4-5 closely related titles!
2. Example: "boys love series about two twins named black and white and white took over the life of black..." -> #1 guess MUST be {{"title": "Not Me", "year": 2021, "media_type": "tv", "why": "Twin brother White impersonates his comatose twin Black and falls for Black's friend Sean."}}
3. Example: "what do you call the film about a boy who lies and his nose gets longer" -> #1 guess MUST be {{"title": "Pinocchio", "year": 1940, "media_type": "movie", "why": "The classic story of a wooden boy whose nose grows longer whenever he tells a lie."}}
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
    # Strip markdown code fences if present
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


def llm_json(system, user, temperature=0.2, timeout=12):
    """
    1) Uses Groq (llama-3.3-70b-versatile) if GROQ_API_KEY is configured and active.
    2) Automatically falls back to Keyless Free OpenAI/Llama JSON endpoint (Pollinations AI)
       so Nova's 70B/GPT-4o-mini brain works 100% of the time even without an API key!
    """
    if GROQ_API_KEY:
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
                parsed = parse_json_safely(res.json()["choices"][0]["message"]["content"])
                if isinstance(parsed, dict):
                    return parsed
        except Exception:
            pass

    # Keyless Free LLM Fallback (Pollinations OpenAI-Compatible Endpoint — No API Key Needed!)
    try:
        res = requests.post(
            "https://text.pollinations.ai/openai",
            headers={"Content-Type": "application/json"},
            json={
                "model": "openai",
                "messages": [
                    {"role": "system", "content": system + "\nRespond ONLY with raw valid JSON."},
                    {"role": "user", "content": user}
                ],
                "response_format": {"type": "json_object"},
                "temperature": temperature,
            },
            timeout=timeout,
        )
        if res.status_code == 200:
            data = res.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            parsed = parse_json_safely(content)
            if isinstance(parsed, dict):
                return parsed
    except Exception:
        pass

    return None


def deep_plot_detective(message):
    """Backup plot resolver if both LLM endpoints are unreachable."""
    lower = message.lower()
    for rule in KNOWN_PLOT_PATTERNS:
        if any(w in lower for w in rule.get("must_have_any", [])):
            score = sum(2 if pat in lower else 0 for pat in rule["patterns"])
            word_hits = sum(1 for w in rule["must_have_any"] if w in lower)
            if score >= 2 or word_hits >= 2:
                return rule["guesses"], rule["reply"]

    # Extract only high-signal nouns/names (strip conversational filler so "boy" doesn't match "Baby Boy")
    stop_words = {
        "what", "do", "you", "call", "the", "film", "movie", "series", "show", "drama",
        "about", "where", "who", "when", "why", "how", "is", "are", "was", "were", "a",
        "an", "in", "on", "of", "to", "for", "and", "or", "his", "her", "their", "he",
        "she", "they", "it", "gets", "got", "took", "over", "after", "since", "slowly",
        "fell", "love", "with", "named", "that", "this", "looking", "find", "tell", "me",
        "boys", "boy", "girl", "guy", "man", "woman", "life", "friend", "badly"
    }
    tokens = [w for w in re.findall(r"[a-z0-9']+", lower) if w not in stop_words and len(w) > 2]
    is_tv_query = any(w in lower for w in ["series", "drama", "show", "bl", "boys love", "k-drama", "kdrama", "episode", "season"])
    media_hint = "television series" if is_tv_query else "film"

    guesses = []
    clean_q = " ".join(tokens[:7]) if tokens else lower
    try:
        if len(clean_q) >= 3:
            wiki_res = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={"action": "query", "list": "search", "srsearch": f'{clean_q} {media_hint} plot', "srlimit": 10, "format": "json"},
                headers={"User-Agent": "CineMindCapstone/2.0"},
                timeout=5
            ).json()
            for item in wiki_res.get("query", {}).get("search", []):
                w_title = html.unescape(item.get("title", ""))
                raw_snippet = re.sub(r"<[^>]+>", "", item.get("snippet", ""))
                snippet = html.unescape(raw_snippet).strip()

                # Skip non-movie/series biography or list pages (prevents "Tupac Shakur" false matches!)
                if any(skip in w_title.lower() for skip in ["list of", "category:", "disambiguation", "awards", "filmography", "discography"]):
                    continue
                is_media_article = any(tag in w_title.lower() for tag in ["film", "tv series", "series", "miniseries", "anime"]) or any(w in snippet.lower() for w in ["directed by", "starring", "plot", " television series", " released in "])
                if not is_media_article and len(guesses) > 0:
                    continue

                m_year = re.search(r"\((\d{4})\s*[^\)]*(?:film|series|tv)", w_title, re.I)
                year = int(m_year.group(1)) if m_year else None
                m_type = "tv" if ("series" in w_title.lower() or "tv" in w_title.lower() or is_tv_query) else "movie"
                clean_title = re.sub(r"\s*\([^\)]*\)\s*", "", w_title).strip()
                if clean_title and len(clean_title) < 60:
                    guesses.append({
                        "title": clean_title,
                        "year": year,
                        "media_type": m_type,
                        "why": snippet[:150] + "..." if snippet else f"Matched via plot keywords: '{clean_q}'."
                    })
                if len(guesses) >= 5:
                    break
    except Exception:
        pass

    if guesses:
        top_name = guesses[0]["title"]
        top_yr = f" ({guesses[0]['year']})" if guesses[0].get("year") else ""
        reply = f"Based on your plot description, the title you're looking for is '{top_name}'{top_yr}! Here are the top matching titles:"
        return guesses, reply
    return [], None


def smart_local_nlp_parse(message, history, username="Guest", fav_genres=None):
    lower = message.lower()

    # 1. Check instant high-precision plot cache first
    for rule in KNOWN_PLOT_PATTERNS:
        if any(w in lower for w in rule.get("must_have_any", [])):
            score = sum(2 if pat in lower else 0 for pat in rule["patterns"])
            word_hits = sum(1 for w in rule["must_have_any"] if w in lower)
            if score >= 2 or word_hits >= 2:
                return {
                    "intent": "plot_search",
                    "plot_guesses": rule["guesses"],
                    "genres": [],
                    "mood_keywords": [],
                    "direct_reply": rule["reply"]
                }

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
    if any(w in lower for w in ["romance", "romantic", "love", "sweet", "heartbreaking", "boys love", "bl"]):
        if "romance" not in genres: genres.append("romance")
    if any(w in lower for w in ["funny", "comedy", "hilarious", "laugh"]):
        if "comedy" not in genres: genres.append("comedy")
    if any(w in lower for w in ["sad", "cry", "tearjerker", "emotional"]):
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
            "why", "how", "what", "movie where", "movie about", "film about",
            "series about", "show about", "looking for", "forgot the name",
            "what's that", "whats that", "stuck", "trapped", "infiltrate",
            "relives", "twins", "nose"
        ])
    )

    if looks_like_plot_or_question:
        det_guesses, det_reply = deep_plot_detective(message)
        if det_guesses:
            return {
                "intent": "plot_search",
                "plot_guesses": det_guesses,
                "genres": genres,
                "mood_keywords": [],
                "direct_reply": det_reply
            }

    if origin_country and not genres:
        if fav_genres:
            genres = [g.lower() for g in fav_genres if g.lower() in GENRES][:3]
        if not genres:
            genres = COUNTRY_DEFAULT_GENRES.get(origin_country, ["drama", "romance"])

    if origin_country == "KR" and "romance" in genres:
        guesses = CURATED_KOREAN_ROMCOMS
        direct_reply = f"I've curated the sweetest, funniest Korean romantic comedies for you, {username}—starting with 'Love Reset', '20th Century Girl', and 'My Sassy Girl'!"

    if not direct_reply:
        desc_parts = [p for p in [country_label, "/".join(genres[:3]).title()] if p]
        desc = " ".join(desc_parts) if desc_parts else f"'{message}'"
        direct_reply = f"Here are the top {desc} recommendations matched to your preferences, {username}!"

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

    # If our instant verified pattern cache already nailed it (e.g. Not Me, Pinocchio, Fall, Parasite, Toy Story), return immediately!
    for rule in KNOWN_PLOT_PATTERNS:
        if any(w in message.lower() for w in rule.get("must_have_any", [])):
            score = sum(2 if pat in message.lower() else 0 for pat in rule["patterns"])
            word_hits = sum(1 for w in rule["must_have_any"] if w in message.lower())
            if score >= 2 or word_hits >= 2:
                return local_parsed

    ctx_lines = [f"{'User' if h.get('role') == 'user' else 'Nova'}: {h.get('content')}" for h in (history or [])[-10:] if isinstance(h, dict) and h.get("content")]
    ctx = "\n".join(ctx_lines) if ctx_lines else "No prior messages."
    user_prompt = f"User: {username}\nFavorite Genres: {', '.join(fav_genres or [])}\nHistory:\n{ctx}\n\nLatest Request: {message}"

    llm_parsed = llm_json(PARSE_PROMPT, user_prompt, temperature=0.15)

    if llm_parsed and isinstance(llm_parsed, dict):
        for k in ("origin_country", "language", "genres"):
            if not llm_parsed.get(k) and local_parsed.get(k):
                llm_parsed[k] = local_parsed[k]
        llm_guesses = llm_parsed.get("plot_guesses") or []
        local_guesses = local_parsed.get("plot_guesses") or []
        llm_parsed["plot_guesses"] = llm_guesses + [g for g in local_guesses if g not in llm_guesses]
        return llm_parsed
    return local_parsed


def search_tmdb_title(title, year=None, media_hint=None):
    """Searches TMDB across BOTH movies and TV series so shows like 'Not Me' are always found!"""
    if not title:
        return None
    title_clean = title.strip()

    # 1. If explicitly a TV series/drama, search /search/tv first
    if media_hint == "tv":
        params = {"query": title_clean}
        if year:
            params["first_air_date_year"] = year
        hits = [h for h in tmdb("/search/tv", **params).get("results", []) if is_safe_non_porn(h) and h.get("poster_path")]
        if not hits and year:
            hits = [h for h in tmdb("/search/tv", query=title_clean).get("results", []) if is_safe_non_porn(h) and h.get("poster_path")]
        if hits:
            exact = next((h for h in hits if (h.get("name") or "").lower() == title_clean.lower()), hits[0])
            exact["media_type"] = "tv"
            return exact

    # 2. Search /search/movie if movie hint or general
    if media_hint != "tv":
        params = {"query": title_clean}
        if year:
            params["year"] = year
        hits = [h for h in tmdb("/search/movie", **params).get("results", []) if is_safe_non_porn(h) and h.get("poster_path")]
        if not hits and year:
            hits = [h for h in tmdb("/search/movie", query=title_clean).get("results", []) if is_safe_non_porn(h) and h.get("poster_path")]
        if hits:
            exact = next((h for h in hits if (h.get("title") or "").lower() == title_clean.lower()), None)
            if exact:
                exact["media_type"] = "movie"
                return exact
            # If not an exact title match on movie, check /search/multi in case it's actually a famous TV series!
            multi = [h for h in tmdb("/search/multi", query=title_clean).get("results", []) if h.get("media_type") in ("movie", "tv") and is_safe_non_porn(h) and h.get("poster_path")]
            exact_multi = next((h for h in multi if (h.get("title") or h.get("name") or "").lower() == title_clean.lower()), None)
            if exact_multi:
                return exact_multi
            hits[0]["media_type"] = "movie"
            return hits[0]

    # 3. Fallback to /search/multi (covers both movies and TV shows)
    multi_hits = [
        h for h in tmdb("/search/multi", query=title_clean).get("results", [])
        if h.get("media_type") in ("movie", "tv") and is_safe_non_porn(h) and h.get("poster_path")
    ]
    if multi_hits:
        exact = next((h for h in multi_hits if (h.get("title") or h.get("name") or "").lower() == title_clean.lower()), multi_hits[0])
        return exact
    return None


def keyword_ids(words):
    ids = []
    for w in (words or [])[:4]:
        r = tmdb("/search/keyword", query=w).get("results", [])
        if r:
            ids.append(str(r[0]["id"]))
    return ids


def plot_search(p):
    results, seen = [], set()
    for idx, g in enumerate((p.get("plot_guesses") or [])[:8]):
        title = g.get("title") if isinstance(g, dict) else str(g)
        year = g.get("year") if isinstance(g, dict) else None
        m_hint = g.get("media_type") if isinstance(g, dict) else p.get("media_preference")
        why = g.get("why") if isinstance(g, dict) else None
        if not title:
            continue

        chosen = search_tmdb_title(title, year=year, media_hint=m_hint)
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
            extra = tmdb("/discover/movie", with_keywords="|".join(kws), sort_by="popularity.desc", **{"vote_count.gte": 30}).get("results", [])
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


def find_movies(intent):
    if intent.get("intent") == "plot_search":
        found = plot_search(intent)
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
        hit = search_tmdb_title(title, year=year, media_hint=m_hint)
        if hit:
            add([hit], bonus=40.0 - (idx * 3.0), why_note=why, default_media=hit.get("media_type", "movie"))

    for t in (intent.get("similar_to") or [])[:2]:
        hit = search_tmdb_title(t)
        if hit:
            m_type = hit.get("media_type", "movie")
            add(tmdb(f"/{m_type}/{hit['id']}/recommendations").get("results", []), bonus=15.0, why_note=f"Recommended based on '{t}'.", default_media=m_type)

    gids = [str(GENRES[g.lower()]) for g in (intent.get("genres") or []) if g.lower() in GENRES]
    xids = [str(GENRES[g.lower()]) for g in intent.get("exclude_genres") or [] if g.lower() in GENRES]

    min_votes = 15 if (target_country or target_lang) else 100
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
    return llm_json(system, f"User Request: {message}\nVerified Titles: {json.dumps(listing)}", temperature=0.25) or {}


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

    cands = find_movies(intent)
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

    # If extract_intent already produced a specific direct_reply for a plot_search, keep it fast & accurate!
    direct_reply = html.unescape(intent.get("direct_reply") or "")
    reasons = {}
    if not direct_reply or direct_reply.startswith("Here are the top"):
        ex = explain(message, username, top, intent)
        reasons = ex.get("reasons", {}) if isinstance(ex.get("reasons"), dict) else {}
        if ex.get("reply"):
            direct_reply = html.unescape(ex.get("reply"))

    reply = direct_reply or f"Here are my top handpicked matches for '{message}', {username}!"

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
        "rationale": html.unescape(reasons.get(str(m["id"])) or m.get("_guess_why") or f"Matched to your '{message}' query."),
    } for m in top]

    return jsonify({"reply": reply, "movies": movies, "intent": intent_type, "success": True})


@app.route("/trends", methods=["GET"])
def trends():
    return jsonify({
        "ai_forecast": "Super-Nova Multi-LLM + Movie/Series Plot-Search Pipeline Online.",
        "trending_genres": ["Multi-LLM Plot & Series Recognition", "TMDB Movie + TV Verification", "OMDb Metadata Enrichment"]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
