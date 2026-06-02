import pytest
from fastapi import status
from app.models import User, Post, Notification



def test_create_notification_on_comment(client, auth_token, db_session):

    post_response = client.post(
        "/posts",
        json={"title": "Test Post", "content": "Content", "is_published": True},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert post_response.status_code == 200
    post_id = post_response.json()["id"]
    post_author_id = post_response.json()["author_id"]
    
    client.post("/register", json={
        "username": "commenter",
        "email": "commenter@example.com",
        "password": "Commenter123"
    })
    commenter_login = client.post("/login", json={
        "username": "commenter",
        "password": "Commenter123"
    })
    commenter_token = commenter_login.json()["access_token"]
    
    comment_response = client.post(
        "/comments",
        json={"content": "Nice post!", "post_id": post_id},
        headers={"Authorization": f"Bearer {commenter_token}"}
    )
    assert comment_response.status_code == 200
    
    notification = db_session.query(Notification).filter(
        Notification.user_id == post_author_id,
        Notification.notification_type == "comment"
    ).first()
    
    assert notification is not None
    assert notification.message == "commenter commented on your post: Nice post!..."
    assert notification.is_read == False


def test_get_notifications(client, auth_token, db_session):
    
    post_response = client.post(
        "/posts",
        json={"title": "Notifications Test", "content": "Content", "is_published": True},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert post_response.status_code == 200
    post_id = post_response.json()["id"]
    
    client.post("/register", json={
        "username": "notifuser",
        "email": "notif@example.com",
        "password": "Notif123"
    })
    notif_login = client.post("/login", json={
        "username": "notifuser",
        "password": "Notif123"
    })
    notif_token = notif_login.json()["access_token"]
    

    client.post(
        "/comments",
        json={"content": "First comment", "post_id": post_id},
        headers={"Authorization": f"Bearer {notif_token}"}
    )
    
    response = client.get(
        "/notifications",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["notification_type"] == "comment"
    assert data[0]["is_read"] == False


def test_mark_notification_as_read(client, auth_token, db_session):

    
    post_response = client.post(
        "/posts",
        json={"title": "Read Test", "content": "Content", "is_published": True},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert post_response.status_code == 200
    post_id = post_response.json()["id"]
    
    client.post("/register", json={
        "username": "readuser",
        "email": "read@example.com",
        "password": "Read123"
    })
    read_login = client.post("/login", json={
        "username": "readuser",
        "password": "Read123"
    })
    read_token = read_login.json()["access_token"]
    
    comment_response = client.post(
        "/comments",
        json={"content": "Read me", "post_id": post_id},
        headers={"Authorization": f"Bearer {read_token}"}
    )
    assert comment_response.status_code == 200
    
    notif_response = client.get(
        "/notifications",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert notif_response.status_code == 200
    notif_id = notif_response.json()[0]["id"]
    
    mark_response = client.put(
        f"/notifications/{notif_id}/read",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert mark_response.status_code == 200
    
    notification = db_session.query(Notification).filter(Notification.id == notif_id).first()
    assert notification.is_read == True


def test_get_notifications_without_auth(client):
    response = client.get("/notifications")
    assert response.status_code == 401


def test_mark_notification_other_user(client, auth_token, db_session):
    from app.models import User, Post, Notification
    
    post_response = client.post(
        "/posts",
        json={"title": "Other User Test", "content": "Content", "is_published": True},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert post_response.status_code == 200
    post_id = post_response.json()["id"]
    
    client.post("/register", json={
        "username": "otheruser",
        "email": "other@example.com",
        "password": "Other123"
    })
    other_login = client.post("/login", json={
        "username": "otheruser",
        "password": "Other123"
    })
    other_token = other_login.json()["access_token"]
    
    comment_response = client.post(
        "/comments",
        json={"content": "Test", "post_id": post_id},
        headers={"Authorization": f"Bearer {other_token}"}
    )
    assert comment_response.status_code == 200
    
    notif_response = client.get(
        "/notifications",
        headers={"Authorization": f"Bearer {other_token}"}
    )
    assert notif_response.status_code == 200
    if notif_response.json():
        notif_id = notif_response.json()[0]["id"]
        
        mark_response = client.put(
            f"/notifications/{notif_id}/read",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert mark_response.status_code in [403, 404]


def test_notification_doesnt_create_for_own_comment(client, auth_token, db_session):
    
    db_session.query(Notification).delete()
    db_session.commit()
    
    post_response = client.post(
        "/posts",
        json={"title": "Self Comment", "content": "Content", "is_published": True},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert post_response.status_code == 200
    post_id = post_response.json()["id"]
    
    comment_response = client.post(
        "/comments",
        json={"content": "My own comment", "post_id": post_id},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert comment_response.status_code == 200
    
    user = db_session.query(User).filter(User.username == "testuser").first()
    notification = db_session.query(Notification).filter(
        Notification.user_id == user.id,
        Notification.notification_type == "comment"
    ).first()
    
    assert notification is None