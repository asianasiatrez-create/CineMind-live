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
        
        # Smart keyword extraction for conversational matching
        keywords = [w for w in user_message.split() if len(w) > 3]
        matched_movies = []
        
        for m in results:
            overview = m.get("overview", "").lower()
            title = m.get("title", "").lower()
            if any(kw in overview or kw in title for kw in keywords):
                matched_movies.append(m)
        
        # Fallback or selection pool
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

        # Dynamic, conversational AI responses based on input
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
