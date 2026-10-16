import os
import re
import json
import sqlite3
import hashlib

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
    10759: "Action & Adventure", 10762: "Kids", 10765: "Sci-Fi & Fantasy", 10768: "War & Politics"
}

SPECIAL_CATEGORIES = ["bl", "boys love", "girls love", "gl", "anime", "kids", "sports", "documentary"]
GENRE_LIST = ", ".join(list(GENRES.keys()) + SPECIAL_CATEGORIES)

COUNTRY_DEFAULT_GENRES = {
    "PH": ["drama", "romance", "comedy", "horror"],
    "KR": ["drama", "thriller", "romance", "action"],
    "TH": ["horror", "romance", "action", "comedy"],
    "JP": ["animation", "fantasy", "sci-fi", "drama"],
    "CN": ["drama", "fantasy", "action", "animation"],
    "TW": ["romance", "drama", "comedy"],
    "IN": ["action", "drama", "romance", "comedy"],
    "ES": ["thriller", "crime", "drama"],
    "FR": ["drama", "romance", "comedy"],
    "GB": ["drama", "crime", "mystery"],
    "US": ["action", "sci-fi", "comedy", "drama"]
}

PORN_BLOCK_WORDS = [
    "porn", "porno", "pornographic", "xxx", "erotic", "erotica", "hentai", "jav",
    "av idol", "sex tape", "playboy", "penthouse", "stripper", "prostitute",
    "brothel", "bdsm", "fetish", "orgasm", "milf", "softcore", "pink film",
    "vivamax", "brazzers", "onlyfans", "nymphomaniac", "365 days", "fifty shades",
    "scorpio nights", "silip", "uhaw", "laman", "pamasahe", "selina's gold",
    "us x her", "bela luna", "kiskisan", "salitan", "lampas langit", "virgin forest",
    "kaliwaan", "purgatoryo", "doblado", "paupahan", "boy bastos", "palitan",
    "tag-init", "sugar baby", "tayuan", "haslers", "dilig", "kaluskos"
]

KNOWN_R18_TITLES = {
    "deadpool", "deadpool 2", "deadpool & wolverine", "logan", "joker", "parasite",
    "oldboy", "oppenheimer", "john wick", "saw", "hereditary", "midsommar",
    "the wolf of wall street", "pulp fiction", "fight club", "gone girl",
    "shutter island", "se7en", "american psycho", "saltburn", "the handmaiden",
    "squid game", "the boys", "euphoria", "game of thrones", "breaking bad",
    "dexter", "monster: the jeffrey dahmer story"
}

# Curated High-Precision Lists for BL, GL, Real-Life Sports, and Documentaries
CURATED_SPECIAL_CATALOG = {
    "BL": [
        {"title": "KinnPorsche", "media_type": "tv", "year": 2022, "why": "Hit Thai Boys' Love action-romance drama."},
        {"title": "2gether: The Series", "media_type": "tv", "year": 2020, "why": "Iconic Thai Boys' Love campus romance series."},
        {"title": "Bad Buddy", "media_type": "tv", "year": 2021, "why": "Beloved Thai Boys' Love enemies-to-lovers series."},
        {"title": "Semantic Error", "media_type": "tv", "year": 2022, "why": "Acclaimed Korean Boys' Love campus romance."},
        {"title": "Cherry Magic! Thirty Years of Virginity Can Make You a Wizard?!", "media_type": "tv", "year": 2020, "why": "Heartwarming Japanese Boys' Love romantic comedy."},
        {"title": "The Eighth Sense", "media_type": "tv", "year": 2023, "why": "Emotional Korean Boys' Love drama."},
        {"title": "I Told Sunset About You", "media_type": "tv", "year": 2020, "why": "Critically acclaimed coming-of-age Thai BL drama."},
        {"title": "Moonlight Chicken", "media_type": "tv", "year": 2023, "why": "Award-winning Thai Boys' Love series."},
        {"title": "Last Twilight", "media_type": "tv", "year": 2023, "why": "Deeply moving Thai BL romance series."},
        {"title": "Young Royals", "media_type": "tv", "year": 2021, "why": "Hit Boys' Love royal boarding school drama."},
        {"title": "Heartstopper", "media_type": "tv", "year": 2022, "why": "Sweet Boys' Love teen romance series."},
        {"title": "Red, White & Royal Blue", "media_type": "movie", "year": 2023, "why": "Popular Boys' Love romantic comedy film."},
        {"title": "Your Name Engraved Herein", "media_type": "movie", "year": 2020, "why": "Landmark Taiwanese Boys' Love romantic drama."}
    ],
    "GL": [
        {"title": "GAP The Series", "media_type": "tv", "year": 2022, "why": "Phenomenal Thai Girls' Love office romance series."},
        {"title": "The Secret of Us", "media_type": "tv", "year": 2024, "why": "Hit Thai Girls' Love romantic drama starring LingOrm."},
        {"title": "23.5", "media_type": "tv", "year": 2024, "why": "Sweet Thai Girls' Love high school rom-com."},
        {"title": "Pluto", "media_type": "tv", "year": 2024, "why": "Emotional Thai Girls' Love mystery-romance series."},
        {"title": "Blank The Series", "media_type": "tv", "year": 2024, "why": "Popular Thai Girls' Love romance series."},
        {"title": "Affair", "media_type": "tv", "year": 2024, "why": "Trending Thai Girls' Love drama series."},
        {"title": "The Loyal Pin", "media_type": "tv", "year": 2024, "why": "Period Thai Girls' Love romance starring FreenBecky."},
        {"title": "Uranus 2324", "media_type": "movie", "year": 2024, "why": "Sci-Fi Thai Girls' Love movie starring Freen & Becky."},
        {"title": "The Handmaiden", "media_type": "movie", "year": 2016, "why": "Acclaimed Korean Girls' Love psychological thriller."},
        {"title": "Portrait of a Lady on Fire", "media_type": "movie", "year": 2019, "why": "Masterpiece Girls' Love historical romance."},
        {"title": "Carol", "media_type": "movie", "year": 2015, "why": "Classic Girls' Love romantic drama."},
        {"title": "Bottoms", "media_type": "movie", "year": 2023, "why": "Hilarious queer Girls' Love comedy."}
    ],
    "SPORTS": [
        {"title": "FIFA Uncovered", "media_type": "tv", "year": 2022, "why": "Real-life FIFA world football documentary series."},
        {"title": "Formula 1: Drive to Survive", "media_type": "tv", "year": 2019, "why": "Real-life Formula 1 championship racing series."},
        {"title": "The Last Dance", "media_type": "tv", "year": 2020, "why": "Iconic NBA basketball championship documentary series."},
        {"title": "Beckham", "media_type": "tv", "year": 2023, "why": "Real-life football legend David Beckham series."},
        {"title": "WWE Raw", "media_type": "tv", "year": 1993, "why": "Live-action professional wrestling flagship show."},
        {"title": "Mr. McMahon", "media_type": "tv", "year": 2024, "why": "Real-life WWE wrestling history docuseries."},
        {"title": "Sprint", "media_type": "tv", "year": 2024, "why": "Real-life track & field world championship series."},
        {"title": "Quarterback", "media_type": "tv", "year": 2023, "why": "Real-life NFL football series."},
        {"title": "Rush", "media_type": "movie", "year": 2013, "why": "Live-action Formula 1 racing biographical drama."},
        {"title": "Ford v Ferrari", "media_type": "movie", "year": 2019, "why": "Live-action Le Mans championship racing drama."},
        {"title": "Creed", "media_type": "movie", "year": 2015, "why": "Hard-hitting live-action championship boxing film."},
        {"title": "King Richard", "media_type": "movie", "year": 2021, "why": "True story of tennis legends Venus and Serena Williams."},
        {"title": "Moneyball", "media_type": "movie", "year": 2011, "why": "True-story Major League Baseball drama."},
        {"title": "The Iron Claw", "media_type": "movie", "year": 2023, "why": "True-story professional wrestling drama."}
    ],
    "DOC": [
        {"title": "Conversations with a Killer: The Jeffrey Dahmer Tapes", "media_type": "tv", "year": 2022, "why": "True-crime documentary series examining Jeffrey Dahmer."},
        {"title": "Monster: The Jeffrey Dahmer Story", "media_type": "tv", "year": 2022, "why": "Biographical true-crime series on Jeffrey Dahmer."},
        {"title": "Night Stalker: The Hunt for a Serial Killer", "media_type": "tv", "year": 2021, "why": "Gripping true-crime documentary series."},
        {"title": "Don't F**k with Cats: Hunting an Internet Killer", "media_type": "tv", "year": 2019, "why": "Investigative true-crime documentary series."},
        {"title": "Making a Murderer", "media_type": "tv", "year": 2015, "why": "Landmark true-crime documentary series."},
        {"title": "American Nightmare", "media_type": "tv", "year": 2024, "why": "True-crime investigative documentary series."},
        {"title": "The Tinder Swindler", "media_type": "movie", "year": 2022, "why": "Hit true-crime investigative documentary."},
        {"title": "American Murder: The Family Next Door", "media_type": "movie", "year": 2020, "why": "True-crime documentary film."},
        {"title": "Girl in the Picture", "media_type": "movie", "year": 2022, "why": "Acclaimed true-crime mystery documentary."},
        {"title": "Our Planet", "media_type": "tv", "year": 2019, "why": "Landmark nature documentary series."},
        {"title": "13th", "media_type": "movie", "year": 2016, "why": "Oscar-nominated historical documentary."}
    ]
}

KNOWN_PLOT_PATTERNS = [
    {
        "patterns": ["boxing in toy story", "toy story boxing", "why is there boxing in toy story", "rock em sock em", "rock 'em sock 'em"],
        "must_have_any": ["toy story", "boxing"],
        "reply": "In the Toy Story franchise (especially Toy Story 2), there is a memorable boxing scene featuring the classic 'Rock 'Em Sock 'Em Robots' (the Red Rocker and Blue Bomber) inside Al's Toy Barn! Plus, 'Real Steel' (2011) is the famous robot-boxing movie many people associate with fighting robots.",
        "guesses": [
            {"title": "Toy Story", "year": 1995, "media_type": "movie", "why": "The original Pixar classic introducing Woody, Buzz Lightyear, and Andy's bedroom toys."},
            {"title": "Toy Story 2", "year": 1999, "media_type": "movie", "why": "Features the famous Rock 'Em Sock 'Em Robots boxing match scene inside Al's office!"},
            {"title": "Toy Story 3", "year": 2010, "media_type": "movie", "why": "Woody, Buzz, and the gang face Sunnyside Daycare as Andy prepares for college."},
            {"title": "Toy Story 4", "year": 2019, "media_type": "movie", "why": "Woody and Buzz embark on a road trip with Forky and Duke Caboom."},
            {"title": "Real Steel", "year": 2011, "media_type": "movie", "why": "The hit robot-boxing movie often associated with fighting toy robots."}
        ]
    },
    {
        "patterns": ["high pole", "tv tower", "radio tower", "two girls", "2 girls", "stuck on top", "climbs a tower", "2000 feet", "ladder breaks", "stuck on a tower", "tall tower", "tall pole"],
        "must_have_any": ["pole", "tower", "stuck", "climb", "high", "top"],
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
    {"title": "Business Proposal", "year": 2022, "media_type": "tv", "why": "Super funny and sweet Korean rom-com series about a blind date with the company CEO."},
    {"title": "Lovely Runner", "year": 2024, "media_type": "tv", "why": "Heart-fluttering Korean time-slip romantic comedy series."},
    {"title": "King the Land", "year": 2023, "media_type": "tv", "why": "Charming, sweet Korean romantic comedy series."}
]


def is_safe_non_porn(m):
    if not m:
        return False
    if m.get("adult") is True:
        return False
    text = f"{m.get('title') or ''} {m.get('name') or ''} {m.get('original_title') or ''} {m.get('overview') or ''}".lower()
    for bad in PORN_BLOCK_WORDS:
        if bad in text:
            return False
    return True


def is_animated_or_cartoon(m):
    if not m:
        return False
    gids = m.get("genre_ids") or [g.get("id") for g in (m.get("genres") or []) if isinstance(g, dict)]
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
    if any(g in gids for g in (27, 80, 53, 99)) and re.search(
        r"\b(murder|serial killer|brutal|blood|gore|cartel|massacre|psychopath|torture|slasher|cannibal|dahmer)\b",
        f"{title_l} {overview}"
    ):
        return True
    return False


def format_exact_genres(m, custom_badge=None):
    names = []
    if custom_badge:
        names.append(custom_badge)
    for g in (m.get("genres") or []):
        if isinstance(g, dict) and g.get("name") and g["name"] not in names:
            names.append(g["name"])
    for gid in (m.get("genre_ids") or []):
        label = GENRE_ID_TO_NAME.get(int(gid))
        if label and label not in names:
            names.append(label)
    lang = (m.get("original_language") or "").lower()
    if "Animation" in names and lang in ("ja", "ko", "zh") and "Anime" not in names:
        names.insert(0, "Anime")
    return names[:4] if names else ["Drama"]


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, genres TEXT DEFAULT '[]')''')
    try:
        c.execute("ALTER TABLE users ADD COLUMN genres TEXT DEFAULT '[]'")
    except Exception:
        pass
    c.execute('''CREATE TABLE IF NOT EXISTS watchlist (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, movie_id INTEGER NOT NULL, title TEXT NOT NULL, poster TEXT, vote_average REAL, media_type TEXT DEFAULT 'movie', UNIQUE(username, movie_id))''')
    try:
        c.execute("ALTER TABLE watchlist ADD COLUMN media_type TEXT DEFAULT 'movie'")
    except Exception:
        pass
    c.execute('''CREATE TABLE IF NOT EXISTS favorites (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, movie_id INTEGER NOT NULL, title TEXT NOT NULL, poster TEXT, vote_average REAL, media_type TEXT DEFAULT 'movie', UNIQUE(username, movie_id))''')
    try:
        c.execute("ALTER TABLE favorites ADD COLUMN media_type TEXT DEFAULT 'movie'")
    except Exception:
        pass
    c.execute('''CREATE TABLE IF NOT EXISTS not_interested (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, movie_id INTEGER NOT NULL, title TEXT NOT NULL, keywords TEXT DEFAULT '[]', UNIQUE(username, movie_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS interactions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, movie_id INTEGER NOT NULL, title TEXT NOT NULL, action TEXT NOT NULL, vote_average REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "CineMind Super-Nova Galaxy Engine Live", "version": "18.0"})


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
        return jsonify({"watchlist": [], "favorites": [], "not_interested": [], "genres": []})
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT movie_id, title, poster, vote_average, media_type FROM watchlist WHERE username = ?", (username,))
    watchlist = [{"id": r[0], "title": r[1], "poster": r[2], "vote_average": r[3], "media_type": r[4] or "movie"} for r in c.fetchall()]
    c.execute("SELECT movie_id, title, poster, vote_average, media_type FROM favorites WHERE username = ?", (username,))
    favorites = [{"id": r[0], "title": r[1], "poster": r[2], "vote_average": r[3], "media_type": r[4] or "movie"} for r in c.fetchall()]
    c.execute("SELECT movie_id, title, keywords FROM not_interested WHERE username = ?", (username,))
    not_interested = [{"id": r[0], "title": r[1], "keywords": json.loads(r[2] or "[]")} for r in c.fetchall()]
    c.execute("SELECT genres FROM users WHERE username = ?", (username,))
    g_row = c.fetchone()
    conn.close()
    saved_genres = []
    if g_row and g_row[0]:
        try:
            saved_genres = json.loads(g_row[0])
        except Exception:
            pass
    return jsonify({"watchlist": watchlist, "favorites": favorites, "not_interested": not_interested, "genres": saved_genres})


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
    media_type = movie.get("media_type", "movie")
    table = "watchlist" if lib_type == "watchlist" else "favorites"
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(f"SELECT id FROM {table} WHERE username = ? AND movie_id = ?", (username, movie_id))
    if c.fetchone():
        c.execute(f"DELETE FROM {table} WHERE username = ? AND movie_id = ?", (username, movie_id))
        action = "removed"
    else:
        c.execute(f"INSERT OR REPLACE INTO {table} (username, movie_id, title, poster, vote_average, media_type) VALUES (?, ?, ?, ?, ?, ?)",
                  (username, movie_id, title, poster, vote_average, media_type))
        action = "added"
        c.execute("INSERT INTO interactions (username, movie_id, title, action, vote_average) VALUES (?, ?, ?, ?, ?)",
                  (username, movie_id, title, 'like' if lib_type == 'favorites' else 'watched', vote_average))
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
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO not_interested (username, movie_id, title, keywords) VALUES (?, ?, ?, ?)",
        (username, movie_id, title, json.dumps(keywords))
    )
    c.execute(
        "INSERT INTO interactions (username, movie_id, title, action, vote_average) VALUES (?, ?, ?, 'not_interested', ?)",
        (username, movie_id, title, movie.get("vote_average", 0.0))
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "action": "hidden"})


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
    c.execute("SELECT COUNT(*) FROM not_interested WHERE username = ?", (username,))
    total_disliked = c.fetchone()[0]
    conn.close()
    rated = [r[1] for r in interactions if r[1]]
    avg_rating = sum(rated) / len(rated) if rated else 0.0
    return jsonify({
        "username": username or "Guest",
        "total_recommendations_viewed": len(interactions),
        "total_liked": total_liked,
        "total_watchlist": total_watchlist,
        "total_not_interested": total_disliked,
        "average_rating_of_interest": round(avg_rating, 2),
        "dominant_mood": "Multi-API Neural Match",
        "genre_distribution": {"Drama": 30, "Sci-Fi": 22, "BL / GL": 18, "Anime": 15, "Docs & Sports": 15}
    })


@app.route("/api/omdb", methods=["GET"])
def omdb_info():
    title = request.args.get("title", "")
    year = request.args.get("year", "")
    if not OMDB_API_KEY or not title:
        return jsonify({})
    try:
        o = requests.get(
            "https://www.omdbapi.com/",
            params={"apikey": OMDB_API_KEY, "t": title, "y": year},
            timeout=4
        ).json()
        if o.get("Response") == "True":
            return jsonify({
                "imdbRating": o.get("imdbRating"),
                "runtime": o.get("Runtime"),
                "director": o.get("Director"),
                "writer": o.get("Writer"),
                "actors": o.get("Actors"),
                "genre": o.get("Genre"),
                "awards": o.get("Awards")
            })
    except Exception:
        pass
    return jsonify({})


@app.route("/api/credits", methods=["GET"])
def movie_credits():
    movie_id = request.args.get("id")
    media_type = "tv" if request.args.get("media_type") == "tv" else "movie"
    if not movie_id:
        return jsonify({})
    d = tmdb(f"/{media_type}/{movie_id}", append_to_response="credits,keywords")
    if not d:
        return jsonify({})
    credits = d.get("credits") or {}
    cast = [
        {"name": c.get("name"), "character": c.get("character") or "Lead Role"}
        for c in (credits.get("cast") or [])[:12] if c.get("name")
    ]
    crew_list = credits.get("crew") or []
    directors = [c.get("name") for c in crew_list if c.get("job") == "Director"]
    if not directors and d.get("created_by"):
        directors = [c.get("name") for c in d.get("created_by") if c.get("name")]
    writers = list({
        c.get("name") for c in crew_list
        if c.get("job") in ("Writer", "Screenplay", "Story", "Creator") or c.get("department") == "Writing"
    })[:4]
    producers = [
        f"{c.get('name')} ({c.get('job')})" for c in crew_list
        if c.get("job") in ("Producer", "Executive Producer", "Original Music Composer", "Director of Photography")
    ][:4]
    genres = [g.get("name") for g in (d.get("genres") or []) if g.get("name")]
    return jsonify({
        "id": d.get("id"),
        "genres": genres,
        "directors": directors[:3],
        "writers": writers,
        "crew": producers,
        "cast": cast
    })


PARSE_PROMPT = f"""You are Nova, a super-intelligent, warm, and encyclopedic AI cinema & TV series expert.
Analyze the user's latest message along with the conversation history and user profile.
Return ONLY a valid JSON object with these exact keys:
{{
  "intent": "recommend" | "similar_to" | "plot_search" | "chitchat" | "question",
  "special_category": "BL" | "GL" | "SPORTS" | "DOC" | "ANIME" | "KIDS" | null,
  "plot_guesses": [{{"title": "Exact Movie or Series Title", "year": 2022, "media_type": "movie" | "tv", "why": "1-sentence explanation of how this matches"}}],
  "genres": [list of matching genres from: {GENRE_LIST}],
  "exclude_genres": [genres the user explicitly does NOT want],
  "year_from": integer or null,
  "year_to": integer or null,
  "min_rating": number 0-10 or null,
  "language": ISO 639-1 code like "ko", "ja", "tl", "th", "es", "fr", "hi", "zh" or null,
  "origin_country": ISO 3166-1 code like "KR", "PH", "JP", "TH", "US", "GB", "IN", "FR", "ES", "TW", "CN" or null,
  "sort": "popularity" | "rating" | "newest",
  "mood_keywords": [2-4 specific plot/theme keywords],
  "similar_to": [movie or series titles the user says they liked or wants similar to],
  "exclude_titles": [titles the user has already seen or marked Not Interested],
  "direct_reply": "Your natural, witty, intelligent conversational response. Note: For Sports, only recommend real-life live-action sports (like FIFA, WWE, Formula 1, NBA), never cartoons/anime. For Documentaries, only recommend real-life documentaries (like Jeffrey Dahmer)."
}}
"""


def tmdb(path, **params):
    params["api_key"] = TMDB_API_KEY
    params.setdefault("include_adult", "false")
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


def detect_special_category(text=""):
    lower = (text or "").lower()
    if re.search(r"\b(boys love|boy's love|boys' love|bl series|bl drama|thai bl|korean bl|japanese bl|yaoi)\b", lower):
        return "BL"
    if re.search(r"\b(girls love|girl's love|girls' love|gl series|gl drama|thai gl|sapphic|lesbian|freenbecky|lingorm|yuri)\b", lower):
        return "GL"
    if re.search(r"\b(fifa|wwe|formula 1|f1|ufc|nba|nfl|real sports|real life sports|sports documentary|boxing|wrestling|football|basketball)\b", lower) and "toy story" not in lower:
        return "SPORTS"
    if re.search(r"\b(documentary|documentaries|docuseries|true crime|jeffrey dahmer|dahmer|serial killer documentary|tinder swindler|making a murderer)\b", lower):
        return "DOC"
    if re.search(r"\b(anime|japanese animation|korean animation|chinese animation|donghua|shonen|studio ghibli|makoto shinkai)\b", lower):
        return "ANIME"
    if re.search(r"\b(kids|children|family movie|pixar|disney animated|dreamworks|cartoon)\b", lower):
        return "KIDS"
    return None


def deep_plot_detective(message):
    lower = message.lower()
    for rule in KNOWN_PLOT_PATTERNS:
        if any(w in lower for w in rule.get("must_have_any", [])):
            score = sum(2 if pat in lower else 0 for pat in rule["patterns"])
            word_hits = sum(1 for w in rule["must_have_any"] if w in lower)
            if score >= 2 or word_hits >= 2:
                return rule["guesses"], rule["reply"]

    guesses = []
    wiki_snippet_answer = None
    try:
        clean_q = re.sub(
            r"\b(why|how|what|who|when|is|there|in|i am|i'm|looking for a|looking for|what is the|what's that|whats that|movie where|movie about|film where|film about|series where|show where|a|an|the|were|was|from|really)\b",
            " ", lower
        )
        clean_q = re.sub(r"\s+", " ", clean_q).strip()
        if len(clean_q) >= 3:
            wiki_res = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={"action": "query", "list": "search", "srsearch": f'{clean_q} film OR television series', "srlimit": 8, "format": "json"},
                headers={"User-Agent": "CineMindCapstone/1.0"},
                timeout=4
            ).json()
            for item in wiki_res.get("query", {}).get("search", []):
                w_title = item.get("title", "")
                snippet = re.sub(r"<[^>]+>", "", item.get("snippet", "")).strip()
                if any(skip in w_title.lower() for skip in ["list of", "category:", "disambiguation", "awards", "filmography"]):
                    continue
                if not wiki_snippet_answer and snippet:
                    wiki_snippet_answer = snippet
                m_year = re.search(r"\((\d{4})\s*[^\)]*(film|series|TV)\)", w_title, re.I)
                year = int(m_year.group(1)) if m_year else None
                m_type = "tv" if re.search(r"series|TV", w_title, re.I) else "movie"
                clean_title = re.sub(r"\s*\([^\)]*\)\s*", "", w_title).strip()
                if clean_title and len(clean_title) < 65:
                    guesses.append({
                        "title": clean_title,
                        "year": year,
                        "media_type": m_type,
                        "why": snippet[:140] + "..." if snippet else f"Matched to '{clean_q}'."
                    })
                if len(guesses) >= 5:
                    break
    except Exception:
        pass

    if guesses:
        top_name = guesses[0]["title"]
        top_yr = f" ({guesses[0]['year']})" if guesses[0].get("year") else ""
        if wiki_snippet_answer and any(q_word in lower for q_word in ["why", "how", "what", "who", "explain"]):
            reply = f"Regarding '{top_name}'{top_yr}: {wiki_snippet_answer}. Here are the matching titles and related releases:"
        else:
            reply = f"Based on your query, the top match is '{top_name}'{top_yr}! Here are the closest matching titles:"
        return guesses, reply
    return [], None


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

    special_cat = detect_special_category(message)

    country_map = {
        "korean": ("KR", "ko", "South Korean"), "korea": ("KR", "ko", "South Korean"),
        "k-drama": ("KR", "ko", "South Korean"), "kdrama": ("KR", "ko", "South Korean"),
        "japanese": ("JP", "ja", "Japanese"), "japan": ("JP", "ja", "Japanese"),
        "filipino": ("PH", "tl", "Filipino"), "pinoy": ("PH", "tl", "Filipino"),
        "philippine": ("PH", "tl", "Philippine"), "philippines": ("PH", "tl", "Philippine"),
        "tagalog": ("PH", "tl", "Filipino"),
        "thai": ("TH", "th", "Thai"), "thailand": ("TH", "th", "Thai"),
        "taiwanese": ("TW", "zh", "Taiwanese"), "taiwan": ("TW", "zh", "Taiwanese"),
        "chinese": ("CN", "zh", "Chinese"), "china": ("CN", "zh", "Chinese"),
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

    if special_cat in CURATED_SPECIAL_CATALOG:
        guesses = list(CURATED_SPECIAL_CATALOG[special_cat])
        if special_cat == "BL":
            direct_reply = f"Here are the top Boys' Love (BL) series and movies curated for you, {username}—including 'KinnPorsche', 'Bad Buddy', 'Semantic Error', and '2gether'!"
        elif special_cat == "GL":
            direct_reply = f"Here are the top Girls' Love (GL) series and films curated for you, {username}—including 'GAP The Series', 'The Secret of Us', '23.5', and 'Pluto'!"
        elif special_cat == "SPORTS":
            direct_reply = f"Here are real-life, live-action Sports series, documentaries, and films (including FIFA, Formula 1, WWE, and NBA—no cartoons!), {username}:"
        elif special_cat == "DOC":
            direct_reply = f"Here are gripping real-life True-Crime and investigative Documentaries like 'Jeffrey Dahmer', 'Making a Murderer', and 'The Tinder Swindler', {username}:"
        return {
            "intent": "recommend",
            "special_category": special_cat,
            "plot_guesses": guesses,
            "genres": genres,
            "origin_country": origin_country,
            "language": language,
            "mood_keywords": mood_keywords,
            "similar_to": similar_to,
            "direct_reply": direct_reply
        }

    if any(w in lower for w in ["romcom", "rom-com", "romantic comedy"]):
        genres.extend(["romance", "comedy"])
    if any(w in lower for w in ["romance", "romantic", "love", "sweet", "heartbreaking"]):
        if "romance" not in genres:
            genres.append("romance")
    if any(w in lower for w in ["funny", "comedy", "hilarious", "laugh"]):
        if "comedy" not in genres:
            genres.append("comedy")
    if any(w in lower for w in ["sad", "cry", "tearjerker", "emotional"]):
        if "drama" not in genres:
            genres.append("drama")
    if any(w in lower for w in ["sci-fi", "scifi", "science fiction", "space", "future", "alien", "time travel"]):
        if "sci-fi" not in genres:
            genres.append("sci-fi")
    if any(w in lower for w in ["mind-bending", "twist", "psychological", "suspense", "dark", "thriller", "stuck", "trapped", "survival"]):
        if "thriller" not in genres:
            genres.append("thriller")
    if any(w in lower for w in ["scary", "horror", "ghost", "creepy", "haunted"]):
        if "horror" not in genres:
            genres.append("horror")
    if any(w in lower for w in ["action", "explosive", "fight", "blockbuster"]):
        if "action" not in genres:
            genres.append("action")

    for g_name in GENRES.keys():
        if re.search(rf"\b{re.escape(g_name)}\b", lower) and g_name not in genres:
            genres.append(g_name)

    if origin_country and not genres and not special_cat:
        if fav_genres:
            genres = [g.lower() for g in fav_genres if g.lower() in GENRES][:3]
        if not genres:
            genres = COUNTRY_DEFAULT_GENRES.get(origin_country, ["drama", "romance"])

    looks_like_plot_or_question = (
        not origin_country and not special_cat and (
            len(lower.split()) >= 4
            or "?" in lower
            or any(p in lower for p in ["why", "how", "what", "movie where", "movie about", "looking for a movie", "forgot the name", "what's that movie", "stuck", "trapped", "infiltrate", "relives", "boxing"])
        )
    )

    if looks_like_plot_or_question:
        det_guesses, det_reply = deep_plot_detective(message)
        if det_guesses:
            return {
                "intent": "plot_search",
                "special_category": None,
                "plot_guesses": det_guesses,
                "genres": genres,
                "mood_keywords": [],
                "direct_reply": det_reply
            }

    if origin_country == "KR" and "romance" in genres:
        guesses = CURATED_KOREAN_ROMCOMS
        direct_reply = f"I've curated the sweetest, funniest Korean romantic comedies for you, {username}—starting with 'Love Reset', '20th Century Girl', and 'Business Proposal'!"

    if not direct_reply:
        desc_parts = [p for p in [country_label, special_cat or "/".join(genres[:3]).title()] if p]
        desc = " ".join(desc_parts) if desc_parts else f"'{message}'"
        direct_reply = f"Here are the top {desc} recommendations matched to your preferences, {username}!"

    return {
        "intent": "plot_search" if looks_like_plot_or_question else intent,
        "special_category": special_cat,
        "plot_guesses": guesses,
        "genres": genres,
        "origin_country": origin_country,
        "language": language,
        "mood_keywords": mood_keywords,
        "similar_to": similar_to,
        "direct_reply": direct_reply
    }


def extract_intent(message, history, username="Guest", fav_genres=None, selected_country=None, client_guesses=None):
    local_parsed = smart_local_nlp_parse(message, history, username, fav_genres)
    ctx_lines = [
        f"{'User' if h.get('role') == 'user' else 'Nova'}: {h.get('content')}"
        for h in (history or [])[-10:] if isinstance(h, dict) and h.get("content")
    ]
    ctx = "\n".join(ctx_lines) if ctx_lines else "No prior messages."
    user_prompt = f"User: {username}\nFavorite Genres: {', '.join(fav_genres or [])}\nHistory:\n{ctx}\n\nLatest Request: {message}"
    llm_parsed = groq_json(PARSE_PROMPT, user_prompt, temperature=0.2)

    merged = llm_parsed if (llm_parsed and isinstance(llm_parsed, dict)) else local_parsed
    for k in ("origin_country", "language", "genres", "special_category"):
        if not merged.get(k) and local_parsed.get(k):
            merged[k] = local_parsed[k]

    combined_guesses = []
    for g in (local_parsed.get("plot_guesses") or []) + (merged.get("plot_guesses") or []) + (client_guesses or []):
        if isinstance(g, dict) and g.get("title"):
            if not any(existing.get("title", "").lower() == g["title"].lower() for existing in combined_guesses):
                combined_guesses.append(g)
    merged["plot_guesses"] = combined_guesses
    return merged


def search_tmdb_title(title, year=None, preferred_media=None):
    media_order = [preferred_media, "tv" if preferred_media == "movie" else "movie"] if preferred_media in ("movie", "tv") else ["movie", "tv"]
    for m_type in media_order:
        if not m_type:
            continue
        params = {"query": title}
        if year and m_type == "movie":
            params["year"] = year
        hits = tmdb(f"/search/{m_type}", **params).get("results", [])
        if not hits and year:
            hits = tmdb(f"/search/{m_type}", query=title).get("results", [])
        hits = [h for h in hits if is_safe_non_porn(h) and h.get("poster_path")]
        if hits:
            exact = next((h for h in hits if (h.get("title") or h.get("name") or "").lower() == title.lower()), hits[0])
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
    for idx, g in enumerate((p.get("plot_guesses") or [])[:10]):
        title = g.get("title") if isinstance(g, dict) else str(g)
        year = g.get("year") if isinstance(g, dict) else None
        why = g.get("why") if isinstance(g, dict) else None
        m_type = g.get("media_type") if isinstance(g, dict) else None
        if not title:
            continue
        chosen = search_tmdb_title(title, year, m_type)
        if chosen:
            u_key = f"{chosen.get('media_type', 'movie')}_{chosen['id']}"
            if u_key not in seen:
                seen.add(u_key)
                chosen["_bonus"] = 50.0 - (idx * 3.5)
                chosen["_is_guess"] = True
                if why:
                    chosen["_guess_why"] = why
                results.append(chosen)

    if len(results) < 6:
        kws = keyword_ids(p.get("mood_keywords", []))
        if kws:
            extra = tmdb("/discover/movie", with_keywords="|".join(kws), sort_by="popularity.desc", **{"vote_count.gte": 40}).get("results", [])
            for m in extra:
                if is_safe_non_porn(m) and m.get("poster_path"):
                    m["media_type"] = "movie"
                    u_key = f"movie_{m['id']}"
                    if u_key not in seen:
                        seen.add(u_key)
                        m["_bonus"] = 10.0
                        results.append(m)

    if results and len(results) < 8:
        top_item = results[0]
        top_id = top_item["id"]
        top_media = top_item.get("media_type", "movie")
        for m in tmdb(f"/{top_media}/{top_id}/recommendations").get("results", []):
            if is_safe_non_porn(m) and m.get("poster_path"):
                m["media_type"] = top_media
                u_key = f"{top_media}_{m['id']}"
                if u_key not in seen:
                    seen.add(u_key)
                    m["_bonus"] = 8.0
                    m["_guess_why"] = f"Recommended because it shares key themes with {top_item.get('title') or top_item.get('name')}."
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

    custom_badge_map = {
        "BL": "Boys' Love (BL)",
        "GL": "Girls' Love (GL)",
        "SPORTS": "Real-Life Sports",
        "DOC": "Documentary",
        "ANIME": "Anime",
        "KIDS": "Kids & Family"
    }
    badge = custom_badge_map.get(special_cat)

    def add(movies, bonus=0, why_note=None, enforce_country=False, default_media="movie"):
        for m in movies:
            if not is_safe_non_porn(m):
                continue
            if not m.get("id") or not m.get("poster_path"):
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
            u_key = f"{m_type}_{m['id']}"
            if u_key not in cands:
                m["_bonus"] = bonus
                if why_note:
                    m["_guess_why"] = why_note
                cands[u_key] = m
            else:
                cands[u_key]["_bonus"] = max(cands[u_key].get("_bonus", 0), bonus)

    for idx, g in enumerate((intent.get("plot_guesses") or [])[:12]):
        title = g.get("title") if isinstance(g, dict) else str(g)
        year = g.get("year") if isinstance(g, dict) else None
        why = g.get("why") if isinstance(g, dict) else None
        m_type = g.get("media_type") if isinstance(g, dict) else None
        if not title:
            continue
        hit = search_tmdb_title(title, year, m_type)
        if hit:
            add([hit], bonus=45.0 - (idx * 2.0), why_note=why, default_media=hit.get("media_type", "movie"))

    # Special Category Discover Queries
    if special_cat == "BL":
        origin_p = target_country or "TH|KR|JP|TW|PH"
        add(tmdb("/discover/tv", with_origin_country=origin_p, with_keywords="286407|250606|158718", without_genres="16", sort_by="popularity.desc").get("results", []), bonus=20.0, why_note="Boys' Love (BL) drama series.", default_media="tv")
        add(tmdb("/discover/movie", with_keywords="286407|250606|158718", without_genres="16", sort_by="popularity.desc").get("results", []), bonus=18.0, why_note="Boys' Love (BL) feature film.", default_media="movie")
    elif special_cat == "GL":
        add(tmdb("/discover/tv", with_keywords="264386|9840|158718", without_genres="16", sort_by="popularity.desc").get("results", []), bonus=20.0, why_note="Girls' Love (GL) series.", default_media="tv")
        add(tmdb("/discover/movie", with_keywords="264386|9840", without_genres="16", sort_by="popularity.desc").get("results", []), bonus=18.0, why_note="Girls' Love (GL) film.", default_media="movie")
    elif special_cat == "SPORTS":
        add(tmdb("/discover/tv", with_keywords="6075|13042|6513|1721", without_genres="16,10765", sort_by="popularity.desc").get("results", []), bonus=22.0, why_note="Real-life sports series.", default_media="tv")
        add(tmdb("/discover/movie", with_keywords="6075|13042|6513|1721", without_genres="16,14", sort_by="popularity.desc").get("results", []), bonus=20.0, why_note="Live-action sports film.", default_media="movie")
    elif special_cat == "DOC":
        add(tmdb("/discover/tv", with_genres="99", without_genres="16,10762", sort_by="popularity.desc").get("results", []), bonus=22.0, why_note="True-crime & real-life documentary series.", default_media="tv")
        add(tmdb("/discover/movie", with_genres="99", without_genres="16,10751", sort_by="popularity.desc").get("results", []), bonus=20.0, why_note="Real-life investigative documentary.", default_media="movie")
    elif special_cat == "ANIME":
        origin_p = target_country or "JP|KR|CN"
        add(tmdb("/discover/tv", with_genres="16", with_origin_country=origin_p, sort_by="popularity.desc").get("results", []), bonus=25.0, why_note="Hit Anime series.", default_media="tv")
        add(tmdb("/discover/movie", with_genres="16", with_origin_country=origin_p, sort_by="popularity.desc").get("results", []), bonus=22.0, why_note="Feature Anime movie.", default_media="movie")
    elif special_cat == "KIDS":
        add(tmdb("/discover/movie", with_genres="10751|16", without_genres="27,53,80", sort_by="popularity.desc").get("results", []), bonus=22.0, why_note="Kids, Family & Animated adventure.", default_media="movie")
        add(tmdb("/discover/tv", with_genres="10762|10751", without_genres="80,9648", sort_by="popularity.desc").get("results", []), bonus=18.0, why_note="Kids & Family series.", default_media="tv")

    for t in (intent.get("similar_to") or [])[:2]:
        mid, m_type = find_movie_id(t)
        if mid:
            add(tmdb(f"/{m_type}/{mid}/recommendations").get("results", []), bonus=15.0, why_note=f"Recommended based on '{t}'.", default_media=m_type)

    if not special_cat:
        gids = [str(GENRES[g.lower()]) for g in (intent.get("genres") or []) if g.lower() in GENRES]
        xids = [str(GENRES[g.lower()]) for g in (intent.get("exclude_genres") or []) if g.lower() in GENRES]
        if strict_no_animation and "16" not in xids:
            xids.append("16")

        min_votes = 10 if (target_country or target_lang) else 80
        p = {"include_adult": "false", "vote_count.gte": min_votes, "language": "en-US", "sort_by": "popularity.desc"}
        if gids:
            p["with_genres"] = "|".join(gids[:3]) if target_country else ",".join(gids[:2])
        if xids:
            p["without_genres"] = ",".join(xids)
        if target_lang:
            p["with_original_language"] = target_lang
        if target_country:
            p["with_origin_country"] = target_country

        for page in (1, 2):
            add(tmdb("/discover/movie", page=page, **p).get("results", []), bonus=10.0, enforce_country=True, default_media="movie")
        if target_country or "tv" in (intent.get("media_preference") or ""):
            add(tmdb("/discover/tv", page=1, **p).get("results", []), bonus=10.0, enforce_country=True, default_media="tv")

    return list(cands.values())


def get_seen_and_disliked(username):
    if not username:
        return set(), set()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    ids = set()
    disliked_keywords = set()
    u_lower = username.lower()
    for q in ("SELECT movie_id FROM watchlist WHERE username=?", "SELECT movie_id FROM favorites WHERE username=?", "SELECT movie_id FROM not_interested WHERE username=?"):
        c.execute(q, (u_lower,))
        ids.update(r[0] for r in c.fetchall())
    c.execute("SELECT keywords FROM not_interested WHERE username=?", (u_lower,))
    for row in c.fetchall():
        try:
            for kw in json.loads(row[0] or "[]"):
                if len(kw) > 3:
                    disliked_keywords.add(kw.lower())
        except Exception:
            pass
    conn.close()
    return ids, disliked_keywords


def norm(t):
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def rank(cands, intent, seen_ids, disliked_titles=None, disliked_keywords=None):
    is_plot = intent.get("intent") == "plot_search"
    blocked = {norm(t) for t in (intent.get("exclude_titles") or [])}
    if disliked_titles:
        blocked |= {norm(t) for t in disliked_titles}
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

        title_norm = norm(m.get("title") or m.get("name"))
        if title_norm in blocked:
            continue
        if not is_plot and not m.get("_is_guess") and m["id"] in seen_ids:
            continue

        # Eliminate movies sharing 2+ concept keywords with "Not Interested" titles
        if disliked_keywords:
            text_blob = f"{m.get('title') or ''} {m.get('name') or ''} {m.get('overview') or ''}".lower()
            hits = sum(1 for kw in disliked_keywords if kw in text_blob)
            if hits >= 2:
                continue

        pop = min((m.get("popularity") or 0) / 100, 1.0)
        m["_score"] = (m.get("vote_average") or 0) * 0.7 + pop * 1.5 + m.get("_bonus", 0)
        out.append(m)

    out.sort(key=lambda x: x["_score"], reverse=True)
    top = out[:12]
    if top:
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
    listing = [
        {
            "id": m["id"],
            "title": m.get("title") or m.get("name"),
            "year": (m.get("release_date") or m.get("first_air_date") or "")[:4],
            "overview": (m.get("overview") or "")[:200]
        }
        for m in movies[:8]
    ]
    system = (
        f"You are Nova, a warm, witty AI cinema companion talking to {username}. "
        'Return ONLY JSON: {"reply": "2 engaging sentences directly answering the user and naming top picks", '
        '"reasons": {"<id>": "1 specific sentence explaining why this title fits their request"}}. '
        "Only mention titles from the provided list."
    )
    return groq_json(system, f"User Request: {message}\nTitles: {json.dumps(listing)}", temperature=0.3) or {}


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    client_guesses = data.get("client_guesses") or []
    profile = data.get("profile") or {}
    username = profile.get("name", "Guest")
    fav_genres = profile.get("favorite_genres") or []
    disliked_titles = profile.get("disliked_titles") or []
    selected_country = (profile.get("origin_country") or "").strip().upper()
    history = data.get("history") or []
    region = (data.get("region") or "").upper() or None

    if not message:
        return jsonify({"reply": f"Hey {username}! Tell me a plot, BL/GL craving, real-life sport, documentary, anime, or mood!", "movies": []})

    intent = extract_intent(message, history, username, fav_genres, selected_country, client_guesses)
    intent_type = intent.get("intent", "recommend")

    if intent_type in ("chitchat", "question") and not intent.get("plot_guesses") and not intent.get("genres") and not intent.get("special_category"):
        reply = intent.get("direct_reply") or f"I'm Nova, your AI cinema companion, {username}! Ask me any movie question or plot and I'll find it."
        return jsonify({"reply": reply, "movies": [], "intent": intent_type, "success": True})

    if intent_type == "recommend" and not intent.get("genres") and not intent.get("plot_guesses") and not intent.get("special_category"):
        if fav_genres:
            intent["genres"] = [g.lower() for g in fav_genres[:3]]
        elif intent.get("origin_country"):
            intent["genres"] = COUNTRY_DEFAULT_GENRES.get(intent["origin_country"], ["drama", "romance"])

    if not intent.get("origin_country") and selected_country and intent_type != "plot_search" and not intent.get("special_category"):
        intent["origin_country"] = selected_country

    cands = find_movies(intent)
    if not cands:
        search_res = tmdb("/search/multi", query=message).get("results", [])
        cands = [m for m in search_res if is_safe_non_porn(m) and m.get("poster_path") and m.get("media_type") in ("movie", "tv")]

    seen_ids, disliked_keywords = get_seen_and_disliked(username)
    top = rank(cands, intent, seen_ids, disliked_titles, disliked_keywords)
    if not top and cands:
        top = cands[:12]

    if not top:
        return jsonify({
            "reply": intent.get("direct_reply") or f"I couldn't find an exact match for '{message}', {username}. Try describing another detail or scene!",
            "movies": [], "intent": intent_type, "success": True
        })

    ex = explain(message, username, top, intent)
    reasons = ex.get("reasons", {}) if isinstance(ex.get("reasons"), dict) else {}
    reply = ex.get("reply") or intent.get("direct_reply") or f"Here are my top handpicked matches for '{message}', {username}!"

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
        "exact_genres": format_exact_genres(m, m.get("_customGenreBadge")),
        "_customGenreBadge": m.get("_customGenreBadge"),
        "origin_country": m.get("origin_country") or ([intent["origin_country"]] if intent.get("origin_country") else []),
        "original_language": m.get("original_language", ""),
        "r18": is_genuine_r18(m),
        "match": m.get("_match", 96),
        "platforms": [region or "Global"],
        "rationale": reasons.get(str(m["id"])) or m.get("_guess_why") or f"Matched to your '{message}' request and genre preferences.",
    } for m in top]

    return jsonify({"reply": reply, "movies": movies, "intent": intent_type, "success": True})


@app.route("/trends", methods=["GET"])
def trends():
    return jsonify({
        "ai_forecast": "Super-Nova Multi-API Memory, BL/GL/Anime/Sports/Doc Curated Streams & Concept Elimination Online.",
        "trending_genres": ["Boys' Love (BL) & Girls' Love (GL)", "Real-Life Sports & True-Crime Docs", "Anime & Kids/Family Separation"]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
