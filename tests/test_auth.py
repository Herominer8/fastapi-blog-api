# tests/test_auth.py
from jose import jwt 
from app.core.config import settings
from app.models import User
def test_register_success(client):
    response = client.post("/register", json={
        "username": "newuser",
        "email": "new@example.com",
        "password": "Strong1"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"

def test_register_duplicate_email(client):
    client.post("/register", json={
        "username": "user1",
        "email": "same@example.com",
        "password": "Pass123"
    })
    response = client.post("/register", json={
        "username": "user2",
        "email": "same@example.com",
        "password": "Pass123"
    })
    assert response.status_code == 400
    assert "already exists" in response.text

def test_login_success(client):
    client.post("/register", json={
        "username": "logintest",
        "email": "login@example.com",
        "password": "Login123"
    })
    response = client.post("/login", json={
        "username": "logintest",
        "password": "Login123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password(client):
    client.post("/register", json={
        "username": "wrongpass",
        "email": "wrong@example.com",
        "password": "Correct1"
    })
    response = client.post("/login", json={
        "username": "wrongpass",
        "password": "Wrong1"
    })
    assert response.status_code == 401

def test_get_profile(client, auth_token):
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

def test_token_validation(client, db_session):
    db_session.query(User).delete()
    db_session.commit()
    
    reg = client.post("/register", json={
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "Test123"
    })
    assert reg.status_code == 200
    
    login = client.post("/login", json={
        "username": "testuser2",
        "password": "Test123"
    })
    assert login.status_code == 200
    
    token = login.json()["access_token"]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print(f"Token payload: {payload}")
    except Exception as e:
        print(f"Token decode error: {e}")
        raise


def test_account_lockout_after_5_failed_attempts(client, db_session):
    client.post("/register", json={
        "username": "locktest",
        "email": "lock@example.com",
        "password": "CorrectPass123"
    })
    
    for i in range(5):
        response = client.post("/login", json={
            "username": "locktest",
            "password": "WrongPass"
        })
        assert response.status_code == 401
    
    response = client.post("/login", json={
        "username": "locktest",
        "password": "CorrectPass123"
    })
    assert response.status_code == 403
    assert "locked" in response.text.lower()