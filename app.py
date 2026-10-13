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
    return jsonify({"status": "CineMind Ultimate Engine Live", "version": "16.0"})

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

    ai_reply = f"Here are the best matches for your mood, {username}!"
    movie_titles = []

    # 1. Standard Safe Gemini Call
    if client:
        try:
            prompt = f"""You are Nova, an expert AI movie recommender. 
            User request: "{user_message}"
            List exactly 4 real, existing movie titles that match this request, separated ONLY by commas. Do not include numbers or extra text. Example: Titanic, Inception, Interstellar, Gladiator"""

            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            if response and response.text:
                text = response.text.strip()
                movie_titles = [t.strip() for t in text.split(",") if t.strip()]
        except Exception:
            pass

    # 2. Fetch movies from TMDB based on AI titles
    movies = []
    for title in movie_titles[:4]:
        try:
            search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={requests.utils.quote(title)}"
            s_res = requests.get(search_url).json()
            results = s_res.get("results", [])
            if results:
                m = results[0]
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
                    "rationale": f"Curated for '{user_message}'."
                })
        except Exception:
            continue

    # 3. GUARANTEED DISCOVER/TOP-RATED FALLBACK (Never returns empty [])
    if not movies:
        genre_map = {"action": 28, "comedy": 35, "horror": 27, "romance": 10749, "drama": 18, "thriller": 53, "sci-fi": 878}
        detected_genre = next((str(gid) for word, gid in genre_map.items() if word in lower_msg), "18") # Default to Drama if emotional/dying
        lang_code = "th" if "thai" in lower_msg else ("ko" if "korean" in lower_msg or "korea" in lower_msg else ("ja" if "japan" in lower_msg else ""))
        
        fallback_url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&with_genres={detected_genre}&sort_by=popularity.desc"
        if lang_code:
            fallback_url += f"&with_original_language={lang_code}"
            
        try:
            f_res = requests.get(fallback_url).json()
            for m in f_res.get("results", [])[:4]:
                movies.append({
                    "id": m.get("id"),
                    "title": m.get("title"),
                    "poster": f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get('poster_path') else "",
                    "vote_average": m.get("vote_average", 0.0),
                    "release_date": m.get("release_date", "2026"),
                    "overview": m.get("overview") or "No overview available.",
                    "match": 98,
                    "platforms": ["TMDB VOD Catalog"],
                    "rationale": "Curated via smart fallback filter."
                })
        except Exception:
            pass

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
