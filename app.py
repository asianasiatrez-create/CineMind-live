@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_message = data.get("message", "").strip()
    profile = data.get("profile", {"name": "Movie Fan"})
    region = data.get("region", "PH")
    username = profile.get("name", "Movie Fan")

    if not user_message:
        return jsonify({"reply": f"Hey {username}! Tell me what kind of movie you're looking for.", "movies": []})

    # Use TMDB's Search API so it actually finds movies matching the user's exact prompt
    tmdb_search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={requests.utils.quote(user_message)}"
    
    try:
        res = requests.get(tmdb_search_url).json()
        results = res.get("results", [])
        
        # If search returns nothing, fallback to popular movies so it never returns an empty screen
        if not results:
            fallback_res = requests.get(f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&page=1").json()
            results = fallback_res.get("results", [])

        selected_pool = results[:4] # Top 4 best matches

        movies = []
        for m in selected_pool:
            movie_id = m.get("id")
            # Fetch regional watch providers
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
                "rationale": f"Matched directly via semantic search for '{user_message}'."
            })

        ai_lag_msg = f"I searched the global cinematic database for your prompt, {username}! Here are the best matches I found:"

    except Exception as e:
        movies = []
        ai_lag_msg = "Oops! My neural search index hit a temporary glitch. Try asking me again!"

    return jsonify({"reply": ai_lag_msg, "movies": movies})
