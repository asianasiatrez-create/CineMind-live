import os
import tempfile
import uuid
import pytest
from datetime import date
from app import app, init_db, DB_NAME, calc_age, filter_for_viewer, load_profile, parse_birth_date
import sqlite3

def signup_payload(username, genres=None):
    return {
        "username": username,
        "password": "securepassword123",
        "genres": genres or ["28", "12", "16"],
        "full_name": "Test User",
        "email": f"{username}@example.com",
        "birth_date": "1990-01-02",
    }

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['TODAY'] = date(2026, 11, 4)
    import app as main_app
    db_path = os.path.join(tempfile.gettempdir(), f"test_cinemind_{uuid.uuid4().hex}.db")
    main_app.DB_NAME = db_path
    main_app.init_db()

    with app.test_client() as client:
        yield client

    for suffix in ("", "-shm", "-wal"):
        path = db_path + suffix
        if os.path.exists(path):
            os.remove(path)

def test_home_route(client):
    """Test that the backend root endpoint responds correctly."""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert "Live" in data.get("status", "")

def test_trends_route(client):
    """Test that the trends analytics endpoint returns valid AI forecasts."""
    response = client.get('/trends')
    assert response.status_code == 200
    data = response.get_json()
    assert "ai_forecast" in data
    assert isinstance(data.get("trending_genres"), list)

def test_signup_and_login(client):
    """Test user registration and authentication security flow."""
    payload = {
        "username": "student_evaluator",
        "password": " securepassword123",
        "genres": ["28", "12", "16"],
        "full_name": "Student Evaluator",
        "email": "student_evaluator@example.com",
        "birth_date": "2000-01-02",
    }
    
    # 1. Test Signup
    res_signup = client.post('/api/signup', json=payload)
    assert res_signup.status_code == 200
    signup_data = res_signup.get_json()
    assert signup_data.get("success") is True
    assert signup_data.get("token")
    assert "role" not in signup_data

    # 2. Test Login with correct credentials
    res_login = client.post('/api/login', json=payload)
    assert res_login.status_code == 200
    login_data = res_login.get_json()
    assert login_data.get("success") is True
    assert login_data.get("token")
    assert login_data["profile"]["email"] == "student_evaluator@example.com"
    assert login_data["genres"] == ["28", "12", "16"]
    assert "role" not in login_data
    me = client.get("/api/me", headers={"Authorization": f"Bearer {login_data['token']}"}).get_json()
    assert me["profile"]["full_name"] == "Student Evaluator"

    # 3. Test Login with incorrect password
    res_bad_login = client.post('/api/login', json={"username": "student_evaluator", "password": "wrongpassword"})
    assert res_bad_login.status_code == 401

def test_signup_requires_valid_profile_and_email_is_unique(client):
    invalid_cases = [
        ({"full_name": " "}, "full name"),
        ({"email": "not-an-email"}, "valid email"),
        ({"birth_date": "2027-01-01"}, "date of birth"),
    ]
    for fields, message in invalid_cases:
        payload = signup_payload(f"invalid_{len(fields)}")
        payload.update(fields)
        response = client.post("/api/signup", json=payload)
        assert response.status_code == 400
        assert message in response.get_json()["message"]

    first = signup_payload("email_owner")
    first["email"] = "DUPLICATE@example.com"
    response = client.post("/api/signup", json=first)
    assert response.status_code == 200
    assert response.get_json()["profile"]["email"] == "duplicate@example.com"
    second = signup_payload("email_claimant")
    second["email"] = "duplicate@example.com"
    response = client.post("/api/signup", json=second)
    assert response.status_code == 409
    assert "email" in response.get_json()["message"]

@pytest.mark.parametrize("field,value", [
    ("password", "short"),
    ("password", "p" * 129),
    ("password", 123456),
    ("full_name", "N" * 61),
])
def test_signup_rejects_out_of_range_fields(client, field, value):
    payload = signup_payload(f"invalid_{field}_{len(str(value))}")
    payload[field] = value
    response = client.post("/api/signup", json=payload)
    assert response.status_code == 400

def test_signup_filters_genres_to_frontend_options(client):
    payload = signup_payload("signup_genre_filter")
    payload["genres"] = ["28", "12", "16", "NOT_A_GENRE"]
    response = client.post("/api/signup", json=payload)
    assert response.status_code == 200
    assert response.get_json()["genres"] == ["28", "12", "16"]

    payload["username"] = "signup_too_few_genres"
    payload["genres"] = ["28", "NOT_A_GENRE", "16"]
    response = client.post("/api/signup", json=payload)
    assert response.status_code == 400

def test_signup_rejects_non_object_json(client):
    response = client.post("/api/signup", json=["not", "an", "object"])
    assert response.status_code == 400

def test_profile_routes_update_and_lock_fields(client):
    account = client.post("/api/signup", json=signup_payload("profile_routes")).get_json()
    headers = {"Authorization": f"Bearer {account['token']}"}

    assert client.get("/api/profile").status_code == 401
    assert client.put("/api/profile", json={"full_name": "Updated"}).status_code == 401
    response = client.get("/api/profile", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["profile"]["username"] == "profile_routes"

    response = client.put("/api/profile", headers=headers, json={
        "full_name": "  Updated   Name ",
        "email": " UPDATED@example.com ",
        "birth_date": "1990-01-02",
    })
    assert response.status_code == 200
    assert response.get_json()["profile"]["full_name"] == "Updated Name"
    assert response.get_json()["profile"]["email"] == "updated@example.com"

    assert client.put("/api/profile", headers=headers, json={"email": "bad"}).status_code == 400
    changed_birth_date = client.put("/api/profile", headers=headers, json={"birth_date": "2000-01-02"})
    assert changed_birth_date.status_code == 403

    assert client.put("/api/profile/avatar", headers=headers, json={
        "avatar": "data:image/png;base64,AAAA"
    }).status_code == 200
    assert client.get("/api/profile", headers=headers).get_json()["profile"]["avatar"] == \
        "data:image/png;base64,AAAA"
    assert client.put("/api/profile/avatar", headers=headers, json={
        "avatar": "https://example.com/avatar.png"
    }).status_code == 400
    response = client.delete("/api/profile/avatar", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["profile"]["avatar"] == ""

def test_age_check_separates_blocked_unknown_and_adult(client, monkeypatch):
    import app as main_app

    monkeypatch.setattr(main_app, "viewer_ceiling", lambda: 17)
    monkeypatch.setattr(main_app, "title_facts", lambda media, title_id: {
        1: {"req": 18, "kid": False}, 2: {"req": 10, "kid": True}, 3: None
    }.get(title_id))
    payload = {"items": [
        {"id": 1, "media_type": "movie"},
        {"id": 2, "media_type": "tv"},
        {"id": 3, "media_type": "movie"},
        {"id": "invalid"},
        {},
    ]}
    minor_response = client.post("/api/age/check", json=payload).get_json()
    assert minor_response == {
        "success": True, "is_adult": False, "ceiling": 17,
        "blocked": ["movie_1"], "unknown": ["movie_3"],
    }

    account = client.post("/api/signup", json=signup_payload("adult_check")).get_json()
    adult_headers = {"Authorization": f"Bearer {account['token']}"}
    monkeypatch.setattr(main_app, "viewer_ceiling", lambda: 999)
    adult_response = client.post("/api/age/check", headers=adult_headers, json=payload).get_json()
    assert adult_response == {
        "success": True, "is_adult": True, "blocked": [], "unknown": [],
    }

def test_tiered_age_facts_and_certifications():
    import app as main_app

    assert main_app.cert_age(" tv-14 ") == 14
    assert main_app.cert_age("12+") == 12
    assert main_app.cert_age("unrated") is None

    rated = main_app.title_age_facts({
        "content_ratings": {"results": [
            {"iso_3166_1": "US", "rating": "TV-14"},
        ]},
        "genres": [{"id": 18}],
    }, "tv")
    kid = main_app.title_age_facts({"genres": [{"id": 16}, {"id": 10751}]}, "movie")
    non_kid = main_app.title_age_facts({"genres": [{"id": 16}, {"id": 27}]}, "movie")

    assert rated == {"req": 14, "kid": False}
    assert main_app.facts_allow(rated, 12) is False
    assert main_app.facts_allow(rated, 17) is True
    assert main_app.facts_allow({"req": None, "kid": False}, 17) is True
    assert main_app.facts_allow({"req": None, "kid": False}, 12) is False
    assert main_app.facts_allow(kid, 12) is True
    assert main_app.facts_allow(non_kid, 12) is False
    assert main_app.facts_allow(rated, 999) is True

def test_discover_filters_restricted_and_unverified_titles(client, monkeypatch):
    import app as main_app

    responses = {
        "/discover/movie": {"results": [
            {"id": 10, "title": "Unknown", "poster_path": "/unknown.jpg"},
            {"id": 11, "title": "Safe Movie", "poster_path": "/safe.jpg"},
        ]},
        "/discover/tv": {"results": [
            {"id": 12, "name": "Safe Show", "poster_path": "/show.jpg"},
        ]},
    }
    monkeypatch.setattr(main_app, "tmdb", lambda path, **kwargs: responses[path])
    monkeypatch.setattr(main_app, "viewer_ceiling", lambda: 17)
    monkeypatch.setattr(main_app, "title_facts", lambda media, title_id: (
        None if title_id == 10 else {"req": 10, "kid": False}
    ))

    response = client.get("/api/discover")
    items = response.get_json()["items"]
    assert [(item["id"], item["media_type"]) for item in items] == [
        (11, "movie"), (12, "tv"),
    ]

def test_movie_credits_requires_verified_safe_title(client, monkeypatch):
    import app as main_app

    monkeypatch.setattr(main_app, "viewer_ceiling", lambda: 17)
    monkeypatch.setattr(main_app, "title_facts", lambda media, title_id: None)
    denied = client.get("/api/credits?id=100")
    assert denied.status_code == 403
    assert denied.get_json()["restricted"] is True

    monkeypatch.setattr(main_app, "title_facts", lambda media, title_id: {"req": 10, "kid": False})
    monkeypatch.setattr(main_app, "tmdb", lambda *args, **kwargs: {
        "id": 100, "credits": {}, "watch/providers": {}, "genres": [],
    })
    allowed = client.get("/api/credits?id=100")
    assert allowed.status_code == 200
    assert allowed.get_json()["id"] == 100

def test_chat_minor_prompt_and_restricted_reply_sanitization(client, monkeypatch):
    import app as main_app

    monkeypatch.setattr(main_app, "viewer_is_adult", lambda: False)
    captured = {}

    def fake_extract(message, history, username, genres, guesses, minor=False):
        captured["minor"] = minor
        return {
            "intent": "question", "plot_guesses": [], "genres": [],
            "special_category": None, "direct_reply": "Deadpool is a fun movie.",
        }

    monkeypatch.setattr(main_app, "extract_intent", fake_extract)
    response = client.post("/chat", json={"message": "Tell me about a movie"})
    assert captured["minor"] is True
    assert response.get_json()["reply"] == main_app.MINOR_SAFE_REPLY

def test_minor_rules_are_added_to_intent_and_explanation_prompts(monkeypatch):
    import app as main_app

    systems = []
    def fake_groq_json(system, user, **kwargs):
        systems.append(system)
        return {"intent": "question", "plot_guesses": []}

    monkeypatch.setattr(main_app, "groq_json", fake_groq_json)
    main_app.extract_intent("hello", [], minor=True)
    main_app.explain("hello", "Guest", [], {}, minor=True)

    assert systems[0].endswith(main_app.MINOR_RULE)
    assert systems[1].endswith(main_app.MINOR_RULE)

def test_chat_filters_unverified_candidates_before_explaining(client, monkeypatch):
    import app as main_app

    monkeypatch.setattr(main_app, "viewer_is_adult", lambda: False)
    monkeypatch.setattr(main_app, "extract_intent", lambda *args, **kwargs: {
        "intent": "recommend", "plot_guesses": [], "genres": ["comedy"],
        "special_category": None, "direct_reply": "A safe recommendation.",
    })
    monkeypatch.setattr(main_app, "find_movies", lambda intent: [
        {"id": 20, "title": "Unverified", "poster_path": "/unknown.jpg", "media_type": "movie"},
    ])
    monkeypatch.setattr(main_app, "get_seen_and_disliked", lambda username: (set(), set()))
    monkeypatch.setattr(main_app, "rank", lambda *args: args[0])
    monkeypatch.setattr(main_app, "title_facts", lambda media, title_id: None)
    response = client.post("/chat", json={"message": "Recommend a comedy"})
    assert response.get_json()["reply"] == main_app.MINOR_SAFE_REPLY
    assert response.get_json()["movies"] == []

def test_top10_filters_unknown_and_restricted_before_ranking(client, monkeypatch):
    import app as main_app

    candidates = [
        {"id": 1, "title": "Unknown", "poster_path": "/unknown.jpg"},
        {"id": 2, "title": "Safe One", "poster_path": "/safe-one.jpg"},
        {"id": 3, "title": "Safe Two", "poster_path": "/safe-two.jpg"},
    ]
    monkeypatch.setattr(main_app, "tmdb", lambda *args, **kwargs: {"results": candidates})
    monkeypatch.setattr(main_app, "viewer_ceiling", lambda: 17)
    monkeypatch.setattr(main_app, "title_facts", lambda media, title_id: (
        None if title_id == 1 else {"req": 10, "kid": False}
    ))

    response = client.get("/api/top10")
    items = response.get_json()["items"]
    assert [item["id"] for item in items] == [2, 3]
    assert [item["rank"] for item in items] == [1, 2]

def test_profile_columns_and_unique_email(client):
    import app as main_app

    assert app.config["MAX_CONTENT_LENGTH"] == 1024 * 1024
    conn = sqlite3.connect(main_app.DB_NAME)
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    finally:
        conn.close()
    assert {"email", "full_name", "birth_date", "avatar"}.issubset(columns)

    client.post("/api/signup", json=signup_payload("profile_alpha"))
    client.post("/api/signup", json=signup_payload("profile_bravo"))
    conn = sqlite3.connect(main_app.DB_NAME)
    try:
        conn.execute("UPDATE users SET email = ? WHERE username = ?", ("same@example.com", "profile_alpha"))
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE users SET email = ? WHERE username = ?", ("same@example.com", "profile_bravo"))
    finally:
        conn.close()

def test_profile_age_calculation_and_birth_date_validation():
    today = date(2026, 11, 4)
    assert calc_age(date(2008, 11, 5), today) == 17
    assert calc_age(date(2008, 11, 4), today) == 18
    assert parse_birth_date("2026-11-05") is None
    assert parse_birth_date("not-a-date") is None
    assert parse_birth_date("1990-01-02") == date(1990, 1, 2)

def test_profile_loading_and_age_gate_filter_fail_closed(client, monkeypatch):
    import app as main_app

    client.post("/api/signup", json=signup_payload("profile_viewer"))
    conn = sqlite3.connect(main_app.DB_NAME)
    try:
        conn.execute(
            "UPDATE users SET email = ?, full_name = ?, birth_date = ? WHERE username = ?",
            ("viewer@example.com", "Profile Viewer", "2000-01-02", "profile_viewer"),
        )
        conn.commit()
    finally:
        conn.close()

    profile = load_profile("profile_viewer")
    assert profile["email"] == "viewer@example.com"
    assert profile["full_name"] == "Profile Viewer"
    assert profile["is_adult"] is True
    assert profile["has_birth_date"] is True
    conn = sqlite3.connect(main_app.DB_NAME)
    try:
        assert "age" not in {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    finally:
        conn.close()

    monkeypatch.setattr(main_app, "viewer_ceiling", lambda: 17)
    monkeypatch.setattr(
        main_app, "title_facts",
        lambda media, title_id: (
            {"req": 10, "kid": False} if title_id == 2
            else ({"req": 18, "kid": False} if title_id == 3 else None)
        ),
    )
    items = [
        {"id": 1, "title": "Unverified title", "media_type": "movie"},
        {"id": 2, "title": "Safe title", "media_type": "movie"},
        {"id": 3, "title": "Marked restricted", "media_type": "movie", "r18": True},
    ]
    assert filter_for_viewer(items) == [items[1]]

def test_admin_audit_logs_route_removed(client):
    response = client.get('/api/admin/audit-logs')
    assert response.status_code == 404
    response = client.get('/api/admin/users')
    assert response.status_code == 404

def test_user_data_requires_token_and_uses_token_identity(client):
    genres = ["28", "12", "16"]
    user_a = client.post('/api/signup', json=signup_payload("user_alpha", genres)).get_json()
    user_b = client.post('/api/signup', json=signup_payload("user_bravo", genres)).get_json()

    assert client.get('/api/user/library').status_code == 401
    assert client.get('/api/user/insights').status_code == 401
    assert client.post('/api/user/genres', json={"genres": genres}).status_code == 401

    auth_headers = {"Authorization": f"Bearer {user_a['token']}"}
    response = client.post('/api/user/library/toggle', headers=auth_headers, json={
        "username": "user_bravo",
        "type": "watchlist",
        "movie": {"id": 101, "title": "Example", "media_type": "movie"},
    })
    assert response.status_code == 200

    response = client.get('/api/user/library?username=user_bravo', headers=auth_headers)
    assert response.status_code == 200
    assert [movie["id"] for movie in response.get_json()["watchlist"]] == [101]

    response = client.get('/api/user/library', headers={
        "Authorization": f"Bearer {user_b['token']}"
    })
    assert response.status_code == 200
    assert response.get_json()["watchlist"] == []

    response = client.post('/api/user/genres', headers=auth_headers, json={"genres": genres})
    assert response.status_code == 200
    assert response.get_json()["genres"] == genres

def test_ratings_require_auth_and_recompute_preferences(client):
    user_a = client.post('/api/signup', json=signup_payload("rating_alpha")).get_json()
    user_b = client.post('/api/signup', json=signup_payload("rating_bravo")).get_json()
    headers_a = {"Authorization": f"Bearer {user_a['token']}"}
    headers_b = {"Authorization": f"Bearer {user_b['token']}"}

    assert client.get('/api/ratings/mine').status_code == 401
    assert client.put('/api/ratings/movie/101', json={"rating": 5}).status_code == 401

    payload = {
        "rating": 5,
        "meta": {"genres": ["28", "18"], "tags": ["Space opera", "Space opera"], "year": 2024},
    }
    response = client.put('/api/ratings/movie/101', headers=headers_a, json=payload)
    assert response.status_code == 200
    assert response.get_json()["community"] == {"average": 5.0, "count": 1}
    assert response.get_json()["preferences"]["genres"]["28"] > 0
    assert response.get_json()["preferences"]["tags"]["space opera"] > 0

    payload["rating"] = 1
    response = client.put('/api/ratings/movie/101', headers=headers_a, json=payload)
    assert response.status_code == 200
    assert response.get_json()["community"] == {"average": 1.0, "count": 1}
    assert response.get_json()["preferences"]["genres"]["28"] < 0

    mine = client.get('/api/ratings/mine', headers=headers_a).get_json()
    assert mine["ratings"] == {"movie_101": 1}
    assert client.get('/api/ratings/mine', headers=headers_b).get_json()["ratings"] == {}
    assert client.get('/api/titles/movie/101/ratings', headers=headers_b).get_json()["mine"] == {
        "rating": None, "review": None
    }

    response = client.delete('/api/ratings/movie/101', headers=headers_a)
    assert response.status_code == 200
    assert response.get_json()["community"] == {"average": None, "count": 0}
    assert response.get_json()["preferences"]["genres"] == {}
    assert client.get('/api/ratings/mine', headers=headers_a).get_json()["ratings"] == {}

def test_ratings_validate_and_reviews_are_user_scoped(client):
    user_a = client.post('/api/signup', json=signup_payload("review_alpha")).get_json()
    user_b = client.post('/api/signup', json=signup_payload("review_bravo")).get_json()
    headers_a = {"Authorization": f"Bearer {user_a['token']}"}
    headers_b = {"Authorization": f"Bearer {user_b['token']}"}

    for bad_rating in (0, 6, 3.5, True, "5"):
        response = client.put(
            '/api/ratings/tv/202',
            headers=headers_a,
            json={"rating": bad_rating},
        )
        assert response.status_code == 400
    assert client.put('/api/ratings/book/202', headers=headers_a, json={"rating": 4}).status_code == 400

    assert client.put('/api/reviews/movie/202', json={"body": "No token"}).status_code == 401
    saved = client.put('/api/reviews/movie/202', headers=headers_a, json={
        "body": "A thoughtful story.\x01\n\n\nGreat cast."
    })
    assert saved.status_code == 200
    assert saved.get_json()["body"] == "A thoughtful story.\n\nGreat cast."
    assert client.put('/api/reviews/movie/202', headers=headers_a, json={"body": "   "}).status_code == 400

    reviews = client.get('/api/titles/movie/202/reviews?limit=1').get_json()
    assert reviews["total"] == 1
    assert reviews["reviews"][0]["username"] == "review_alpha"
    assert reviews["reviews"][0]["mine"] is False
    assert client.get('/api/titles/movie/202/ratings', headers=headers_a).get_json()["mine"]["review"] == saved.get_json()["body"]

    assert client.delete('/api/reviews/movie/202', headers=headers_b).status_code == 200
    assert client.get('/api/titles/movie/202/reviews').get_json()["total"] == 1
    assert client.delete('/api/reviews/movie/202', headers=headers_a).status_code == 200
    assert client.get('/api/titles/movie/202/reviews').get_json()["total"] == 0

def test_chat_ai_endpoint(client):
    """Test AI chat recommendation response payload."""
    response = client.post('/chat', json={
        "message": "sci-fi space adventure",
        "profile": {"name": "Evaluator"},
        "region": "PH"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert "reply" in data
    assert "movies" in data
