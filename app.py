from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from datetime import timedelta
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template


# Initialize Flask app
app = Flask(__name__)
CORS(app)

# JWT Config
app.config['JWT_SECRET_KEY'] = 'your_secret_key_here'  # Replace with strong secret key
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=30)

jwt = JWTManager(app)

# MySQL configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Secure@1234",  # Change to your DB password
    "database": "patient_portal"
}
@app.route("/ui")
def serve_ui():
    return render_template("index.html")
# Home route
@app.route("/")
def home():
    return jsonify({"message": "Secure Patient Portal API is running!"})

# Register route
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not all([name, email, password]):
        return jsonify({"status": "error", "message": "All fields are required"}), 400

    hashed_password = generate_password_hash(password)

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                       (name, email, hashed_password))
        conn.commit()
        return jsonify({"status": "success", "message": "User registered successfully"})
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# Login route
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"status": "error", "message": "Email and password are required"}), 400

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user["password"], password):
            user_id = str(user["id"])  # <-- Fix: define user_id before using
            access_token = create_access_token(identity=user_id)
            return jsonify({"status": "success", "token": access_token}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid email or password"}), 401

    except mysql.connector.Error as db_err:
        return jsonify({"status": "error", "message": f"Database error: {str(db_err)}"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": f"Unexpected error: {str(e)}"}), 500

    finally:
        if conn:
            cursor.close()
            conn.close()

# Protected route: Dashboard
@app.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    try:
        user_id = get_jwt_identity()
        return jsonify(message="Welcome to your dashboard!", user_id=user_id), 200
    except Exception as e:
        return jsonify(message=f"Unexpected error: {str(e)}", status="error"), 500

# Protected route: Get all users
@app.route("/users", methods=["GET"])
@jwt_required()
def get_users():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email FROM users")
        users = cursor.fetchall()
        return jsonify({"status": "success", "users": users})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Add a new patient (protected route)
@app.route("/patients", methods=["POST"])
@jwt_required()
def add_patient():
    try:
        data = request.get_json()
        name = data.get("name")
        age = data.get("age")
        gender = data.get("gender")
        contact = data.get("contact")

        if not name:
            return jsonify({"status": "error", "message": "Patient name is required"}), 400

        created_by = get_jwt_identity()  # User ID from token

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO patients (name, age, gender, contact, created_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, age, gender, contact, created_by))
        conn.commit()

        return jsonify({"status": "success", "message": "Patient added successfully"}), 201

    except mysql.connector.Error as db_err:
        return jsonify({"status": "error", "message": f"Database error: {str(db_err)}"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": f"Unexpected error: {str(e)}"}), 500

    finally:
        cursor.close()
        conn.close()


# Get all patients (protected route)
@app.route("/patients", methods=["GET"])
@jwt_required()
def get_patients():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM patients")  # Ensure this table exists
        patients = cursor.fetchall()
        return jsonify({"status": "success", "patients": patients})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# GET single patient by ID
@app.route("/patients/<int:patient_id>", methods=["GET"])
@jwt_required()
def get_patient(patient_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
        patient = cursor.fetchone()
        if not patient:
            return jsonify({"status": "error", "message": "Patient not found"}), 404
        return jsonify({"status": "success", "patient": patient}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# UPDATE patient by ID
@app.route("/patients/<int:patient_id>", methods=["PUT"])
@jwt_required()
def update_patient(patient_id):
    data = request.get_json()
    name = data.get("name")
    age = data.get("age")
    gender = data.get("gender")
    contact = data.get("contact")

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE patients 
            SET name = %s, age = %s, gender = %s, contact = %s 
            WHERE id = %s
        """, (name, age, gender, contact, patient_id))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"status": "error", "message": "Patient not found"}), 404

        return jsonify({"status": "success", "message": "Patient updated successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# DELETE patient by ID
@app.route("/patients/<int:patient_id>", methods=["DELETE"])
@jwt_required()
def delete_patient(patient_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM patients WHERE id = %s", (patient_id,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"status": "error", "message": "Patient not found"}), 404

        return jsonify({"status": "success", "message": "Patient deleted successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

from datetime import datetime

# Create medical record for a patient
@app.route("/patients/<int:patient_id>/records", methods=["POST"])
@jwt_required()
def add_medical_record(patient_id):
    data = request.get_json()
    diagnosis = data.get("diagnosis")
    treatment = data.get("treatment")
    doctor = data.get("doctor")
    date_str = data.get("date")  # Expected format: YYYY-MM-DD

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO medical_records (patient_id, diagnosis, treatment, doctor, date)
            VALUES (%s, %s, %s, %s, %s)
        """, (patient_id, diagnosis, treatment, doctor, date))
        conn.commit()
        return jsonify({"status": "success", "message": "Medical record added"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Get all medical records for a patient
@app.route("/patients/<int:patient_id>/records", methods=["GET"])
@jwt_required()
def get_medical_records(patient_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM medical_records WHERE patient_id = %s", (patient_id,))
        records = cursor.fetchall()
        return jsonify({"status": "success", "records": records}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Update a medical record
@app.route("/patients/<int:patient_id>/records", methods=["POST"])
@jwt_required()
def create_medical_record(patient_id):  # <-- renamed from add_medical_record
    conn = None
    cursor = None
    try:
        data = request.get_json()
        diagnosis = data.get("diagnosis")
        treatment = data.get("treatment")
        record_date = data.get("record_date")

        if not all([diagnosis, treatment, record_date]):
            return jsonify({"status": "error", "message": "All fields are required"}), 400

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO medical_records (patient_id, diagnosis, treatment, record_date) VALUES (%s, %s, %s, %s)",
            (patient_id, diagnosis, treatment, record_date)
        )
        conn.commit()
        return jsonify({"status": "success", "message": "Medical record added"}), 201

    except mysql.connector.Error as db_err:
        return jsonify({"status": "error", "message": str(db_err)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Delete a medical record
@app.route("/records/<int:record_id>", methods=["DELETE"])
@jwt_required()
def delete_medical_record(record_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM medical_records WHERE id = %s", (record_id,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"status": "error", "message": "Record not found"}), 404

        return jsonify({"status": "success", "message": "Record deleted"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
