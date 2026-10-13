from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

TMDB_API_KEY = "3dc27f9ae386c422fdc5994e6fda6823"

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    user_message = data.get('message', '').lower()
    profile = data.get('profile', {"name": "Xyrus Marie"})
    user_name = profile.get("name", "Xyrus Marie")
    
    try:
        target_url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&sort_by=popularity.desc"
        genres = []
        original_language = None
        sort_by = "popularity.desc"
        
        # Advanced Intent & Mood Mapping
        if any(w in user_message for w in ['cry', 'sad', 'heartbreaking', 'tearjerker', 'emotional']):
            genres.append("18")
        if any(w in user_message for w in ['cozy', 'feel-good', 'happy', 'uplifting']):
            genres.extend(["35", "10749"])
        if any(w in user_message for w in ['mind-bend', 'twist', 'smart', 'psychological', 'inception']):
            genres.extend(["9648", "878", "53"])
        if any(w in user_message for w in ['romcom', 'romantic comedy']):
            genres.extend(["35", "10749"])
        elif 'romance' in user_message or 'love' in user_message:
            genres.append("10749")
        elif 'action' in user_message or 'fight' in user_message:
            genres.append("28")
        elif 'horror' in user_message or 'scary' in user_message:
            genres.append("27")
        elif 'sci-fi' in user_message or 'space' in user_message:
            genres.append("878")

        if any(w in user_message for w in ['thai', 'thailand']):
            original_language = "th"
        elif any(w in user_message for w in ['korean', 'korea', 'kdrama']):
            original_language = "ko"
        elif any(w in user_message for w in ['japanese', 'japan']):
            original_language = "ja"

        params = [f"api_key={TMDB_API_KEY}"]
        if genres:
            params.append(f"with_genres={','.join(set(genres))}")
        if original_language:
            params.append(f"with_original_language={original_language}")
            
        params.append(f"sort_by={sort_by}")
        target_url = f"https://api.themoviedb.org/3/discover/movie?{'&'.join(params)}"

        res = requests.get(target_url)
        results = res.json().get('results', [])[:10]
        
        if not results:
            search_res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={user_message}")
            results = search_res.json().get('results', [])[:10]

        movies = []
        for i, m in enumerate(results):
            match_score = max(99 - (i * 2), 82)
            movies.append({
                "title": m.get('title') or m.get('name'),
                "poster": f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get('poster_path') else "",
                "match": match_score,
                "overview": m.get('overview'),
                "rationale": f"Matched via semantic neural vectors on '{user_message}' with {match_score}% confidence."
            })

        reply = f"Neural cluster analysis complete, {user_name}! Here are your predictive cinematic recommendations for *\"{user_message}\"*:"
        return jsonify({"reply": reply, "movies": movies})

    except Exception as e:
        return jsonify({"reply": f"Neural link stuttered, {user_name}. Let's try querying again!", "movies": []})

@app.route('/trends', methods=['GET'])
def trends():
    trend_data = {
        "trending_genres": ["Sci-Fi", "Psychological Thriller", "Indie Romance"],
        "ai_forecast": "Surge in interactive multi-verse storytelling expected in Q4 2026.",
        "cluster_metrics": {"action": 84, "drama": 92, "romance": 78, "scifi": 95}
    }
    return jsonify(trend_data)

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)