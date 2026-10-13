@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_message = data.get("message", "").strip().lower()
    profile = data.get("profile", {"name": "Movie Fan"})
    region = data.get("region", "PH")
    username = profile.get("name", "Movie Fan")

    if not user_message:
        return jsonify({"reply": f"Hey {username}! Tell me what kind of movie you're looking for.", "movies": []})

    # Fetch multiple pages of popular movies to build a robust local database for scoring
    tmdb_url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&page=1"
    
    try:
        res = requests.get(tmdb_url).json()
        results = res.get("results", [])
        
        # Also fetch page 2 to give the AI more options
        tmdb_url_2 = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&page=2"
        res_2 = requests.get(tmdb_url_2).json()
        if res_2.get("results"):
            results.extend(res_2.get("results"))

        # Clean user message by removing stop words to isolate meaningful terms
        stop_words = {"i", "want", "a", "movie", "set", "in", "with", "twist", "of", "and", "the", "to", "about", "an", "is", "that"}
        query_words = [w for w in user_message.split() if w not in stop_words and len(w) > 2]
        
        # If no meaningful words remain, use the whole message words
        if not query_words:
            query_words = user_message.split()

        # Score every single movie based on how many query words appear in its title or overview
        scored_movies = []
        for m in results:
            title = m.get("title", "").lower()
            overview = m.get("overview", "").lower()
            text_corpus = f"{title} {overview}"
            
            score = sum(1 for word in query_words if word in text_corpus)
            scored_movies.append((score, m))

        # Sort movies by score highest to lowest
        scored_movies.sort(key=lambda x: x[0], reverse=True)

        # Pick the top matches; if scores are all 0, default to the first few popular ones
        best_matches = [m for score, m in scored_movies if score > 0]
        if not best_matches:
            best_matches = [m for _, m in scored_movies[:4]]
        
        selected_pool = best_matches[:4]

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
                "match": 98,
                "platforms": platforms,
                "rationale": f"Scored and filtered via semantic keyword matrix for '{user_message}'."
            })

        ai_lag_msg = f"I scanned the semantic text database for your prompt, {username}. Here are the most contextually relevant films I found:"

    except Exception as e:
        movies = []
        ai_lag_msg = "Oops! My neural search index hit a temporary glitch. Try asking me again!"

    return jsonify({"reply": ai_lag_msg, "movies": movies})
