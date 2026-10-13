@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_message = data.get("message", "").strip()
    profile = data.get("profile", {"name": "Guest"})
    region = data.get("region", "PH")
    username = profile.get("name", "Guest")

    if not user_message:
        return jsonify({"reply": f"Hey {username}! Tell me what kind of movie you're looking for.", "movies": []})

    ai_reply = f"Here are the precise cinematic matches for your request, {username}!"
    recommendations = []

    if client:
        try:
            # EXPLICIT INSTRUCTION LOCK FOR ACCURACY
            prompt = f"""You are Nova, an expert AI movie recommender. 
            The user typed this exact request: "{user_message}"
            
            CRITICAL RULES:
            1. Do NOT return generic popular movies like Spider-Man, Resident Evil, or Insidious unless specifically asked.
            2. You must select 4 real, specific movies that strictly and accurately match the user's criteria (such as emotional tone, subgenre, era, or theme).
            3. Return a valid JSON object with:
               - "reply": A warm, 1-sentence response as Nova addressing {username}.
               - "recommendations": An array of exactly 4 objects, each containing:
                 - "title": Exact real movie title.
                 - "match": An integer between 95 and 99.
                 - "rationale": A detailed XAI reason explaining why this specific movie matches the user's prompt."""

            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            res_data = json.loads(response.text)
            ai_reply = res_data.get("reply", ai_reply)
            recommendations = res_data.get("recommendations", [])
        except Exception as e:
            print("Gemini Error:", e)

    movies = []
    for rec in recommendations[:4]:
        title = rec.get("title", "")
        rationale = rec.get("rationale", f"Curated for '{user_message}'.")
        match_score = rec.get("match", 98)
        if not title:
            continue
            
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
                    "match": match_score,
                    "platforms": platforms,
                    "rationale": rationale
                })
        except Exception:
            continue

    return jsonify({"reply": ai_reply, "movies": movies})
