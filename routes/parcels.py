from flask import Blueprint, render_template, session
from db_connection import get_db_connection

parcels_bp = Blueprint('parcels_bp', __name__)

@parcels_bp.route('/parcel_services')
def parcel_services():
    if not session.get("logged_in"): return redirect(url_for("auth_bp.login_page"))
    return render_template('parcel_services.html')

@app.route("/request_delivery", methods=["GET", "POST"])
def request_delivery():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))

    if request.method == "POST":
        item_name = request.form.get("item_name")
        delivery_address = request.form.get("delivery_address")
        sender_id = session.get("user_id")
        
        # Generate a random 8-character tracking number
        tracking_number = "TRK-" + str(uuid.uuid4().hex[:8]).upper()

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 1. Insert the new parcel
            sql = "INSERT INTO parcels (item_name, tracking_number, sender_id, delivery_address) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (item_name, tracking_number, sender_id, delivery_address))
            conn.commit()

            # Get the ID of the parcel we just inserted
            parcel_id = cursor.lastrowid

            # 2. Insert the initial tracking history record
            history_sql = "INSERT INTO tracking_history (parcel_id, status, location, remarks) VALUES (%s, %s, %s, %s)"
            cursor.execute(history_sql, (parcel_id, "On Hold", "Warehouse", "Parcel requested and pending processing."))
            conn.commit()

            cursor.close()
            conn.close()
            
            success_message = f"Delivery requested successfully! Tracking Number: {tracking_number}"
            return f"<script>alert('{success_message}'); window.location.href='/parcel_services';</script>"

        except Exception as e:
            cursor.close()
            conn.close()
            return "<script>alert('An error occurred while requesting the delivery.'); window.location.href='/request_delivery';</script>"

    # If it's a GET request, just show the form
    return render_template("request_delivery.html")


@app.route("/manage_address", methods=["GET", "POST"])
def manage_address():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))

    user_id = session.get("user_id")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # If the user submits a new address
    if request.method == "POST":
        address_label = request.form.get("address_label")
        full_address = request.form.get("full_address")

        try:
            sql = "INSERT INTO addresses (user_id, address_label, full_address) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user_id, address_label, full_address))
            conn.commit()

            cursor.close()
            conn.close()
            return "<script>alert('Address saved successfully!'); window.location.href='/manage_address';</script>"

        except Exception as e:
            cursor.close()
            conn.close()
            print(f"DATABASE ERROR: {e}")
            return "<script>alert('An error occurred while saving the address.'); window.location.href='/manage_address';</script>"

    # If it is a GET request, fetch the user's saved addresses to display
    cursor.execute("SELECT address_label, full_address FROM addresses WHERE user_id = %s", (user_id,))
    saved_addresses = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("manage_address.html", addresses=saved_addresses)


@app.route("/my_parcels")
def my_parcels():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))

    user_id = session.get("user_id")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Assumes your table is named 'parcels' and has 'sender_id'
        sql = "SELECT tracking_number, item_name, delivery_address, status FROM parcels WHERE sender_id = %s"
        cursor.execute(sql, (user_id,))
        parcels = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template("my_parcels.html", parcels=parcels)

    except Exception as e:
        cursor.close()
        conn.close()
        print(f"DATABASE ERROR: {e}")
        return "<script>alert('An error occurred while fetching your parcels.'); window.location.href='/parcel_services';</script>"