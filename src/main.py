import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
import re
from src.models.user import db
# Training plan models will be imported by the routes that use them
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.rides import rides_bp
from src.routes.dashboard import dashboard_bp
from src.routes.coaching import coaching_bp
from src.routes.upload import upload_bp
from src.routes.analytics import analytics_bp
# from src.routes.strava import strava_bp
# from src.routes.training_plans import training_plans_bp  # Disabled due to SQLAlchemy registry conflict

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes with credentials support
# Allow localhost and all Vercel deployments using regex pattern
CORS(app, 
     supports_credentials=True, 
     origins=r'https://ai-cycling-dashboard.*\.vercel\.app|http://localhost:517[34]',
     allow_headers=['Content-Type'],
     expose_headers=['*'])

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(rides_bp, url_prefix='/api')
app.register_blueprint(dashboard_bp, url_prefix='/api')
app.register_blueprint(coaching_bp, url_prefix='/api')
app.register_blueprint(upload_bp, url_prefix='/api')
app.register_blueprint(analytics_bp, url_prefix='/api')
# app.register_blueprint(strava_bp, url_prefix='/api/strava')
# app.register_blueprint(training_plans_bp, url_prefix='/api/training-plans')  # Disabled due to SQLAlchemy registry conflict

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # Import base models only - training_plan models will be imported through routes
    from src.models.user import User
    from src.models.ride import Ride
    from src.models.strava_token import StravaToken
    from src.models.chat_message import ChatMessage
    from src.models.client_profile import ClientProfile
    
    db.create_all()
    
    # Auto-initialize demo accounts if database is empty
    if User.query.count() == 0:
        print("Database is empty. Initializing demo accounts...")
        try:
            from src.utils.setup_accounts_v2 import main as setup_main
            setup_main()
            print("Demo accounts created successfully!")
        except Exception as e:
            print(f"Warning: Could not create demo accounts: {e}")

@app.route('/api/health')
def health():
    from flask import jsonify
    return jsonify({'status': 'ok'}), 200

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
