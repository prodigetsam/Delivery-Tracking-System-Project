from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db_connection import get_db_connection
import uuid

app = Flask(__name__)
app.secret_key = "super_secret_secure_key_for_parcel_system"

# ==========================================
# 1. AUTHENTICATION & REGISTRATION
# ==========================================

@app.route("/")
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_process():
    email = request.form.get("email")
    password_raw = request.form.get("password")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True) 

    try:
        sql = "SELECT id, first_name, last_name, password, role FROM user_credentials WHERE email = %s"
        cursor.execute(sql, (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user["password"], password_raw):
            session["logged_in"] = True
            session["user_id"] = user["id"]
            session["first_name"] = user["first_name"]
            session["last_name"] = user["last_name"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("user_dashboard"))
        
        return "<script>alert('Invalid email or password.'); window.location.href='/';</script>"
    finally:
        # Using 'finally' ensures these close even if an error occurs above
        cursor.close()
        conn.close()

@app.route("/register")
def registration_page():
    return render_template("registration.html")

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
        return "<script>alert('Registration successful! You can now log in.'); window.location.href='/';</script>"
    except Exception as e:
        print(f"REGISTRATION ERROR: {e}") # Helpful for debugging
        return "<script>alert('Registration failed. Email might exist.'); window.location.href='/register';</script>"
    finally:
        cursor.close()
        conn.close()

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

# ==========================================
# 2. DASHBOARDS
# ==========================================

@app.route("/dashboard")
def user_dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))
    return render_template("user_dashboard.html")

@app.route("/admin_dashboard")
def admin_dashboard():
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect(url_for("login_page"))
    return render_template("admin_dashboard.html")

# ==========================================
# 3. USER PROFILE MANAGEMENT
# ==========================================

@app.route('/profile')
def profile():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT first_name, last_name, email FROM user_credentials WHERE id = %s", (session.get("user_id"),))
        user = cursor.fetchone()
        return render_template('profile.html', user=user)
    finally:
        cursor.close()
        conn.close()

@app.route("/update_profile", methods=["POST"])
def update_profile():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))

    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    user_id = session.get("user_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        sql = "UPDATE user_credentials SET first_name = %s, last_name = %s, email = %s WHERE id = %s"
        cursor.execute(sql, (first_name, last_name, email, user_id))
        conn.commit()

        session["first_name"] = first_name
        session["last_name"] = last_name

        return "<script>alert('Profile updated successfully.'); window.location.href='/profile';</script>"
    except Exception as e:
        print(f"PROFILE UPDATE ERROR: {e}")
        return "<script>alert('Error updating profile. The email may already be in use.'); window.location.href='/profile';</script>"
    finally:
        cursor.close()
        conn.close()

@app.route("/change_password", methods=["POST"])
def change_password():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))

    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")
    user_id = session.get("user_id")

    if new_password != confirm_password:
        return "<script>alert('New passwords do not match. Please try again.'); window.location.href='/profile';</script>"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT password FROM user_credentials WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if user and check_password_hash(user["password"], current_password):
            hashed_new_password = generate_password_hash(new_password, method="pbkdf2:sha256", salt_length=16)
            cursor.execute("UPDATE user_credentials SET password = %s WHERE id = %s", (hashed_new_password, user_id))
            conn.commit()
            return "<script>alert('Password updated successfully!'); window.location.href='/profile';</script>"
        else:
            return "<script>alert('Incorrect current password. Please try again.'); window.location.href='/profile';</script>"
    except Exception as e:
        print(f"PASSWORD CHANGE ERROR: {e}")
        return "<script>alert('An error occurred while updating the password.'); window.location.href='/profile';</script>"
    finally:
        cursor.close()
        conn.close()

# ==========================================
# 4. PARCEL SERVICES & MANAGEMENT
# ==========================================

@app.route('/parcel_services')
def parcel_services():
    return render_template('parcel_services.html')

@app.route("/request_delivery", methods=["GET", "POST"])
def request_delivery():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))

    if request.method == "POST":
        item_name = request.form.get("item_name")
        delivery_address = request.form.get("delivery_address")
        sender_id = session.get("user_id")
        tracking_number = "TRK-" + str(uuid.uuid4().hex[:8]).upper()

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            sql = "INSERT INTO parcels (item_name, tracking_number, sender_id, delivery_address) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (item_name, tracking_number, sender_id, delivery_address))
            conn.commit()

            parcel_id = cursor.lastrowid

            history_sql = "INSERT INTO tracking_history (parcel_id, status, location, remarks) VALUES (%s, %s, %s, %s)"
            cursor.execute(history_sql, (parcel_id, "On Hold", "Warehouse", "Parcel requested and pending processing."))
            conn.commit()
            
            success_message = f"Delivery requested successfully! Tracking Number: {tracking_number}"
            return f"<script>alert('{success_message}'); window.location.href='/parcel_services';</script>"
        except Exception as e:
            print(f"REQUEST DELIVERY ERROR: {e}")
            return "<script>alert('An error occurred while requesting the delivery.'); window.location.href='/request_delivery';</script>"
        finally:
            cursor.close()
            conn.close()

    return render_template("request_delivery.html")

@app.route("/manage_address", methods=["GET", "POST"])
def manage_address():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))

    user_id = session.get("user_id")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == "POST":
            address_label = request.form.get("address_label")
            full_address = request.form.get("full_address")
            sql = "INSERT INTO addresses (user_id, address_label, full_address) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user_id, address_label, full_address))
            conn.commit()
            return "<script>alert('Address saved successfully!'); window.location.href='/manage_address';</script>"

        # GET request logic
        cursor.execute("SELECT address_label, full_address FROM addresses WHERE user_id = %s", (user_id,))
        saved_addresses = cursor.fetchall()
        return render_template("manage_address.html", addresses=saved_addresses)

    except Exception as e:
        print(f"MANAGE ADDRESS ERROR: {e}")
        return "<script>alert('An error occurred with address management.'); window.location.href='/manage_address';</script>"
    finally:
        cursor.close()
        conn.close()

@app.route("/my_parcels")
def my_parcels():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        sql = "SELECT tracking_number, item_name, delivery_address, status FROM parcels WHERE sender_id = %s"
        cursor.execute(sql, (session.get("user_id"),))
        parcels = cursor.fetchall()
        return render_template("my_parcels.html", parcels=parcels)
    except Exception as e:
        print(f"MY PARCELS ERROR: {e}")
        return "<script>alert('An error occurred while fetching your parcels.'); window.location.href='/parcel_services';</script>"
    finally:
        cursor.close()
        conn.close()

# ==========================================
# 5. TRACKING
# ==========================================

@app.route('/tracking')
def tracking():
    return render_template('tracking.html')

@app.route("/track_parcel", methods=["POST"])
def track_parcel():
    parcel_id = request.form.get("parcel_id")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM parcels WHERE tracking_number = %s", (parcel_id,))
        parcel = cursor.fetchone()
        
        if parcel:
            return render_template("tracking_result.html", parcel=parcel)
        return "<script>alert('Parcel not found.'); window.location.href='/tracking';</script>"
    finally:
        cursor.close()
        conn.close()

@app.route("/parcel_history", methods=["POST"])
def parcel_history():
    parcel_id = request.form.get("parcel_id")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM tracking_history WHERE parcel_id = %s ORDER BY updated_at DESC", (parcel_id,))
        history = cursor.fetchall()
        return render_template("history_result.html", history=history, parcel_id=parcel_id)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    app.run(debug=True)