from flask import Flask
from routes.auth import auth_bp
from routes.parcels import parcels_bp
from routes.tracking import tracking_bp

app = Flask(__name__)
app.secret_key = "super_secret_secure_key_for_parcel_system"

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(parcels_bp)
app.register_blueprint(tracking_bp)

if __name__ == "__main__":
    app.run(debug=True)