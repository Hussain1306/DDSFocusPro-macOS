from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
from moduller.veritabani_yoneticisi import VeritabaniYoneticisi

# --- Configuration ---
load_dotenv()
app = Flask(__name__)

# --- Database Connection Check ---
@app.route('/check-db-connection', methods=['GET'])
def check_db_connection():
    """Check if the database connection is successful and return the result."""
    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    port = int(os.getenv("DB_PORT"))

    # Initialize the VeritabaniYoneticisi object and try to connect
    veritabani = VeritabaniYoneticisi(db_host, db_user, db_password, db_name, port)
    veritabani.baglanti_olustur()

    # Check if the database connection is active
    if veritabani.baglanti_testi():
        return jsonify({"status": "success", "message": " "})
    else:
        return jsonify({"status": "error", "message": "Database connection failed. main"})

# --- Fetch Data from tblstaff ---
@app.route('/get-staff-data', methods=['GET'])
def get_staff_data():
    """Fetch and show all data from the tblstaff table"""
    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    port = int(os.getenv("DB_PORT"))

    # Initialize the VeritabaniYoneticisi object and try to connect
    veritabani = VeritabaniYoneticisi(db_host, db_user, db_password, db_name, port)
    veritabani.baglanti_olustur()

    # Query to get all data from the tblstaff table
    query = "SELECT * FROM tblstaff"
    staff_data = veritabani.sorgu_calistir(query)

    if staff_data:
        # Print all staff data in the terminal
        print("Staff Data from tblstaff table:")
        for staff in staff_data:
            print(f"Staff ID: {staff.get('staffid')}")
            print(f"Name: {staff.get('full_name')}")
            print(f"Email: {staff.get('email')}")
            print(f"Position: {staff.get('position')}")
            print(f"Status: {staff.get('status')}")
            print("-" * 30)

        # Returning the staff data in JSON response
        return jsonify({"status": "success", "staff_data": staff_data})
    else:
        return jsonify({"status": "error", "message": "No staff data found."})




# --- Routes ---
@app.route('/')
def index():
    """Render the login page when the root route is accessed"""
    return render_template('login.html')

# --- Client Page ---
@app.route('/client')
def client():
    """Render the client page after successful login"""
    return render_template('client.html')  # This will render client.html from the templates folder


if __name__ == '__main__':
    # Run the app
    print("[INFO] Flask application is starting...")
    app.run(debug=True)

