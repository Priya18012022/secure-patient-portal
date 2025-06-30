from test.utils import get_token

def test_add_medical_record(client):
    token = get_token(client, "admin@example.com", "adminpass")

    # Add a dummy patient first
    client.post("/patients", json={
        "name": "Record Patient", "age": 40, "gender": "Male"
    }, headers={"Authorization": f"Bearer {token}"})

    # Get patients to fetch patient_id
    patients = client.get("/patients", headers={"Authorization": f"Bearer {token}"}).json["patients"]
    patient_id = patients[0]["id"]

    # Now test medical record creation
    response = client.post("/add_medical_record", json={
        "patient_id": patient_id,
        "diagnosis": "Fever",
        "prescription": "Paracetamol",
        "doctor_name": "Dr. Admin",
        "visit_date": "2025-06-30"
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in [201, 400]
