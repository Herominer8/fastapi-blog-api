# tests/test_admin.py
from app.models import User
def test_admin_list_users(admin_token, client):
    response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1 

def test_admin_list_users_unauthorized(client, auth_token):
    response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 403



def test_admin_list_users_no_token(client):
    response = client.get("/admin/users")
    assert response.status_code == 401



def test_admin_deactivate_user(admin_token, client):

    reg_response = client.post("/register", json={
        "username": "todeactivate",
        "email": "deactivate@example.com",
        "password": "Pass123"
    })
    user_id = reg_response.json()["id"]  
    
    login_response = client.post("/login", json={
        "username": "todeactivate",
        "password": "Pass123"
    })
    assert login_response.status_code == 200
    
    
    response = client.put(
        f"/admin/users/{user_id}/deactivate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert "deactivated" in response.json()["message"].lower()



def test_admin_deactivate_self(admin_token, client, db_session):
    admin_user = db_session.query(User).filter(User.username == "admin").first()
    assert admin_user is not None, "Admin user not found in database"
    
    response = client.put(
        f"/admin/users/{admin_user.id}/deactivate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400
    assert "Cannot deactivate yourself" in response.text

def test_admin_deactivate_nonexistent_user(admin_token, client):
    response = client.put(
        "/admin/users/99999/deactivate",  
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404

def test_admin_deactivate_without_token(client):
    response = client.put("/admin/users/testuser/deactivate")
    assert response.status_code == 401

def test_admin_deactivate_with_user_token(client, auth_token):
    response = client.put(
        "/admin/users/testuser/deactivate",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 403