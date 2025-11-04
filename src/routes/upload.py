"""
Upload routes for handling ride file uploads
"""
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
from src.models.user import db
from src.models.ride import Ride
from src.utils.file_parser import RideFileParser
from src.utils.ai_analysis import analyze_ride_with_ai

upload_bp = Blueprint('upload', __name__)

# Configure upload settings
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'fit', 'gpx', 'tcx'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@upload_bp.route('/upload', methods=['POST'])
def upload_ride():
    """Handle ride file upload"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Check if file is selected
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check if file type is allowed
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: .fit, .gpx, .tcx'}), 400
    
    try:
        # Save file temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        # Parse the file
        parser = RideFileParser(file_path)
        ride_data = parser.parse()
        
        # Get user's FTP for TSS calculation
        from src.models.user import User
        user = User.query.get(session['user_id'])
        
        # Calculate TSS if power data is available
        if ride_data['avg_power'] > 0 and user.current_ftp > 0:
            ride_data['tss'] = RideFileParser.calculate_tss(
                ride_data['duration'],
                ride_data['avg_power'],
                user.current_ftp
            )
        
        # Create ride record in database
        ride = Ride(
            user_id=session['user_id'],
            name=ride_data['name'],
            date=ride_data['date'] or datetime.now(),
            distance=ride_data['distance'],
            duration=ride_data['duration'] * 60,  # Convert minutes to seconds
            elevation_gain=ride_data['elevation_gain'],
            avg_power=ride_data['avg_power'],
            avg_heart_rate=ride_data['avg_heart_rate'],
            avg_cadence=ride_data['avg_cadence'],
            max_speed=ride_data['max_speed'],
            training_stress_score=ride_data.get('tss', 0),
            ftp=user.current_ftp,
            file_path=file_path
        )
        
        db.session.add(ride)
        db.session.commit()
        
        # Generate simple AI analysis summary
        analysis_text = f"Great ride! You covered {ride.distance:.1f}km in {ride.duration // 60} minutes"
        if ride.avg_power > 0:
            analysis_text += f" with an average power of {ride.avg_power}W"
        if ride.training_stress_score > 0:
            analysis_text += f" (TSS: {ride.training_stress_score:.0f})"
        analysis_text += ". Keep up the good work!"
        
        ride.ai_analysis = analysis_text
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Ride uploaded successfully',
            'ride': {
                'id': ride.id,
                'name': ride.name,
                'date': ride.date.isoformat(),
                'distance': ride.distance,
                'duration': ride.duration,
                'elevation_gain': ride.elevation_gain,
                'avg_power': ride.avg_power,
                'avg_heart_rate': ride.avg_heart_rate,
                'tss': ride.training_stress_score,
                'ai_analysis': ride.ai_analysis
            }
        }), 200
        
    except Exception as e:
        # Clean up file if processing failed
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return jsonify({
            'error': f'Failed to process file: {str(e)}'
        }), 500


@upload_bp.route('/upload/preview', methods=['POST'])
def preview_ride():
    """Preview ride data before uploading"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        # Save file temporarily for preview
        filename = secure_filename(file.filename)
        temp_path = os.path.join(UPLOAD_FOLDER, f"preview_{filename}")
        file.save(temp_path)
        
        # Parse the file
        parser = RideFileParser(temp_path)
        ride_data = parser.parse()
        
        # Clean up temporary file
        os.remove(temp_path)
        
        # Return preview data
        return jsonify({
            'success': True,
            'preview': {
                'name': ride_data['name'],
                'date': ride_data['date'].isoformat() if ride_data['date'] else None,
                'distance': ride_data['distance'],
                'duration': ride_data['duration'],
                'elevation_gain': ride_data['elevation_gain'],
                'avg_power': ride_data['avg_power'],
                'avg_heart_rate': ride_data['avg_heart_rate'],
                'avg_cadence': ride_data['avg_cadence'],
                'max_speed': ride_data['max_speed'],
                'data_points_count': len(ride_data['data_points'])
            }
        }), 200
        
    except Exception as e:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return jsonify({
            'error': f'Failed to preview file: {str(e)}'
        }), 500

