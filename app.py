import os
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import hashlib

app = Flask(__name__)
CORS(app)

TMDB_API_KEY = "3dc27f9ae386c422fdc5994e6fda6823"
DB_NAME = "cinemind.db"

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
    return jsonify({"status": "CineMind AI Neural Backend Live", "version": "4.1"})

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
    user_message = data.get("message", "").strip().lower()
    profile = data.get("profile", {"name": "Movie Fan"})
    region = data.get("region", "PH")
    username = profile.get("name", "Movie Fan")

    tmdb_url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&page=1"
    
    try:
        res = requests.get(tmdb_url).json()
        results = res.get("results", [])
        
        keywords = [w for w in user_message.split() if len(w) > 3]
        matched_movies = []
        
        for m in results:
            overview = m.get("overview", "").lower()
            title = m.get("title", "").lower()
            if any(kw in overview or kw in title for kw in keywords):
                matched_movies.append(m)
        
        selected_pool = matched_movies[:4] if matched_movies else results[:4]

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
                "overview": m.get("overview"),
                "match": 96,
                "platforms": platforms,
                "rationale": f"Hand-picked by Nova for {username} based on your vibe!"
            })

        if "sad" in user_message or "cry" in user_message or "heartbreak" in user_message:
            ai_lag_msg = f"Oh no, {username}... 🥺 Sounds like you're in the mood for an emotional rollercoaster. Grab some tissues and check out these powerful stories I found for you:"
        elif "sci-fi" in user_message or "space" in user_message or "future" in user_message:
            ai_lag_msg = f"Ooh, quantum vibes! 🌌 Let's bend some realities together, {username}. Here are some mind-expanding sci-fi picks:"
        elif "action" in user_message or "fight" in user_message or "thrill" in user_message:
            ai_lag_msg = f"Time for some adrenaline, {username}! 💥 Buckle up, because these high-octane blockbusters will keep you on the edge of your seat:"
        elif "romance" in user_message or "love" in user_message or "romcom" in user_message:
            ai_lag_msg = f"Aww, love is in the air! 💕 Here are some gorgeous, heartwarming romantic flicks just for you, {username}:"
        else:
            ai_lag_msg = f"I love that prompt, {username}! ✨ I dug through the cinematic matrix and pulled out these stellar matches that fit your exact mood:"

    except Exception as e:
        movies = []
        ai_lag_msg = "Oops! My neural circuits hit a slight glitch, but I'm right here with you. Try asking me again!"

    return jsonify({"reply": ai_lag_msg, "movies": movies})

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
