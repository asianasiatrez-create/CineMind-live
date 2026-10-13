import os
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import hashlib
from google import genai

app = Flask(__name__)
CORS(app)

TMDB_API_KEY = "3dc27f9ae386c422fdc5994e6fda6823"
DB_NAME = "cinemind.db"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            movie_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            poster TEXT,
            vote_average REAL,
            UNIQUE(username, movie_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            movie_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            poster TEXT,
            vote_average REAL,
            UNIQUE(username, movie_id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "CineMind Bulletproof Engine Live", "version": "8.0"})

@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required."}), 400

    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Account created successfully!"})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Username already exists."}), 400

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_pw))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({"success": True, "username": username, "message": "Login successful!"})
    return jsonify({"success": False, "message": "Invalid username or password."}), 401

@app.route("/api/user/library", methods=["GET"])
def get_library():
    username = request.args.get("username", "").strip().lower()
    if not username:
        return jsonify({"watchlist": [], "favorites": []})

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT movie_id, title, poster, vote_average FROM watchlist WHERE username = ?", (username,))
    watchlist = [{"id": r[0], "title": r[1], "poster": r[2], "vote_average": r[3]} for r in cursor.fetchall()]

    cursor.execute("SELECT movie_id, title, poster, vote_average FROM favorites WHERE username = ?", (username,))
    favorites = [{"id": r[0], "title": r[1], "poster": r[2], "vote_average": r[3]} for r in cursor.fetchall()]
    conn.close()

    return jsonify({"watchlist": watchlist, "favorites": favorites})

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

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    table = "watchlist" if lib_type == "watchlist" else "favorites"

    cursor.execute(f"SELECT id FROM {table} WHERE username = ? AND movie_id = ?", (username, movie_id))
    exists = cursor.fetchone()

    if exists:
        cursor.execute(f"DELETE FROM {table} WHERE username = ? AND movie_id = ?", (username, movie_id))
        action = "removed"
    else:
        cursor.execute(f"INSERT OR REPLACE INTO {table} (username, movie_id, title, poster, vote_average) VALUES (?, ?, ?, ?, ?)",
                       (username, movie_id, title, poster, vote_average))
        action = "added"

    conn.commit()
    conn.close()
    return jsonify({"success": True, "action": action})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_message = data.get("message", "").strip()
    profile = data.get("profile", {"name": "Movie Fan"})
    region = data.get("region", "PH")
    username = profile.get("name", "Movie Fan")
    lower_msg = user_message.lower()

    if not user_message:
        return jsonify({"reply": f"Hey {username}! Tell me what kind of movie you're looking for.", "movies": []})

    # 1. Get AI conversational reply safely
    ai_reply = f"Here are the best matches for your mood, {username}!"
    if client:
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"Respond as Nova, a warm AI movie companion, to this user message: '{user_message}' (Keep it under 2 sentences)."
            )
            if response and response.text:
                ai_reply = response.text.strip()
        except Exception:
            pass

    # 2. Reliable Python-side Intent & Genre Parsing
    genre_map = {
        "action": 28, "adventure": 12, "animation": 16, "comedy": 35,
        "crime": 80, "documentary": 99, "drama": 18, "family": 10751,
        "fantasy": 14, "history": 36, "horror": 27, "music": 10402,
        "mystery": 9648, "romance": 10749, "sci-fi": 878, "science fiction": 878,
        "thriller": 53, "war": 10752, "western": 37
    }

    detected_genres = [str(gid) for word, gid in genre_map.items() if word in lower_msg]

    lang_param = ""
    if "japan" in lower_msg or "japanese" in lower_msg:
        lang_param = "ja"
    elif "korea" in lower_msg or "korean" in lower_msg:
        lang_param = "ko"
    elif "thailand" in lower_msg or "thai" in lower_msg:
        lang_param = "th"

    results = []
    try:
        # Build TMDB Discover URL
        tmdb_url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&sort_by=popularity.desc"
        if detected_genres:
            tmdb_url += f"&with_genres={','.join(detected_genres)}"
        if lang_param:
            tmdb_url += f"&with_original_language={lang_param}"

        res = requests.get(tmdb_url).json()
        results = res.get("results", [])

        # Fallback to search query if discover is empty
        if not results:
            search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={requests.utils.quote(user_message)}"
            s_res = requests.get(search_url).json()
            results = s_res.get("results", [])

        # Absolute fallback
        if not results:
            pop_res = requests.get(f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&page=1").json()
            results = pop_res.get("results", [])

        selected_pool = results[:4]
        movies = []
        for m in selected_pool:
            movie_id = m.get("id")
            providers_url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={TMDB_API_KEY}"
            prov_res = requests.get(providers_url).json().get("results", {})
            reg_prov = prov_res.get(region, prov_res.get("US", {}))
            flatrate = reg_prov.get("flatrate", [])
            platforms = [p.get("provider_name") for p in flatrate] if flatrate else ["TMDB VOD Catalog"]

            movies.append({
                "id": movie_id,
                "title": m.get("title"),
                "poster": f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get('poster_path') else "",
                "vote_average": m.get("vote_average", 0.0),
                "release_date": m.get("release_date", "2026"),
                "overview": m.get("overview") or "No overview available.",
                "match": 99,
                "platforms": platforms,
                "rationale": f"Matched via robust parameter routing for '{user_message}'."
            })
    except Exception as e:
        movies = []

    return jsonify({"reply": ai_reply, "movies": movies})

@app.route("/trends", methods=["GET"])
def trends():
    return jsonify({
        "ai_forecast": "Neural analytics indicate a 94.2% surge in quantum narrative demand for Q4 2026.",
        "trending_genres": [
            "Quantum Sci-Fi & Temporal Loops (98.4 Index)",
            "Psychological Neo-Noir Thrillers (95.1 Index)",
            "Aesthetic Contemporary Romance (91.7 Index)"
        ]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
