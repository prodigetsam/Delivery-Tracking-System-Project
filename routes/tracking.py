from flask import Blueprint, render_template, redirect, url_for, session
from db_connection import get_db_connection

tracking_bp = Blueprint('tracking_bp', __name__)

@tracking_bp.route('/tracking')
def tracking():
    if not session.get("logged_in"): return redirect(url_for("auth_bp.login_page"))
    return render_template('tracking.html')

@app.route("/track_parcel", methods=["POST"])
def track_parcel():
    parcel_id = request.form.get("parcel_id")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # This remains correct because your 'parcels' table has 'tracking_number'
    cursor.execute("SELECT * FROM parcels WHERE tracking_number = %s", (parcel_id,))
    parcel = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if parcel:
        return render_template("tracking_result.html", parcel=parcel)
    else:
        return "<script>alert('Parcel not found.'); window.location.href='/tracking';</script>"

@app.route("/parcel_history", methods=["POST"])
def parcel_history():
    parcel_id = request.form.get("parcel_id")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Use 'parcel_id' to match the column name in your tracking_history table
    cursor.execute("SELECT * FROM tracking_history WHERE parcel_id = %s ORDER BY updated_at DESC", (parcel_id,))
    history = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template("history_result.html", history=history, parcel_id=parcel_id)