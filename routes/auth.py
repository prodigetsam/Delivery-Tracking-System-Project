from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from db_connection import get_db_connection

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route("/", methods=["GET"])
def login_page():
    return render_template("login.html")

@auth_bp.route("/login", methods=["POST"])
def login_process():
    email = request.form.get("email")
    password_raw = request.form.get("password")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor.execute("SELECT id, first_name, last_name, password, role FROM user_credentials WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and check_password_hash(user["password"], password_raw):
        session.update({"logged_in": True, "user_id": user["id"], "first_name": user["first_name"], "last_name": user["last_name"], "role": user["role"]})
        return redirect(url_for("auth_bp.admin_dashboard" if user["role"] == "admin" else "auth_bp.user_dashboard"))
    return "<script>alert('Invalid email or password.'); window.location.href='/';</script>"

@auth_bp.route("/register")
def registration_page(): return render_template("registration.html")

@auth_bp.route("/registration", methods=["POST"])
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

@auth_bp.route("/dashboard")
def user_dashboard():
    if not session.get("logged_in"): return redirect(url_for("auth_bp.login_page"))
    return render_template("user_dashboard.html")

@auth_bp.route("/admin_dashboard")
def admin_dashboard():
    if not session.get("logged_in") or session.get("role") != "admin": return redirect(url_for("auth_bp.login_page"))
    return render_template("admin_dashboard.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth_bp.login_page"))

@auth_bp.route('/profile')
def profile():
    if not session.get("logged_in"): return redirect(url_for("auth_bp.login_page"))
    return render_template('profile.html')