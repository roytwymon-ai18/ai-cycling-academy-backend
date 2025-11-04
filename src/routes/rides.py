from flask import Blueprint, request, jsonify, session
from src.models.user import User, db
from src.models.ride import Ride
from src.utils.ai_analysis import analyze_ride_with_ai
from datetime import datetime, timedelta
import json

rides_bp = Blueprint('rides', __name__)

def require_auth():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

@rides_bp.route('/rides', methods=['GET'])
def get_rides():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get query parameters
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    rides = Ride.query.filter(
        Ride.user_id == user.id,
        Ride.date >= start_date
    ).order_by(Ride.date.desc()).all()
    
    return jsonify({
        'rides': [ride.to_dict() for ride in rides],
        'total': len(rides)
    }), 200

@rides_bp.route('/rides', methods=['POST'])
def upload_ride():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    
    # Create new ride
    ride = Ride(
        user_id=user.id,
        name=data.get('name', 'Untitled Ride'),
        date=datetime.fromisoformat(data.get('date', datetime.utcnow().isoformat())),
        duration=data.get('duration', 0),
        distance=data.get('distance', 0),
        avg_power=data.get('avg_power'),
        max_power=data.get('max_power'),
        normalized_power=data.get('normalized_power'),
        ftp=data.get('ftp', user.current_ftp),
        intensity_factor=data.get('intensity_factor'),
        training_stress_score=data.get('training_stress_score'),
        avg_heart_rate=data.get('avg_heart_rate'),
        max_heart_rate=data.get('max_heart_rate'),
        avg_speed=data.get('avg_speed'),
        max_speed=data.get('max_speed'),
        avg_cadence=data.get('avg_cadence'),
        elevation_gain=data.get('elevation_gain'),
        time_in_zone_1=data.get('time_in_zone_1', 0),
        time_in_zone_2=data.get('time_in_zone_2', 0),
        time_in_zone_3=data.get('time_in_zone_3', 0),
        time_in_zone_4=data.get('time_in_zone_4', 0),
        time_in_zone_5=data.get('time_in_zone_5', 0),
        time_in_zone_6=data.get('time_in_zone_6', 0),
        time_in_zone_7=data.get('time_in_zone_7', 0)
    )
    
    db.session.add(ride)
    db.session.commit()
    
    # Automatically analyze with AI
    try:
        analysis_result = analyze_ride_with_ai(ride)
        ride.ai_analysis = json.dumps(analysis_result.get('analysis', {}))
        ride.ai_recommendations = analysis_result.get('recommendations', '')
        ride.analyzed_at = datetime.utcnow()
        db.session.commit()
    except Exception as e:
        print(f"AI analysis failed: {e}")
    
    return jsonify({
        'message': 'Ride uploaded successfully',
        'ride': ride.to_dict()
    }), 201

@rides_bp.route('/rides/<int:ride_id>', methods=['GET'])
def get_ride(ride_id):
    user = require_auth()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    ride = Ride.query.filter_by(id=ride_id, user_id=user.id).first()
    if not ride:
        return jsonify({'error': 'Ride not found'}), 404
    
    return jsonify({'ride': ride.to_dict()}), 200

@rides_bp.route('/rides/<int:ride_id>/analyze', methods=['POST'])
def analyze_ride(ride_id):
    user = require_auth()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    ride = Ride.query.filter_by(id=ride_id, user_id=user.id).first()
    if not ride:
        return jsonify({'error': 'Ride not found'}), 404
    
    try:
        analysis_result = analyze_ride_with_ai(ride)
        ride.ai_analysis = json.dumps(analysis_result.get('analysis', {}))
        ride.ai_recommendations = analysis_result.get('recommendations', '')
        ride.analyzed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Analysis completed',
            'analysis': analysis_result
        }), 200
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

