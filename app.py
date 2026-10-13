import os
import json
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import hashlib

app = Flask(__name__)
CORS(app)

TMDB_API_KEY = "3dc27f9ae386c422fdc5994e6fda6823"
DB_NAME = "cinemind.db"

# Cleans your API Key instantly in case of accidental quotes/spaces
raw_gemini = os.environ.get("GEMINI_API_KEY", "")
GEMINI_API_KEY = raw_gemini.strip().strip('"').strip("'")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS watchlist (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, movie_id INTEGER NOT NULL, title TEXT NOT NULL, poster TEXT, vote_average REAL, UNIQUE(username, movie_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS favorites (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, movie_id INTEGER NOT NULL, title TEXT NOT NULL, poster TEXT, vote_average REAL, UNIQUE(username, movie_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS interactions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, movie_id INTEGER NOT NULL, title TEXT NOT NULL, action TEXT NOT NULL, vote_average REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "CineMind Gemini 3.0 Engine Live", "version": "600.0"})

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
        cursor.execute(f"INSERT OR REPLACE INTO {table} (username, movie_id, title, poster, vote_average) VALUES (?, ?, ?, ?, ?)", (username, movie_id, title, poster, vote_average))
        action = "added"
        cursor.execute("INSERT INTO interactions (username, movie_id, title, action, vote_average) VALUES (?, ?, ?, ?, ?)", (username, movie_id, title, 'like' if lib_type=='favorites' else 'watched', vote_average))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "action": action})

@app.route("/api/user/insights", methods=["GET"])
def get_insights():
    username = request.args.get("username", "").strip().lower()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT action, vote_average FROM interactions WHERE username = ?", (username,))
    interactions = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) FROM favorites WHERE username = ?", (username,))
    total_liked = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM watchlist WHERE username = ?", (username,))
    total_watchlist = cursor.fetchone()[0]
    conn.close()
    
    total_interactions = len(interactions) or 4
    avg_rating = sum(r[1] for r in interactions if r[1]) / total_interactions if total_interactions > 0 else 8.5
    
    return jsonify({
        "username": username or "Guest",
        "total_recommendations_viewed": total_interactions + 18,
        "total_liked": total_liked + 4,
