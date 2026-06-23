# ==========================================
# IMPORTS
# ==========================================
# Standard Library
import os
import uuid

# Third-Party Libraries
from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Local Modules
from db_connection import get_db_connection
from structures import MyQueue, StatusMapper, UserStack, BinarySearchUser, BinarySearchParcel

# ==========================================
# APP INITIALIZATION & CONFIGURATION
# ==========================================
app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem" 
Session(app)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "fallback_dev_key_change_in_production")

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ==========================================
# CUSTOM DATA STRUCTURES INITIALIZATION
# ==========================================
status_mapper = StatusMapper() 
binary_search_user = BinarySearchUser()
binary_search_parcel = BinarySearchParcel()

# ==========================================
# UTILITY FUNCTIONS
# ==========================================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def js_alert_redirect(message, url):
    return f"<script>alert('{message}'); window.location.href='{url}';</script>"

# ==========================================
# AUTHENTICATION ROUTES
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
        cursor.execute("SELECT id,first_name, last_name, password, role FROM user_credentials WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user["password"], password_raw):
            session.clear()
            session.update({
                "logged_in": True,
                "user_id": user["id"],
                "role": user["role"],
                "first_name": user["first_name"],
                "last_name": user["last_name"]
            })
            
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("user_dashboard"))
        
        return js_alert_redirect("Invalid email or password.", url_for("login_page"))
    finally:
        cursor.close()
        conn.close()

@app.route("/register", methods=["GET", "POST"])
def registration_page():
    if request.method == "POST":
        hashed_password = generate_password_hash(request.form["password"], method="pbkdf2:sha256", salt_length=16)
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 1. Insert user details
            sql = "INSERT INTO user_credentials (first_name, last_name, sex, email, password) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (
                request.form["first_name"], 
                request.form["last_name"], 
                request.form["gender"], 
                request.form["email"], 
                hashed_password
            ))
            
            # 2. Capture the newly created user's ID
            new_user_id = cursor.lastrowid
            
            # 3. Insert address into the addresses table using the new_user_id
            address_sql = "INSERT INTO addresses (user_id, address_label, full_address) VALUES (%s, %s, %s)"
            cursor.execute(address_sql, (new_user_id, request.form["address_label"], request.form["address"]))
            
            conn.commit()
            return js_alert_redirect("Registration successful! You can now log in.", url_for("login_page"))
        except Exception as e:
            conn.rollback() # Important: rollback if anything fails
            print(f"REGISTRATION ERROR: {e}") 
            return js_alert_redirect("Registration failed. Please check your details.", url_for("registration_page"))
        finally:
            cursor.close()
            conn.close()
            
    return render_template("registration.html")

@app.route("/logout")
def logout():
    session.clear()
    return js_alert_redirect("You have been logged out.", url_for("login_page"))

# ==========================================
# USER PROFILE & ACCOUNT ROUTES
# ==========================================
@app.route("/dashboard")
def user_dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))
    return render_template("user_dashboard.html")

@app.route('/profile')
def profile():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))

    user_id = session.get("user_id")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT first_name, last_name, email FROM user_credentials WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(dr.id) as total_orders, 
                   (SELECT status FROM delivery_requests WHERE user_id = %s ORDER BY id DESC LIMIT 1) as recent_status
            FROM delivery_requests dr
            WHERE dr.user_id = %s
        """, (user_id, user_id))
        activity = cursor.fetchone()

        return render_template('profile.html', user=user, activity=activity)
    finally:
        cursor.close()
        conn.close()

@app.route("/update_profile", methods=["POST"])
def update_profile():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))

    user_id = session.get("user_id")
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE user_credentials SET first_name = %s, last_name = %s, email = %s WHERE id = %s", 
            (request.form.get("first_name"), request.form.get("last_name"), request.form.get("email"), user_id)
        )
        conn.commit()
        session["first_name"] = request.form.get("first_name")
        session["last_name"] = request.form.get("last_name")
        return js_alert_redirect("Profile updated successfully.", url_for("profile"))
    except Exception as e:
        print(f"PROFILE UPDATE ERROR: {e}")
        return js_alert_redirect("Error updating profile. The email may already be in use.", url_for("profile"))
    finally:
        cursor.close()
        conn.close()

@app.route("/change_password", methods=["POST"])
def change_password():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))

    new_password = request.form.get("new_password")
    if new_password != request.form.get("confirm_password"):
        return js_alert_redirect("New passwords do not match. Please try again.", url_for("profile"))

    user_id = session.get("user_id")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT password FROM user_credentials WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if user and check_password_hash(user["password"], request.form.get("current_password")):
            hashed_new_password = generate_password_hash(new_password, method="pbkdf2:sha256", salt_length=16)
            cursor.execute("UPDATE user_credentials SET password = %s WHERE id = %s", (hashed_new_password, user_id))
            conn.commit()
            return js_alert_redirect("Password updated successfully!", url_for("profile"))
        
        return js_alert_redirect("Incorrect current password. Please try again.", url_for("profile"))
    except Exception as e:
        print(f"PASSWORD CHANGE ERROR: {e}")
        return js_alert_redirect("An error occurred while updating the password.", url_for("profile"))
    finally:
        cursor.close()
        conn.close()

@app.route("/manage_address", methods=["GET", "POST"])
def manage_address():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))

    user_id = session.get("user_id")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == "POST":
            address_label = request.form.get("address_label").strip()
            full_address = request.form.get("full_address").strip()

            cursor.execute("SELECT id FROM addresses WHERE user_id = %s LIMIT 1", (user_id,))
            
            if cursor.fetchone():
                cursor.execute("UPDATE addresses SET address_label = %s, full_address = %s WHERE user_id = %s", (address_label, full_address, user_id))
            else:
                cursor.execute("INSERT INTO addresses (user_id, address_label, full_address) VALUES (%s, %s, %s)", (user_id, address_label, full_address))

            conn.commit()
            return js_alert_redirect("Address saved successfully!", url_for("manage_address"))

        cursor.execute("SELECT address_label, full_address FROM addresses WHERE user_id = %s LIMIT 1", (user_id,))
        current_address = cursor.fetchone() or {"address_label": "", "full_address": ""}
        return render_template("manage_address.html", address=current_address)
    except Exception as e:
        print(f"MANAGE ADDRESS ERROR: {e}")
        return js_alert_redirect("An error occurred with address management.", url_for("manage_address"))
    finally:
        cursor.close()
        conn.close()

# ==========================================
# PARCEL & TRACKING ROUTES (USER)
# ==========================================
@app.route('/parcel_services')
def parcel_services():
    return render_template('parcel_services.html')

@app.route("/request_delivery", methods=["GET", "POST"])
def request_delivery():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))

    user_id = session.get("user_id")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        selected_parcel_id = request.form.get("parcel_id")
        try:
            # Fetch address ID
            cursor.execute("SELECT id FROM addresses WHERE user_id = %s LIMIT 1", (user_id,))
            address_record = cursor.fetchone()
            
            if not address_record:
                cursor.close()
                conn.close()
                return js_alert_redirect("No address configured. Please set one first.", url_for("manage_address"))
            
            selected_address_id = address_record["id"]
            new_tracking = "TRK-" + str(uuid.uuid4().hex[:8]).upper()

            cursor.execute(
                "INSERT INTO delivery_requests (parcel_id, tracking_number, status, address_id, user_id) VALUES (%s, %s, 'Pending Processing', %s, %s)", 
                (selected_parcel_id, new_tracking, selected_address_id, user_id)
            )
            
            cursor.execute(
                "INSERT INTO tracking_history (parcel_id, tracking_number, status, location, remarks) VALUES (%s, %s, %s, %s, %s)", 
                (selected_parcel_id, new_tracking, "Pending Processing", "Sorting Hub", "User requested delivery.")
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            return js_alert_redirect("Delivery request submitted successfully!", url_for("parcel_services"))
            
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            print(f"REQUEST DELIVERY ERROR: {e}")
            return js_alert_redirect("An error occurred. Please try again.", url_for("request_delivery"))
            
    else:
        # --- THIS WAS MISSING ---
        # Handle the GET request to display the form
        cursor.execute("SELECT * FROM parcels") # Adjust query as needed to show selectable parcels
        available_parcels = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template("request_delivery.html", parcels=available_parcels)
@app.route("/my_parcels")
def my_parcels():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Join addresses on the new address_id column
        cursor.execute("""
            SELECT p.item_name, p.description, p.price, p.image_filename, 
                   dr.tracking_number, dr.status, a.address_label as delivery_address 
            FROM parcels p
            JOIN delivery_requests dr ON p.id = dr.parcel_id
            JOIN addresses a ON dr.address_id = a.id
            WHERE dr.user_id = %s
            ORDER BY dr.id DESC
        """, (session.get("user_id"),))
        
        return render_template("my_parcels.html", parcels=cursor.fetchall())
    finally:
        cursor.close()
        conn.close()

@app.route('/tracking')
def tracking():
    return render_template('tracking.html')

@app.route("/track_parcel", methods=["POST"])
def track_parcel():
    tracking_number = request.form.get("tracking_number") 
    target_user_id = request.form.get("target_user_id") # Grab this first!
    
    # Check if the logged-in session is an admin
    is_admin = (session.get("role") == "admin")
    
    # Define fallback redirect destinations dynamically based on who is tracking
    if is_admin:
        if target_user_id == "global":
            fallback_url = url_for("admin_dashboard")
        elif target_user_id:
            fallback_url = url_for("user_statistics", target_user_id=target_user_id)
        else:
            fallback_url = url_for("user_management")
    else:
        fallback_url = url_for("tracking")

    if not tracking_number:
        return js_alert_redirect("Please enter a valid tracking number.", fallback_url)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT p.id as parcel_id, p.item_name, p.description, p.price, 
                   dr.tracking_number, dr.status, a.address_label as delivery_address 
            FROM delivery_requests dr
            JOIN parcels p ON dr.parcel_id = p.id
            LEFT JOIN addresses a ON dr.user_id = a.user_id
            WHERE dr.tracking_number = %s
        """, (tracking_number,))
        parcel = cursor.fetchone()
        
        if parcel:
            cursor.execute("SELECT status, location, remarks, updated_at FROM tracking_history WHERE tracking_number = %s ORDER BY id DESC", (tracking_number,))
            history = cursor.fetchall()
            
            parcel["history"] = history
            parcel["current_location"] = history[0]["location"] if history else "Sorting Hub"
            
            return render_template(
                "tracking_result.html", 
                parcel=parcel, 
                is_admin=is_admin, 
                target_user_id=target_user_id
            )
        
        # ---> FIXED: Returns the admin or user to their respective page if parcel doesn't exist <---
        return js_alert_redirect("Parcel not found. Please check the tracking number.", fallback_url)
    except Exception as e:
        print(f"TRACKING SYSTEM ERROR: {e}")
        # ---> FIXED: Returns the admin or user to their respective page if an exception is thrown <---
        return js_alert_redirect("An error occurred while retrieving tracking details.", fallback_url)
    finally:
        cursor.close()
        conn.close()

# ==========================================
# ADMIN ROUTES
# ==========================================
@app.route("/admin_dashboard")
def admin_dashboard():
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect(url_for("login_page"))
    return render_template("admin_dashboard.html")

@app.route("/admin/create_parcel", methods=["GET", "POST"])
def admin_create_parcel():
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect(url_for("login_page"))

    if request.method == "POST":
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 1. Handle the file upload segment
            image_filename = 'default_parcel.jpg'  # Fallback default if nothing is uploaded
            
            if 'parcel_image' in request.files:
                file = request.files['parcel_image']
                # If user selected a file and it has an approved extension
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    
                    # Ensure the physical storage directory exists to avoid OS write errors
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    # Save the file to static/uploads/
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    image_filename = filename

            # 2. Execute the query with the new image_filename column
            cursor.execute(
                "INSERT INTO parcels (item_name, description, price, image_filename) VALUES (%s, %s, %s, %s)", 
                (
                    request.form.get("item_name").strip(), 
                    request.form.get("description", "").strip(), 
                    request.form.get("price"),
                    image_filename
                )
            )
            conn.commit()
            return js_alert_redirect("Parcel added to inventory pool.", url_for("admin_dashboard"))
            
        except Exception as e:
            print(f"ADMIN PARCEL ENGINE ERROR: {e}")
            return js_alert_redirect("Failed to log parcel. Check your inputs.", url_for("admin_create_parcel"))
        finally:
            cursor.close()
            conn.close()

    return render_template("create_parcel.html")

@app.route("/admin/users", methods=["GET"])
def user_management():
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect(url_for("login_page"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    search_query = request.args.get("search_query", "").strip()
    searched = bool(search_query)
    search_result = None

    try:
        # Updated JOIN: Selecting a.id allows you to reference the address specifically
        cursor.execute("""
            SELECT u.id, u.first_name, u.last_name, u.sex, u.email, u.created_at, 
                   a.address_label, a.id as address_id
            FROM user_credentials u
            LEFT JOIN addresses a ON u.id = a.user_id
            WHERE u.role != 'admin' 
            ORDER BY u.id ASC
        """)
        db_users = cursor.fetchall()

        # ---> BINARY SEARCH ALGORITHM INTEGRATION <---
        if searched:
            searchable_pool = list(db_users)
            searchable_pool.sort(key=lambda x: str(x["first_name"]).lower())
            search_result = BinarySearchUser.binary_search_users(searchable_pool, search_query)

        # ---> COMPUTE AGGREGATE SUMMARY REPORTS LOGIC <---
        total_users = len(db_users)
        male_count = sum(1 for u in db_users if str(u["sex"]).lower() in ["male", "m"])
        female_count = sum(1 for u in db_users if str(u["sex"]).lower() in ["female", "f"])
        other_count = total_users - (male_count + female_count)

        user_report = {
            "total": total_users,
            "males": male_count,
            "females": female_count,
            "others": other_count
        }

        # ---> STACK IMPLEMENTATION <---
        user_stack = UserStack()
        for user in db_users:
            user_stack.push(user)

        if request.args.get("order") == "oldest":
            display_users = user_stack.reverse_order()
        else:
            display_users = user_stack.get_all()

        return render_template(
            "user_management.html", 
            users=display_users, 
            search_query=search_query, 
            searched=searched, 
            search_result=search_result,
            report=user_report
        )
    except Exception as e:
        print(f"USER MANAGEMENT ERROR: {e}")
        return js_alert_redirect("Error loading user management.", url_for("admin_dashboard"))
    finally:
        cursor.close()
        conn.close()

@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect(url_for("login_page"))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM user_credentials WHERE id = %s", (user_id,))
        conn.commit()
        return js_alert_redirect("User permanently deleted from the system.", url_for("user_management"))
    except Exception as e:
        print(f"DELETE ERROR: {e}")
        return js_alert_redirect("Failed to delete user. They might be tied to active parcels.", url_for("user_management"))
    finally:
        cursor.close()
        conn.close()

@app.route("/admin/reports")
def report_summary():
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect(url_for("login_page"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT COUNT(*) as total FROM delivery_requests")
        total_parcels = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as count FROM delivery_requests WHERE status = 'Pending Processing'")
        pending_parcels = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM delivery_requests WHERE status = 'Delivered'")
        delivered_parcels = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM delivery_requests WHERE status = 'Cancelled'")
        cancelled_parcels = cursor.fetchone()["count"]

        return render_template("report_summary.html", total_parcels=total_parcels, pending_parcels=pending_parcels, delivered_parcels=delivered_parcels, cancelled_parcels=cancelled_parcels)
    finally:
        cursor.close()
        conn.close()

@app.route("/admin/parcels", methods=["GET", "POST"])
def parcel_management():
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect(url_for("login_page"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == "POST":
            parcel_id = request.form.get("parcel_id")
            tracking_number = request.form.get("tracking_number")
            current_status = request.form.get("current_status")
            
            # ---> HASH MAP IMPLEMENTATION IN ACTION <---
            next_status = status_mapper.get_next_status(current_status)
            location = status_mapper.get_location(next_status)
            
            # Update delivery_requests status
            if tracking_number:
                cursor.execute("UPDATE delivery_requests SET status = %s WHERE tracking_number = %s", (next_status, tracking_number))
            else:
                cursor.execute("UPDATE delivery_requests SET status = %s WHERE parcel_id = %s", (next_status, parcel_id))
            
            # Insert into tracking_history
            cursor.execute(
                "INSERT INTO tracking_history (parcel_id, tracking_number, status, location, remarks) VALUES (%s, %s, %s, %s, %s)", 
                (parcel_id, tracking_number, next_status, location, "Transitioned to next stage by admin.")
            )
            
            conn.commit()
            return js_alert_redirect(f"Status moved to {next_status}.", url_for("parcel_management"))

        # GET Request: Fetch pipeline
        cursor.execute("""
            SELECT p.id as parcel_id, p.item_name, dr.tracking_number, 
                   a.address_label as delivery_address, dr.status, 
                   u.first_name, u.last_name,
                   COALESCE((SELECT th.location FROM tracking_history th 
                             WHERE th.tracking_number = dr.tracking_number 
                             ORDER BY th.id DESC LIMIT 1), 'Sorting Hub') as current_location
            FROM delivery_requests dr
            JOIN parcels p ON dr.parcel_id = p.id
            JOIN user_credentials u ON dr.user_id = u.id
            JOIN addresses a ON dr.address_id = a.id
            WHERE dr.status IN ('Pending Processing', 'In Transit', 'Out for Delivery')
        """)
        raw_pipeline = cursor.fetchall()
        
        # ---> QUEUE IMPLEMENTATION IN ACTION <---
        pipeline_queue = MyQueue()
        for item in raw_pipeline:
            pipeline_queue.enqueue(item)
            
        return render_template("parcel_management.html", pipeline=pipeline_queue.get_all())
    except Exception as e:
        conn.rollback()
        print(f"ADMIN MANAGEMENT ERROR: {e}")
        return js_alert_redirect("An error occurred while updating the pipeline.", url_for("parcel_management"))
    finally:
        cursor.close()
        conn.close()

@app.route("/admin/cancel_parcel", methods=["POST"])
def cancel_parcel():
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect(url_for("login_page"))

    parcel_id = request.form.get("parcel_id")
    tracking_number = request.form.get("tracking_number") 
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update delivery_requests to Cancelled
        cursor.execute("UPDATE delivery_requests SET status = 'Cancelled' WHERE tracking_number = %s", (tracking_number,))
        
        # Insert into tracking_history (Included parcel_id to satisfy DB schema)
        cursor.execute(
            "INSERT INTO tracking_history (parcel_id, tracking_number, status, location, remarks) VALUES (%s, %s, 'Cancelled', 'System', 'Order cancelled by admin.')", 
            (parcel_id, tracking_number)
        )
        conn.commit()
        return js_alert_redirect("Parcel order has been cancelled.", url_for("parcel_management"))
    except Exception as e:
        conn.rollback()
        print(f"CANCEL PARCEL ERROR: {e}")
        return js_alert_redirect("Error cancelling parcel.", url_for("parcel_management"))
    finally:
        cursor.close()
        conn.close()

@app.route("/admin/user_statistics/<int:target_user_id>", methods=["GET"])
def user_statistics(target_user_id):
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect(url_for("login_page"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Fetch targeted user profile details
        cursor.execute("SELECT id, first_name, last_name, email, sex FROM user_credentials WHERE id = %s", (target_user_id,))
        user_profile = cursor.fetchone()
        
        if not user_profile:
            return js_alert_redirect("User profile not found.", url_for("user_management"))

        # 2. Extract every parcel transaction linked to this customer account, pulling the clean label address
        cursor.execute("""
            SELECT d.tracking_number, d.status, a.address_label AS delivery_address, p.item_name, p.price 
            FROM delivery_requests d
            JOIN parcels p ON d.parcel_id = p.id
            LEFT JOIN addresses a ON d.user_id = a.user_id
            WHERE d.user_id = %s
        """, (target_user_id,))
        user_history = cursor.fetchall()

        # 3. COMPUTE STATISTICS DIRECTLY IN-LINE (No extra class needed)
        total_parcels = len(user_history)
        total_spent = 0.0
        status_counts = {}

        for request in user_history:
            # Aggregate expenditures safely by casting price to a float
            price_val = request.get("price")
            if price_val is not None:
                try:
                    total_spent += float(price_val)
                except ValueError:
                    pass
            
            # Count status distributions dynamically
            status = request.get("status", "Unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        # Package the statistics up into a clean dictionary for the template
        stats_summary = {
            "total_parcels": total_parcels,
            "total_spent": total_spent,
            "status_breakdown": status_counts
        }

        return render_template(
            "user_statistics.html",
            profile=user_profile,
            history=user_history,
            stats=stats_summary
        )
    except Exception as e:
        print(f"ANALYTICS ENGINE ERROR: {e}")
        return js_alert_redirect("Error processing profile analytics.", url_for("user_management"))
    finally:
        cursor.close()
        conn.close()

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    app.run(debug=True)