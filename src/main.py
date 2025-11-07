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
from src.routes.admin import admin_bp
from src.routes.strava import strava_bp
from src.routes.training_plan import training_plan_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')

# Session cookie configuration for cross-origin requests
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True  # Required for SameSite=None
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Enable CORS for all routes with credentials support
# Allow localhost and all Vercel deployments using regex pattern
CORS(app, 
     supports_credentials=True, 
     origins=r'https://aicyclingacademy\.app|https://www\.aicyclingacademy\.app|https://ai-cycling-dashboard.*\.vercel\.app|http://localhost:517[34]',
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
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(strava_bp, url_prefix='/api/strava')
app.register_blueprint(training_plan_bp, url_prefix='/api')

# Database configuration
# Use DATABASE_URL from environment (PostgreSQL on Render), fallback to SQLite for local dev
database_url = os.getenv('DATABASE_URL')
if database_url:
    # Render PostgreSQL URLs start with postgres://, but SQLAlchemy requires postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Fallback to SQLite for local development
    db_path = '/data/app.db' if os.path.exists('/data') else os.path.join(os.path.dirname(__file__), 'database', 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
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

@app.route('/api/test/profiles')
def test_profiles():
    """Diagnostic endpoint to check all client profiles"""
    from flask import jsonify
    from src.models.client_profile import ClientProfile
    
    try:
        profiles = ClientProfile.query.all()
        return jsonify({
            'success': True,
            'count': len(profiles),
            'profiles': [{
                'id': p.id,
                'user_id': p.user_id,
                'onboarding_completed': p.onboarding_completed,
                'onboarding_step': p.onboarding_step,
                'created_at': p.created_at.isoformat() if p.created_at else None
            } for p in profiles]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test/db-write')
def test_db_write():
    """Test endpoint to verify database writes are persisting"""
    from flask import jsonify
    import os
    from datetime import datetime
    
    try:
        # Check if database file exists
        db_path = '/data/app.db' if os.path.exists('/data') else os.path.join(os.path.dirname(__file__), 'database', 'app.db')
        db_exists = os.path.exists(db_path)
        db_writable = os.access(os.path.dirname(db_path), os.W_OK) if os.path.exists(os.path.dirname(db_path)) else False
        
        # Try to create a test user
        test_username = f"test_{int(datetime.utcnow().timestamp())}"
        test_user = User(username=test_username, email=f"{test_username}@test.com", password_hash="test")
        db.session.add(test_user)
        db.session.commit()
        
        # Verify it was saved
        found_user = User.query.filter_by(username=test_username).first()
        
        # Clean up test user
        if found_user:
            db.session.delete(found_user)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'db_path': db_path,
            'db_exists': db_exists,
            'db_writable': db_writable,
            'write_success': True,
            'read_success': found_user is not None,
            'test_username': test_username
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'db_path': db_path,
            'db_exists': db_exists,
            'db_writable': db_writable
        }), 500

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
