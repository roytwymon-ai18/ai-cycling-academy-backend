from flask import Blueprint, jsonify
from src.models.user import db, User
from src.models.ride import Ride
from datetime import datetime, timedelta
import random

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/generate-sample-data', methods=['POST'])
def generate_sample_data():
    """Generate sample ride data for demo account"""
    try:
        # Find demo user
        demo_user = User.query.filter_by(username='demo').first()
        if not demo_user:
            return jsonify({'error': 'Demo user not found'}), 404
        
        # Check if demo user already has rides
        existing_rides = Ride.query.filter_by(user_id=demo_user.id).count()
        if existing_rides > 0:
            return jsonify({'message': f'Demo user already has {existing_rides} rides'}), 200
        
        # Generate 5 sample rides over the past 2 weeks
        sample_rides = []
        base_date = datetime.now() - timedelta(days=14)
        
        for i in range(5):
            ride_date = base_date + timedelta(days=i*3)
            duration = random.randint(1800, 5400)  # 30-90 minutes
            distance = random.randint(15000, 45000)  # 15-45 km
            avg_power = random.randint(180, 250)
            avg_hr = random.randint(135, 165)
            avg_cadence = random.randint(80, 95)
            elevation_gain = random.randint(200, 800)
            
            ride = Ride(
                user_id=demo_user.id,
                filename=f'sample_ride_{i+1}.fit',
                upload_date=ride_date,
                ride_date=ride_date,
                duration=duration,
                distance=distance,
                avg_power=avg_power,
                max_power=int(avg_power * 1.8),
                avg_hr=avg_hr,
                max_hr=int(avg_hr * 1.15),
                avg_cadence=avg_cadence,
                max_cadence=int(avg_cadence * 1.3),
                elevation_gain=elevation_gain,
                calories=int(duration * avg_power * 0.0036),
                tss=int(duration * avg_power * 0.01)
            )
            sample_rides.append(ride)
        
        # Add all rides to database
        for ride in sample_rides:
            db.session.add(ride)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully generated {len(sample_rides)} sample rides for demo user',
            'rides': len(sample_rides)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

