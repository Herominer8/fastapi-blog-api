import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, limiter 
from app.core.database import Base, get_db
from app.models import User
from app.core.config import settings


print(f"SECRET_KEY: {settings.SECRET_KEY}")
TEST_DATABASE_URL = "sqlite:///./test.db"
limiter.enabled = False

@pytest.fixture(scope="session")
def engine():
    return create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

@pytest.fixture(scope="session")
def tables(engine):
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(engine, tables):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

@pytest.fixture
def auth_token(client, db_session):
    db_session.query(User).delete()
    db_session.commit()
    
    reg_response = client.post("/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test123"
    })
    if reg_response.status_code != 200:
        pytest.fail(f"Registration failed: {reg_response.status_code} - {reg_response.text}")
    
    user = db_session.query(User).filter(User.username == "testuser").first()
    if user:
        user.is_verified = True
        db_session.commit()
    
    login_response = client.post("/login", json={
        "username": "testuser",
        "password": "Test123"
    })
    if login_response.status_code != 200:
        pytest.fail(f"Login failed: {login_response.status_code} - {login_response.text}")
    
    token = login_response.json().get("access_token")
    if not token:
        pytest.fail("No access token in login response")
    return token

@pytest.fixture
def admin_token(client, db_session):
    db_session.query(User).delete()
    db_session.commit()
    
    reg_response = client.post("/register", json={
        "username": "admin",
        "email": "admin@example.com",
        "password": "Admin123"
    })
    if reg_response.status_code != 200:
        pytest.fail(f"Admin registration failed: {reg_response.status_code} - {reg_response.text}")
    
    user = db_session.query(User).filter(User.username == "admin").first()
    if user:
        user.is_admin = True
        db_session.commit()
    
    client.post("/register", json={
        "username": "normaluser",
        "email": "normal@example.com",
        "password": "Normal123"
    })
    
    login_response = client.post("/login", json={
        "username": "admin",
        "password": "Admin123"
    })
    if login_response.status_code != 200:
        pytest.fail(f"Admin login failed: {login_response.status_code} - {login_response.text}")
    
    token = login_response.json().get("access_token")
    if not token:
        pytest.fail("No access token in admin login response")
    return token