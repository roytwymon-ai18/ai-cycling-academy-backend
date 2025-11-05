#!/usr/bin/env python3
"""
Check what metrics the demo account rides have
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

from src.models.user import db, User
from src.models.ride import Ride
from src.main import app

def check_demo_rides():
    """Check metrics for demo account rides"""
    with app.app_context():
        # Find demo user
        demo_user = User.query.filter_by(username='demo').first()
        
        if not demo_user:
            print("❌ Demo user not found")
            return
        
        print(f"✅ Found demo user: {demo_user.username} (ID: {demo_user.id})\n")
        
        # Get demo rides
        rides = Ride.query.filter_by(user_id=demo_user.id).order_by(Ride.date.desc()).all()
        
        print(f"Total rides: {len(rides)}\n")
        
        for i, ride in enumerate(rides[:5], 1):  # Show first 5 rides
            print(f"Ride {i}: {ride.name}")
            print(f"  Date: {ride.date}")
            print(f"  Distance: {ride.distance} km")
            print(f"  Duration: {ride.duration} seconds")
            print(f"  Avg Power: {ride.avg_power}W")
            print(f"  Max Power: {ride.max_power}W")
            print(f"  Avg Speed: {ride.avg_speed} km/h")
            print(f"  Max Speed: {ride.max_speed} km/h")
            print()

if __name__ == '__main__':
    check_demo_rides()

