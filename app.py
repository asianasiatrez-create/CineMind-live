import os
import json
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
    return jsonify({"status": "CineMind Debug Engine Live", "version": "15.0"})

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

    # 1. Attempt Gemini AI
    if client:
        try:
            prompt = f"""You are Nova, an expert AI movie recommender. 
            User request: "{user_message}"
            Provide a JSON response with:
            - "reply": A warm, friendly 1-sentence response as Nova addressing {username}.
            - "titles": An array of exactly 4 real, existing movie titles that accurately match the user's request."""

            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            res_data = json.loads(response.text)
            ai_reply = res_data.get("reply", ai_reply)
            movie_titles = res_data.get("titles", [])
        except Exception as e:
            ai_reply = f"I processed your request, {username}!"

    # 2. GUARANTEED FALLBACK: If Gemini failed or key is missing, parse words so it NEVER falls back to Spider-Man
    if not movie_titles:
        stop_words = {"i", "want", "a", "movie", "wherein", "the", "main", "character", "will", "die", "about", "set", "in", "with", "and", "to", "an", "is", "that"}
        keywords = [w for w in lower_msg.split() if w not in stop_words and len(w) > 2]
        query_str = " ".join(keywords) if keywords else user_message
        
        # Search TMDB using their actual words
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={requests.utils.quote(query_str)}"
        s_res = requests.get(search_url).json()
        results = s_res.get("results", [])
        movie_titles = [m.get("title") for m in results[:4]]

    # 3. Fetch movies from TMDB
    movies = []
    titles_to_fetch = movie_titles if isinstance(movie_titles, list) else [user_message]
    
    for title in titles_to_fetch[:4]:
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
