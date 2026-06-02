import os
from fastapi import status
from app.models import User

def test_upload_profile_picture_success(client, auth_token, db_session):
    test_file_content = b"fake image content"
    files = {"file": ("test.jpg", test_file_content, "image/jpeg")}
    
    response = client.post(
        "/users/me/profile-picture",
        files=files,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "file_path" in data
    

    user = db_session.query(User).filter(User.username == "testuser").first()
    assert user.profile_picture is not None
    assert os.path.exists(user.profile_picture)
    
    if user.profile_picture and os.path.exists(user.profile_picture):
        os.remove(user.profile_picture)
        user.profile_picture = None
        db_session.commit()


def test_upload_profile_picture_wrong_type(client, auth_token):
    test_file_content = b"fake text content"
    files = {"file": ("test.txt", test_file_content, "text/plain")}
    
    response = client.post(
        "/users/me/profile-picture",
        files=files,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "JPEG and PNG" in response.text


def test_upload_profile_picture_too_large(client, auth_token):
    large_content = b"x" * (3 * 1024 * 1024)
    files = {"file": ("large.jpg", large_content, "image/jpeg")}
    
    response = client.post(
        "/users/me/profile-picture",
        files=files,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "2MB" in response.text


def test_upload_profile_picture_without_auth(client):
    test_file_content = b"fake image content"
    files = {"file": ("test.jpg", test_file_content, "image/jpeg")}
    
    response = client.post(
        "/users/me/profile-picture",
        files=files
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_profile_picture_success(client, auth_token, db_session):
    test_file_content = b"fake image content"
    files = {"file": ("test_get.jpg", test_file_content, "image/jpeg")}
    
    upload_response = client.post(
        "/users/me/profile-picture",
        files=files,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert upload_response.status_code == 200
    
    response = client.get(
        "/users/me/profile-picture",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] in ["image/jpeg", "image/jpg"]
    
    user = db_session.query(User).filter(User.username == "testuser").first()
    if user.profile_picture and os.path.exists(user.profile_picture):
        os.remove(user.profile_picture)
        user.profile_picture = None
        db_session.commit()


def test_get_profile_picture_not_found(client, auth_token, db_session):
    
    user = db_session.query(User).filter(User.username == "testuser").first()
    if user.profile_picture and os.path.exists(user.profile_picture):
        os.remove(user.profile_picture)
    user.profile_picture = None
    db_session.commit()
    
    response = client.get(
        "/users/me/profile-picture",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND