@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_message = data.get("message", "").strip().lower()
    profile = data.get("profile", {"name": "Movie Fan"})
    region = data.get("region", "PH")
    username = profile.get("name", "Movie Fan")

    if not user_message:
        return jsonify({"reply": f"Hey {username}! Tell me what kind of movie you're looking for.", "movies": []})

    # Official TMDB Genre Mapping
    genre_map = {
        "action": 28, "adventure": 12, "animation": 16, "comedy": 35,
        "crime": 80, "documentary": 99, "drama": 18, "family": 10751,
        "fantasy": 14, "history": 36, "horror": 27, "music": 10402,
        "mystery": 9648, "romance": 10749, "sci-fi": 878, "science fiction": 878,
        "thriller": 53, "war": 10752, "western": 37
    }

    detected_genres = [gid for word, gid in genre_map.items() if word in user_message]
    
    # If genres are found, use TMDB Discover to guarantee the movies match those genres
    if detected_genres:
        genres_str = ",".join(map(str, detected_genres))
        tmdb_url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&with_genres={genres_str}&sort_by=vote_average.desc"
    else:
        # Otherwise, search TMDB directly
        stop_words = {"i", "want", "a", "movie", "set", "in", "with", "twist", "of", "and", "the", "to", "about", "an", "is", "that"}
        query_words = [w for w in user_message.split() if w not in stop_words]
        query_str = " ".join(query_words) if query_words else user_message
        tmdb_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={requests.utils.quote(query_str)}"

    try:
        res = requests.get(tmdb_url).json()
        results = res.get("results", [])
        
        if not results:
            fallback_res = requests.get(f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&page=1").json()
            results = fallback_res.get("results", [])

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
                "match": 98,
                "platforms": platforms,
                "rationale": f"Filtered and matched via genre/keyword matrix for '{user_message}'."
            })

        ai_reply = f"Here are the most accurate movie matches for your prompt, {username}:"
    except Exception as e:
        movies = []
        ai_reply = "Neural search hit a temporary glitch. Try asking me again!"

    return jsonify({"reply": ai_reply, "movies": movies})
