from test.utils import get_token

def test_add_patient(client):
    token = get_token(client, "admin@example.com", "adminpass")
    response = client.post(
        "/patients",
        json={"name": "Jane Doe", "age": 28, "gender": "Female"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in [201, 400]

def test_get_patients(client):
    token = get_token(client, "admin@example.com", "adminpass")
    response = client.get(
        "/patients",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
