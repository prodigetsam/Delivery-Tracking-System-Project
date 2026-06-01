
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from db_connection import get_db_connection

app = Flask(__name__)

# This encrypts your session variables for tracking if login or not
app.secret_key = "super_secret_secure_key_for_parcel_system"

# Displays your Login Page
@app.route("/")
def login_page():
    return render_template("login.html")

# 2. LOGIN PROCESSING: Handles the data submission from login form
@app.route("/login", methods=["POST"])
def login_process():
    email = request.form.get("email")
    password_raw = request.form.get("password")

    conn = get_db_connection()
    # FIXED: Added buffered=True to clear the MySQL stream immediately
    cursor = conn.cursor(dictionary=True, buffered=True) 

    sql = "SELECT id, first_name, last_name, password, role FROM user_credentials WHERE email = %s"
    cursor.execute(sql, (email,))
    user = cursor.fetchone()

    # Clean up the database connection immediately after fetching
    cursor.close()
    conn.close()

    if user and check_password_hash(user["password"], password_raw):
        session["logged_in"] = True
        session["user_id"] = user["id"]
        session["first_name"] = user["first_name"]
        session["last_name"] = user["last_name"]
        session["role"] = user["role"]

        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("user_dashboard"))
        
    return "<script>alert('Invalid email or password.'); window.location.href='/';</script>"

# 3. REGISTRATION VIEW: Shows signup interface
@app.route("/register")
def registration_page():
    return render_template("registration.html")

# 4. REGISTRATION PROCESSING: Creates new account hashes inside database
@app.route("/registration", methods=["POST"])
def register():
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    gender = request.form["gender"]
    email = request.form["email"]
    password_raw = request.form["password"]

    hashed_password = generate_password_hash(password_raw, method="pbkdf2:sha256", salt_length=16)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        sql = """
        INSERT INTO user_credentials (first_name, last_name, sex, email, password)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (first_name, last_name, gender, email, hashed_password))
        conn.commit()
        cursor.close()
        conn.close()
        return "<script>alert('Registration successful! You can now log in.'); window.location.href='/';</script>"
    except Exception as e:
        cursor.close()
        conn.close()
        return "<script>alert('Registration failed. Email might exist.'); window.location.href='/register';</script>"

# 5. USER DASHBOARD VIEW
@app.route("/dashboard")
def user_dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))
    return render_template("user_dashboard.html")

# 6. ADMIN DASHBOARD VIEW
@app.route("/admin_dashboard")
def admin_dashboard():
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect(url_for("login_page"))
    return render_template("admin_dashboard.html")

# 7. LOGOUT FUNCTION
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

if __name__ == "__main__":
    app.run(debug=True)