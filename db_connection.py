import mysql.connector

def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",      # Put your MySQL password here
        database="delivery_tracking_system"
    )
    return conn