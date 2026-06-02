# tests/test_comments.py
def test_create_comment(client, auth_token):
    post = client.post(
        "/posts",
        json={"title": "Comment Post", "content": "Content"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert post.status_code == 200
    post_id = post.json()["id"]
    
    response = client.post(
        "/comments",
        json={"content": "Nice post!", "post_id": post_id},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert response.json()["content"] == "Nice post!"

def test_get_comments(client, auth_token):
    post = client.post(
        "/posts",
        json={"title": "Comments List", "content": "Content"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert post.status_code == 200
    post_id = post.json()["id"]
    
    client.post(
        "/comments",
        json={"content": "First", "post_id": post_id},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    client.post(
        "/comments",
        json={"content": "Second", "post_id": post_id},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    response = client.get(f"/posts/{post_id}/comments")
    assert response.status_code == 200
    assert len(response.json()) >= 2

def test_delete_own_comment(client, auth_token):
    post = client.post(
        "/posts",
        json={"title": "Delete Comment", "content": "Content"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert post.status_code == 200
    post_id = post.json()["id"]
    
    comment = client.post(
        "/comments",
        json={"content": "Delete me", "post_id": post_id},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert comment.status_code == 200
    comment_id = comment.json()["id"]
    
    response = client.delete(
        f"/comments/{comment_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200