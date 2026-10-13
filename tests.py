import os
import pytest
from app import app, init_db, DB_NAME
import sqlite3

@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Use a fresh test database for unit tests
    if os.path.exists("test_cinemind.db"):
        os.remove("test_cinemind.db")
    
    # Temporarily override database connection for testing
    import app as main_app
    main_app.DB_NAME = "test_cinemind.db"
    main_app.init_db()

    with app.test_client() as client:
        yield client

    if os.path.exists("test_cinemind.db"):
        os.remove("test_cinemind.db")

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
    payload = {"username": "student_evaluator", "password": " securepassword123"}
    
    # 1. Test Signup
    res_signup = client.post('/api/signup', json=payload)
    assert res_signup.status_code == 200
    assert res_signup.get_json().get("success") is True

    # 2. Test Login with correct credentials
    res_login = client.post('/api/login', json=payload)
    assert res_login.status_code == 200
    assert res_login.get_json().get("success") is True

    # 3. Test Login with incorrect password
    res_bad_login = client.post('/api/login', json={"username": "student_evaluator", "password": "wrongpassword"})
    assert res_bad_login.status_code == 401

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
