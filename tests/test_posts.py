# tests/test_posts.py
def test_create_post(client, auth_token):
    response = client.post(
        "/posts",
        json={"title": "My Post", "content": "Content", "is_published": True},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "My Post"
    assert "id" in data

def test_create_post_no_auth(client):
    response = client.post("/posts", json={"title": "No Auth", "content": "No", "is_published": True})
    assert response.status_code == 401

def test_list_posts(client, auth_token):
    client.post(
        "/posts",
        json={"title": "List Test", "content": "Content", "is_published": True},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    response = client.get("/posts?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "posts" in data
    assert "total" in data

def test_get_single_post(client, auth_token):
    create = client.post(
        "/posts",
        json={"title": "Single", "content": "Content", "is_published": True},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert create.status_code == 200
    post_id = create.json()["id"]
    
    response = client.get(f"/posts/{post_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Single"

def test_update_post(client, auth_token):
    create = client.post(
        "/posts",
        json={"title": "Old", "content": "Old", "is_published": True},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert create.status_code == 200
    post_id = create.json()["id"]
    
    response = client.put(
        f"/posts/{post_id}",
        json={"title": "New", "content": "New", "is_published": True},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New"

def test_delete_post(client, auth_token):
    create = client.post(
        "/posts",
        json={"title": "To Delete", "content": "Delete", "is_published": True},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert create.status_code == 200
    post_id = create.json()["id"]
    
    response = client.delete(
        f"/posts/{post_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    
    get_response = client.get(f"/posts/{post_id}")
    assert get_response.status_code == 404