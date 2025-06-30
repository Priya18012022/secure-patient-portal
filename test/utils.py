def get_token(client, email, password):
    response = client.post("/login", json={
        "email": email,
        "password": password
    })
    print("Login JSON:", response.json)  # ✅ Add this temporarily for debugging
    assert response.status_code == 200
    return response.json["token"]
