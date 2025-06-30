from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from datetime import timedelta
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = 'your_secret_key_here'  # Change to a strong key
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=30)
jwt = JWTManager(app)

# MySQL Configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Secure@1234",
    "database": "patient_portal"
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# -------------------- Routes --------------------

@app.route("/")
def home():
    return jsonify({"message": "Secure Patient Portal API is running!"})

@app.route("/add_record_form")
def show_add_record_form():
    return render_template('add_record.html')

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
        conn = get_db_connection()
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

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password are required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user["password"], password):
            access_token = create_access_token(identity=str(user["id"]))
            return jsonify({"status": "success", "token": access_token}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid credentials"}), 401

    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    user_id = get_jwt_identity()
    return jsonify({"message": "Welcome to your dashboard!", "user_id": user_id}), 200

@app.route("/users", methods=["GET"])
@jwt_required()
def get_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email FROM users")
        users = cursor.fetchall()
        return jsonify({"status": "success", "users": users})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/patients", methods=["POST"])
@jwt_required()
def add_patient():
    user_id = get_jwt_identity()
    data = request.get_json()
    name = data.get("name")
    age = data.get("age")
    gender = data.get("gender")

    if not all([name, age, gender]):
        return jsonify({"status": "error", "message": "All fields are required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO patients (name, age, gender, created_by) VALUES (%s, %s, %s, %s)",
            (name, age, gender, user_id)
        )
        conn.commit()
        return jsonify({"status": "success", "message": "Patient added successfully"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/patients", methods=["GET"])
@jwt_required()
def get_patients():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, age, gender, created_at FROM patients")
        patients = cursor.fetchall()
        return jsonify({"status": "success", "patients": patients}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/add_medical_record', methods=['POST'])
def add_medical_record():
    try:
        if request.content_type != 'application/json':
            return jsonify({"error": "Content-Type must be application/json"}), 415

        data = request.get_json()

        # Extract fields
        patient_id = data.get('patient_id')
        diagnosis = data.get('diagnosis')
        prescription = data.get('prescription')
        doctor_name = data.get('doctor_name')
        visit_date = data.get('visit_date')

        if not all([patient_id, diagnosis, prescription, doctor_name, visit_date]):
            return jsonify({"error": "Missing required fields"}), 400

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        sql = """
            INSERT INTO medical_records 
            (patient_id, diagnosis, prescription, doctor_name, visit_date)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (patient_id, diagnosis, prescription, doctor_name, visit_date))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Medical record added successfully"}), 201

    except Exception as e:
        print("🚨 Error in /add_medical_record:", e)  # DEBUG print
        return jsonify({"error": str(e)}), 500

@app.route('/view_records')
def view_medical_records():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT mr.id, p.name AS patient_name, mr.diagnosis, mr.prescription,
                   mr.doctor_name, mr.visit_date
            FROM medical_records mr
            JOIN patients p ON mr.patient_id = p.id
            ORDER BY mr.visit_date DESC
        """)
        records = cursor.fetchall()
        return render_template('view_records.html', records=records)
    except Exception as e:
        return f"<h2>Error: {str(e)}</h2>", 500
    finally:
        cursor.close()
        conn.close()


# -------------------- Run App --------------------
if __name__ == "__main__":
    app.run(debug=True)
