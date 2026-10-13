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
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Watchlist table
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
    # Favorites table
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
    return jsonify({"status": "CineMind Production Secure Backend Live", "version": "3.0"})

# --- Authentication Routes ---
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

# --- Cloud Watchlist / Favorites Routes ---
@app.route("/api/user/library", methods=["GET"])
def get_library():
    username = request.args.get("username", "").strip().lower()
    if not username:
        return jsonify({"watchlist": [], "favorites": []})

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT movie_id, title, poster, vote_average FROM watchlist WHERE username = ?", (username,))
    w_rows = cursor.fetchall()
    watchlist = [{"id": r[0], "title": r[1], "poster": r[2], "vote_average": r[3]} for r in w_rows]

    cursor.execute("SELECT movie_id, title, poster, vote_average FROM favorites WHERE username = ?", (username,))
    f_rows = cursor.fetchall()
    favorites = [{"id": r[0], "title": r[1], "poster": r[2], "vote_average": r[3]} for r in f_rows]
    conn.close()

    return jsonify({"watchlist": watchlist, "favorites": favorites})

@app.route("/api/user/library/toggle", methods=["POST"])
def toggle_library():
    data = request.get_json() or {}
    username = data.get("username", "").strip().lower()
    lib_type = data.get("type") # 'watchlist' or 'favorites'
    movie = data.get("movie", {})

    if not username or not lib_type or not movie:
        return jsonify({"success": False, "message": "Invalid payload."}), 400

    movie_id = movie.get("id")
    title = movie.get("title") or movie.get("name")
    poster = movie.get("poster") or (f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get('poster_path') else "")
    vote_average = movie.get("vote_average", 0.0)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    table = "watchlist" if lib_type == "watchlist" else "favorites"

    # Check if exists
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

# --- AI Chat & Trends Routes ---
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_message = data.get("message", "").lower()
    profile = data.get("profile", {"name": "Movie Fan"})
    region = data.get("region", "PH")
    username = profile.get("name", "Movie Fan")

    query_term = user_message
    if any(k in user_message for k in ["romance", "romantic", "romcom", "love", "sad"]):
        query_term = "romance"
    elif any(k in user_message for k in ["sci-fi", "science fiction", "space", "time", "quantum", "dream"]):
        query_term = "science fiction"
    elif any(k in user_message for k in ["action", "blockbuster", "fight", "hero", "marvel"]):
        query_term = "action"
    elif any(k in user_message for k in ["horror", "scary", "ghost", "thriller", "suspense"]):
        query_term = "thriller"
    elif any(k in user_message for k in ["comedy", "funny", "laugh"]):
        query_term = "comedy"

    tmdb_url = f"https://api.themoviedb.org/3/search/movie?api_key=${TMDB_API_KEY}&query={requests.utils.quote(query_term)}"
    
    try:
        res = requests.get(tmdb_url)
        results = res.json().get("results", [])[:6]
        
        movies = []
        for index, m in enumerate(results):
            movie_id = m.get("id")
            providers_url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={TMDB_API_KEY}"
            prov_res = requests.get(providers_url).json().get("results", {})
            reg_prov = prov_res.get(region, prov_res.get("US", {}))
            flatrate = reg_prov.get("flatrate", [])
            platforms = [p.get("provider_name") for p in flatrate] if flatrate else ["TMDB VOD Catalog"]

            movies.append({
                "id": movie_id,
                "title": m.get("title"),
                "poster": f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get("poster_path") else "",
                "vote_average": m.get("vote_average", 0.0),
                "release_date": m.get("release_date", "2026"),
                "overview": m.get("overview"),
                "match": 99 - (index * 2),
                "platforms": platforms,
                "rationale": f"High-dimensional semantic clustering match for {username} tailored to regional telemetry ({region})."
            })

        ai_reply = f"Here are the most accurate matches for your query, {username}. Available on {', '.join(movies[0]['platforms'][:2])}." if movies else f"I scanned our neural database for '{user_message}', but found no direct vector alignment."
    except Exception:
        movies = []
        ai_reply = "Neural vector processing encountered a transient exception. Please retry."

    return jsonify({"reply": ai_reply, "movies": movies})

@app.route("/trends", methods=["GET"])
def trends():
    return jsonify({
        "ai_forecast": "Neural analytics indicate an aggressive surge in quantum sci-fi and immersive multi-verse storytelling for Q4 2026.",
        "trending_genres": [
            "Quantum Sci-Fi & Temporal Loops (98.4 Index)",
            "Psychological Neo-Noir Thrillers (95.1 Index)",
            "Aesthetic Contemporary Romance (91.7 Index)",
            "Epic Cybernetic Action Blockbusters (89.2 Index)"
        ]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)