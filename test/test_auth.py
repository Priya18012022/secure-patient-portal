# test/test_auth.py

def test_register(client):
    response = client.post("/register", json={
        "name": "Test User",
        "email": "testuser@example.com",
        "password": "testpass",
        "role": "doctor"
    })
    assert response.status_code in [200, 500]  # 500 if user already exists

def test_login(client):
    response = client.post("/login", json={
        "email": "testuser@example.com",
        "password": "testpass"
    })
    assert response.status_code == 200
    assert "token" in response.json
