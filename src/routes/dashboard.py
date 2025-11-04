from flask import Blueprint, request, jsonify, session
from src.models.user import User, db
from src.models.ride import Ride
from datetime import datetime, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

def require_auth():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

@dashboard_bp.route('/dashboard/summary', methods=['GET'])
def get_dashboard_summary():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get query parameters
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get rides in period
    rides = Ride.query.filter(
        Ride.user_id == user.id,
        Ride.date >= start_date
    ).all()
    
    if not rides:
        return jsonify({
            'summary': {
                'total_rides': 0,
                'total_distance': 0,
                'total_time': 0,
                'avg_power': 0,
                'avg_speed': 0,
                'total_elevation': 0,
                'total_tss': 0,
                'current_ftp': user.current_ftp or 0
            },
            'recent_rides': [],
            'power_zones': {},
            'trends': {}
        }), 200
    
    # Calculate summary statistics
    total_rides = len(rides)
    total_distance = sum(ride.distance for ride in rides if ride.distance)
    total_time = sum(ride.duration for ride in rides if ride.duration)
    avg_power = sum(ride.avg_power for ride in rides if ride.avg_power) / len([r for r in rides if r.avg_power]) if any(r.avg_power for r in rides) else 0
    avg_speed = sum(ride.avg_speed for ride in rides if ride.avg_speed) / len([r for r in rides if r.avg_speed]) if any(r.avg_speed for r in rides) else 0
    total_elevation = sum(ride.elevation_gain for ride in rides if ride.elevation_gain)
    total_tss = sum(ride.training_stress_score for ride in rides if ride.training_stress_score)
    
    # Power zone distribution
    total_zone_time = {
        'zone_1': sum(ride.time_in_zone_1 for ride in rides if ride.time_in_zone_1),
        'zone_2': sum(ride.time_in_zone_2 for ride in rides if ride.time_in_zone_2),
        'zone_3': sum(ride.time_in_zone_3 for ride in rides if ride.time_in_zone_3),
        'zone_4': sum(ride.time_in_zone_4 for ride in rides if ride.time_in_zone_4),
        'zone_5': sum(ride.time_in_zone_5 for ride in rides if ride.time_in_zone_5),
        'zone_6': sum(ride.time_in_zone_6 for ride in rides if ride.time_in_zone_6),
        'zone_7': sum(ride.time_in_zone_7 for ride in rides if ride.time_in_zone_7)
    }
    
    # Recent rides (last 5)
    recent_rides = sorted(rides, key=lambda x: x.date, reverse=True)[:5]
    
    # Weekly trends
    weeks = {}
    for ride in rides:
        week_start = ride.date - timedelta(days=ride.date.weekday())
        week_key = week_start.strftime('%Y-%m-%d')
        if week_key not in weeks:
            weeks[week_key] = {'distance': 0, 'time': 0, 'tss': 0, 'rides': 0}
        weeks[week_key]['distance'] += ride.distance or 0
        weeks[week_key]['time'] += ride.duration or 0
        weeks[week_key]['tss'] += ride.training_stress_score or 0
        weeks[week_key]['rides'] += 1
    
    return jsonify({
        'summary': {
            'total_rides': total_rides,
            'total_distance': round(total_distance, 1),
            'total_time': total_time,
            'avg_power': round(avg_power, 0),
            'avg_speed': round(avg_speed, 1),
            'total_elevation': round(total_elevation, 0),
            'total_tss': round(total_tss, 0),
            'current_ftp': user.current_ftp or 0
        },
        'recent_rides': [ride.to_dict() for ride in recent_rides],
        'power_zones': total_zone_time,
        'trends': weeks
    }), 200

@dashboard_bp.route('/dashboard/analytics', methods=['GET'])
def get_analytics():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get query parameters
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get rides with power data
    power_rides = Ride.query.filter(
        Ride.user_id == user.id,
        Ride.date >= start_date,
        Ride.avg_power.isnot(None)
    ).order_by(Ride.date).all()
    
    # Calculate power progression
    power_progression = []
    for ride in power_rides:
        power_progression.append({
            'date': ride.date.isoformat(),
            'avg_power': ride.avg_power,
            'normalized_power': ride.normalized_power,
            'intensity_factor': ride.intensity_factor
        })
    
    # FTP progression (simplified - would need more sophisticated tracking)
    ftp_history = [{'date': datetime.utcnow().isoformat(), 'ftp': user.current_ftp or 0}]
    
    return jsonify({
        'power_progression': power_progression,
        'ftp_history': ftp_history,
        'performance_metrics': {
            'avg_weekly_tss': 0,  # Would calculate from data
            'training_load': 0,   # Would calculate from data
            'fitness_trend': 0    # Would calculate from data
        }
    }), 200

