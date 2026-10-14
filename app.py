@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    username = (data.get("profile") or {}).get("name", "Guest")
    history = data.get("history") or []
    region = (data.get("region") or "").upper() or None

    if not message:
        return jsonify({"reply": f"Hey {username}! Tell me what kind of movie you're looking for.", "movies": []})

    intent = extract_intent(message, history)
    cands = gather_candidates(intent, region)
    
    # Force a fresh search/shuffle if candidates didn't change or came up empty
    if not cands or len(cands) < 4:
        # Fallback to direct keyword search or trending to ensure it always changes
        search_res = tmdb("/search/movie", query=message).get("results", [])
        trending_res = tmdb("/trending/movie/week").get("results", [])
        cands = search_res + trending_res
        cands = [m for m in cands if m.get("poster_path")]

    top = rank(cands, intent, get_seen_ids(username))
    
    # If ranking is too strict, grab the raw candidate slice so it always updates visually
    if not top and cands:
        top = cands[:8]

    if not top:
        return jsonify({"reply": "I couldn't find anything new matching that. Try loosening your filters!",
                        "movies": [], "success": True})

    ex = explain(message, username, top)
    reasons = ex.get("reasons", {}) if isinstance(ex.get("reasons"), dict) else {}
    reply = ex.get("reply") or f"Here are some matches for '{message}', {username}!"

    movies = [{
        "id": m["id"],
        "title": m["title"],
        "poster": f"https://image.tmdb.org/t/p/w500{m['poster_path']}",
        "vote_average": m.get("vote_average", 0.0),
        "vote_count": m.get("vote_count", 0),
        "release_date": m.get("release_date", ""),
        "overview": m.get("overview", ""),
        "match": m.get("_match", 95),
        "platforms": [region or "Global"],
        "rationale": reasons.get(str(m["id"])) or f"Dynamic neural match for '{message}'.",
    } for m in top]

    return jsonify({"reply": reply, "movies": movies, "success": True})
