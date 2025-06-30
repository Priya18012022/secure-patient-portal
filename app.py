from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

# MySQL configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Secure@1234",  # replace with your actual password
    "database": "patient_portal"
}

@app.route("/")
def home():
    return jsonify({"message": "Secure Patient Portal API is running!"})

@app.route("/register", methods=["POST"])
def register_user():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, password)
        )
        conn.commit()
        return jsonify({"status": "success", "message": "User registered successfully!"})
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)})
    finally:
        cursor.close()
        conn.close()

@app.route("/users", methods=["GET"])
def get_users():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email FROM users")
        users = cursor.fetchall()
        return jsonify({"status": "success", "users": users})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    app.run(debug=True)
