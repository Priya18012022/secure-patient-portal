import pytest
from app import app, mysql

@pytest.fixture(scope="function")
def client():
    app.config["TESTING"] = True
    client = app.test_client()

    # Clean DB before each test
    with app.app_context():
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM medical_records")
        cursor.execute("DELETE FROM patients")
        cursor.execute("DELETE FROM users")
        mysql.connection.commit()
        cursor.close()

    yield client

    # Optional: cleanup after test
