#!/usr/bin/env python3
"""
Setup script for AI Cycling Academy dual account system
Creates demo account with example data and fresh user account
Uses SQLAlchemy models directly to ensure schema compatibility
"""

import json
import os
import sys
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.user import User, db
from src.models.ride import Ride
from src.main import app

def create_demo_account():
    """Create demo account with example data"""
    
    # Create demo user
    demo_user = User.query.filter_by(username='demo').first()
    if demo_user:
        # Delete existing demo user and their rides
        Ride.query.filter_by(user_id=demo_user.id).delete()
        db.session.delete(demo_user)
        db.session.commit()
    
    demo_user = User(
        username='demo',
        email='demo@aicyclistacademy.com',
        password_hash=generate_password_hash('demo123'),
        current_ftp=285,
        weight=72.5,
        max_heart_rate=185,
        resting_heart_rate=52,
        subscription_tier='premium'
    )
    
    db.session.add(demo_user)
    db.session.commit()
    
    # Create sample ride data programmatically
    try:
        # Generate 3 sample rides with realistic data
        from datetime import datetime, timedelta
        
        recent_dates = [
            datetime.now() - timedelta(days=2),
            datetime.now() - timedelta(days=5),
            datetime.now() - timedelta(days=8)
        ]
        
        rides_data = [
            {
                "name": "Morning Ride",
                "date": recent_dates[0].isoformat(),
                "distance": 66.1,
                "duration": 13140,
                "elevation_gain": 81,
                "average_power": 155,
                "average_heart_rate": 142,
                "average_cadence": 88,
                "training_stress_score": 119
            },
            {
                "name": "Recovery Ride",
                "date": recent_dates[1].isoformat(),
                "distance": 42.3,
                "duration": 7200,
                "elevation_gain": 43,
                "average_power": 120,
                "average_heart_rate": 128,
                "average_cadence": 85,
                "training_stress_score": 45
            },
            {
                "name": "Interval Training",
                "date": recent_dates[2].isoformat(),
                "distance": 13.9,
                "duration": 1860,
                "elevation_gain": 16,
                "average_power": 186,
                "average_heart_rate": 165,
                "average_cadence": 92,
                "training_stress_score": 25
            }
        ]
        
        # Insert demo rides with recent dates
        # Spread rides across the last 2 weeks
        ride_dates = [
            datetime.utcnow() - timedelta(days=14),
            datetime.utcnow() - timedelta(days=7),
            datetime.utcnow() - timedelta(days=2)
        ]
        
        for idx, ride_data in enumerate(rides_data):
            # Calculate metrics from available data
            power_values = ride_data.get('power_values', [])
            hr_values = ride_data.get('heart_rate_values', [])
            
            avg_power = int(sum(power_values) / len(power_values)) if power_values else None
            max_power = max(power_values) if power_values else None
            avg_hr = int(sum(hr_values) / len(hr_values)) if hr_values else None
            max_hr = max(hr_values) if hr_values else None
            
            # Calculate training metrics
            ftp = 285  # Demo user FTP
            if avg_power and avg_power > 0:
                normalized_power = avg_power * 1.05  # Rough NP estimate
                intensity_factor = normalized_power / ftp if ftp > 0 else 0
                tss = (ride_data['duration'] / 3600) * intensity_factor ** 2 * 100 if ftp > 0 else 0
            else:
                intensity_factor = 0
                tss = 0
                normalized_power = 0
            
            # Use recent date instead of original date
            ride_date = ride_dates[idx] if idx < len(ride_dates) else datetime.utcnow() - timedelta(days=1)
            
            ride = Ride(
                user_id=demo_user.id,
                date=ride_date,
                name=ride_data.get('name', f"Ride {ride_date.strftime('%Y-%m-%d')}"),
                duration=ride_data['duration'],
                distance=ride_data['distance'],
                avg_power=avg_power,
                max_power=max_power,
                normalized_power=int(normalized_power) if normalized_power else None,
                ftp=ftp,
                avg_heart_rate=avg_hr,
                max_heart_rate=max_hr,
                elevation_gain=int(ride_data['elevation_gain']) if ride_data.get('elevation_gain') else 0,
                avg_speed=ride_data.get('avg_speed', 25.0),
                max_speed=ride_data.get('avg_speed', 25.0) * 1.5 if ride_data.get('avg_speed') else 37.5,
                training_stress_score=tss,
                intensity_factor=intensity_factor,
                file_path=f"demo_{ride_data['name'].replace(' ', '_')}.fit"
            )
            
            db.session.add(ride)
        
        db.session.commit()
        print(f"✅ Created demo account with {len(rides_data)} rides")
        
    except FileNotFoundError:
        print("⚠️  No ride data found, creating demo account without rides")
        db.session.commit()
    
    return demo_user.id

def create_user_account():
    """Create fresh user account"""
    
    # Create user account
    user = User.query.filter_by(username='user').first()
    if user:
        # Delete existing user and their rides
        Ride.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
    
    user = User(
        username='user',
        email='user@aicyclistacademy.com',
        password_hash=generate_password_hash('user123'),
        current_ftp=250,
        weight=70.0,
        max_heart_rate=180,
        resting_heart_rate=60,
        subscription_tier='free'
    )
    
    db.session.add(user)
    db.session.commit()
    
    print("✅ Created fresh user account")
    return user.id

def main():
    """Main setup function"""
    print("🚀 Setting up AI Cycling Academy dual account system...")
    
    with app.app_context():
        # Create accounts
        demo_id = create_demo_account()
        user_id = create_user_account()
        
        # Create account info file
        account_info = {
            "demo_account": {
                "id": demo_id,
                "username": "demo",
                "email": "demo@aicyclistacademy.com",
                "password": "demo123",
                "description": "Demo account with example ride data and coaching history"
            },
            "user_account": {
                "id": user_id,
                "username": "user",
                "email": "user@aicyclistacademy.com", 
                "password": "user123",
                "description": "Fresh user account for actual use"
            }
        }
        
        with open('/home/ubuntu/account_info.json', 'w') as f:
            json.dump(account_info, f, indent=2)
        
        print("\n🎉 Dual account system setup complete!")
        print("\n📋 Account Details:")
        print("Demo Account (with example data):")
        print("  Username: demo")
        print("  Email: demo@aicyclistacademy.com")
        print("  Password: demo123")
        print("\nUser Account (fresh for actual use):")
        print("  Username: user")
        print("  Email: user@aicyclistacademy.com")
        print("  Password: user123")
        print("\n💾 Account info saved to: /home/ubuntu/account_info.json")

if __name__ == "__main__":
    main()

