# tests/test_likes.py
def test_like_post(client, auth_token):
    post = client.post(
        "/posts",
        json={"title": "Like Post", "content": "Content"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert post.status_code == 200
    post_id = post.json()["id"]
    
    response = client.post(
        f"/posts/{post_id}/like",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Liked"
    
    response = client.post(
        f"/posts/{post_id}/like",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Unliked"

def test_likes_count(client, auth_token):
    post = client.post(
        "/posts",
        json={"title": "Count Likes", "content": "Content"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert post.status_code == 200
    post_id = post.json()["id"]
    
    client.post(
        f"/posts/{post_id}/like",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    response = client.get(f"/posts/{post_id}/likes-count")
    assert response.status_code == 200
    assert response.json()["likes_count"] == 1