import os
import tempfile
import uuid
import pytest
from app import app, init_db, DB_NAME
import sqlite3

@pytest.fixture
def client():
    app.config['TESTING'] = True
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
    assert "role" not in login_data

    # 3. Test Login with incorrect password
    res_bad_login = client.post('/api/login', json={"username": "student_evaluator", "password": "wrongpassword"})
    assert res_bad_login.status_code == 401

def test_admin_audit_logs_route_removed(client):
    response = client.get('/api/admin/audit-logs')
    assert response.status_code == 404
    response = client.get('/api/admin/users')
    assert response.status_code == 404

def test_user_data_requires_token_and_uses_token_identity(client):
    genres = ["28", "12", "16"]
    user_a = client.post('/api/signup', json={
        "username": "user_alpha", "password": "securepassword123", "genres": genres
    }).get_json()
    user_b = client.post('/api/signup', json={
        "username": "user_bravo", "password": "securepassword123", "genres": genres
    }).get_json()

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
    user_a = client.post('/api/signup', json={
        "username": "rating_alpha", "password": "securepassword123", "genres": ["28", "12", "16"]
    }).get_json()
    user_b = client.post('/api/signup', json={
        "username": "rating_bravo", "password": "securepassword123", "genres": ["28", "12", "16"]
    }).get_json()
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
    user_a = client.post('/api/signup', json={
        "username": "review_alpha", "password": "securepassword123", "genres": ["28", "12", "16"]
    }).get_json()
    user_b = client.post('/api/signup', json={
        "username": "review_bravo", "password": "securepassword123", "genres": ["28", "12", "16"]
    }).get_json()
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
