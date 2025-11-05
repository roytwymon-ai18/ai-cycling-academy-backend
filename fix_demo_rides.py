#!/usr/bin/env python3
"""
Add realistic power and speed metrics to demo rides
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

from src.models.user import db, User
from src.models.ride import Ride
from src.main import app

def fix_demo_rides():
    """Add realistic metrics to demo rides"""
    with app.app_context():
        # Find demo user
        demo_user = User.query.filter_by(username='demo').first()
        
        if not demo_user:
            print("❌ Demo user not found")
            return
        
        print(f"✅ Found demo user: {demo_user.username} (ID: {demo_user.id})")
        print(f"   FTP: {demo_user.current_ftp}W\n")
        
        # Get demo rides
        rides = Ride.query.filter_by(user_id=demo_user.id).order_by(Ride.date.desc()).all()
        
        print(f"Updating {len(rides)} rides...\n")
        
        # Ride type intensities (as % of FTP)
        ride_types = {
            'Recovery': 0.55,
            'Endurance': 0.65,
            'Tempo': 0.75,
            'Threshold': 0.88,
            'Interval': 0.95,
            'Morning': 0.70,  # General ride
            'Afternoon': 0.70,
            'Evening': 0.70
        }
        
        for ride in rides:
            # Determine ride intensity based on name
            intensity = 0.70  # default
            for ride_type, intensity_factor in ride_types.items():
                if ride_type in ride.name:
                    intensity = intensity_factor
                    break
            
            # Calculate power if missing
            if ride.avg_power is None or ride.avg_power == 0:
                ride.avg_power = int(demo_user.current_ftp * intensity)
                ride.max_power = int(ride.avg_power * 2.0)  # Sprint power
                ride.normalized_power = int(ride.avg_power * 1.08)  # NP typically 5-10% higher
                
                # Calculate training metrics
                if demo_user.current_ftp:
                    ride.ftp = demo_user.current_ftp
                    ride.intensity_factor = round(ride.normalized_power / demo_user.current_ftp, 3)
                    # TSS = (duration_hours × NP × IF) / FTP × 100
                    duration_hours = ride.duration / 3600
                    ride.training_stress_score = round(
                        (duration_hours * ride.normalized_power * ride.intensity_factor) / demo_user.current_ftp * 100,
                        1
                    )
                
                print(f"  Updated: {ride.name}")
                print(f"    Avg Power: {ride.avg_power}W")
                print(f"    Max Power: {ride.max_power}W")
                print(f"    NP: {ride.normalized_power}W")
                print(f"    IF: {ride.intensity_factor}")
                print(f"    TSS: {ride.training_stress_score}")
                print()
        
        # Commit all changes
        db.session.commit()
        print(f"✅ Successfully updated all demo rides")

if __name__ == '__main__':
    fix_demo_rides()

