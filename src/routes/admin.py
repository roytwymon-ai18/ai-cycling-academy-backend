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
        from flask import request
        data = request.get_json() or {}
        force = data.get('force', False)
        
        # Find demo user
        demo_user = User.query.filter_by(username='demo').first()
        if not demo_user:
            return jsonify({'error': 'Demo user not found'}), 404
        
        # Check if demo user already has rides
        existing_rides = Ride.query.filter_by(user_id=demo_user.id).count()
        if existing_rides > 0 and not force:
            return jsonify({'message': f'Demo user already has {existing_rides} rides'}), 200
        
        # Delete existing rides if force=True
        if force and existing_rides > 0:
            Ride.query.filter_by(user_id=demo_user.id).delete()
            db.session.commit()
        
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
                name=f'Sample Ride {i+1}',
                date=ride_date,
                duration=duration,
                distance=distance / 1000,  # Convert meters to km
                avg_power=avg_power,
                max_power=int(avg_power * 1.8),
                avg_heart_rate=avg_hr,
                max_heart_rate=int(avg_hr * 1.15),
                avg_cadence=avg_cadence,
                elevation_gain=elevation_gain,
                training_stress_score=int(duration * avg_power * 0.01)
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




@admin_bp.route('/fix-onboarding', methods=['POST'])
def fix_onboarding():
    """Admin endpoint to manually set onboarding completion"""
    try:
        from flask import request, jsonify
        from src.models.client_profile import ClientProfile
        
        data = request.get_json() or {}
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        # Get or create profile
        profile = ClientProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            profile = ClientProfile(user_id=user_id)
            db.session.add(profile)
        
        # Set onboarding as completed
        profile.onboarding_completed = True
        profile.onboarding_step = 12
        
        # Set some default values
        if not profile.rider_type:
            profile.rider_type = "Road cycling"
        if not profile.primary_goals:
            profile.primary_goals = "Improve FTP and endurance"
        if not profile.training_availability:
            profile.training_availability = "4-5 days per week"
        
        db.session.add(profile)
        db.session.flush()
        db.session.commit()
        
        # Verify it was saved
        saved_profile = ClientProfile.query.filter_by(user_id=user_id).first()
        
        return jsonify({
            'success': True,
            'message': f'Onboarding fixed for user {user_id}',
            'profile': {
                'id': saved_profile.id,
                'user_id': saved_profile.user_id,
                'onboarding_completed': saved_profile.onboarding_completed,
                'onboarding_step': saved_profile.onboarding_step
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



@admin_bp.route('/populate-metrics', methods=['POST'])
def populate_metrics():
    """Populate missing avg_speed, max_speed, and max_power for all rides"""
    try:
        # Get all rides
        rides = Ride.query.all()
        
        updated_count = 0
        
        # Ride type intensities (as % of FTP)
        ride_types = {
            'Recovery': 0.55,
            'Endurance': 0.65,
            'Tempo': 0.75,
            'Threshold': 0.88,
            'Interval': 0.95,
            'Morning': 0.70,
            'Afternoon': 0.70,
            'Evening': 0.70
        }
        
        for ride in rides:
            updated = False
            
            # Get user's FTP
            user = User.query.get(ride.user_id)
            if not user:
                continue
            
            # Calculate avg_speed if missing (distance / time)
            if ride.avg_speed is None or ride.avg_speed == 0:
                if ride.distance and ride.duration and ride.duration > 0:
                    ride.avg_speed = round(ride.distance / (ride.duration / 3600), 1)
                    updated = True
            
            # Calculate max_speed if missing
            if ride.max_speed is None or ride.max_speed == 0:
                if ride.avg_speed and ride.avg_speed > 0:
                    ride.max_speed = round(ride.avg_speed * 1.3, 1)
                    updated = True
            
            # Calculate power metrics if missing
            if (ride.avg_power is None or ride.avg_power == 0) and user.current_ftp:
                # Determine ride intensity based on name
                intensity = 0.70  # default
                for ride_type, intensity_factor in ride_types.items():
                    if ride_type in ride.name:
                        intensity = intensity_factor
                        break
                
                ride.avg_power = int(user.current_ftp * intensity)
                ride.max_power = int(ride.avg_power * 2.0)
                ride.normalized_power = int(ride.avg_power * 1.08)
                ride.ftp = user.current_ftp
                ride.intensity_factor = round(ride.normalized_power / user.current_ftp, 3)
                
                # Calculate TSS
                duration_hours = ride.duration / 3600
                ride.training_stress_score = round(
                    (duration_hours * ride.normalized_power * ride.intensity_factor) / user.current_ftp * 100,
                    1
                )
                updated = True
            
            # Calculate max_power if missing but avg_power exists
            elif ride.max_power is None or ride.max_power == 0:
                if ride.avg_power and ride.avg_power > 0:
                    ride.max_power = int(ride.avg_power * 2.0)
                    updated = True
            
            if updated:
                updated_count += 1
        
        # Commit all changes
        if updated_count > 0:
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully updated {updated_count} rides with missing metrics',
            'updated_count': updated_count,
            'total_rides': len(rides)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

