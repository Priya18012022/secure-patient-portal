from test.utils import get_token

def test_get_users_admin_only(client):
    token = get_token(client, "admin@example.com", "adminpass")
    response = client.get("/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
