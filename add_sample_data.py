#!/usr/bin/env python3
"""
Script to add sample ride data to the demo account
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from src.models.user import db, User
from src.models.ride import Ride
from src.main import app
import random

def add_sample_rides():
    """Add sample ride data to the demo user account"""
    with app.app_context():
        # Find demo user
        demo_user = User.query.filter_by(username='demo').first()
        if not demo_user:
            print("Demo user not found!")
            return
        
        print(f"Found demo user: {demo_user.username} (ID: {demo_user.id})")
        
        # Check if demo user already has rides
        existing_rides = Ride.query.filter_by(user_id=demo_user.id).count()
        if existing_rides > 0:
            print(f"Demo user already has {existing_rides} rides. Skipping...")
            return
        
        print("Adding sample rides...")
        
        # Generate 10 sample rides over the past 30 days
        base_date = datetime.utcnow()
        
        sample_rides = [
            {
                'days_ago': 2,
                'duration': 3600,  # 1 hour
                'distance': 25.5,  # km
                'avg_power': 220,  # watts
                'avg_hr': 145,
                'max_hr': 165,
                'avg_cadence': 85,
                'elevation_gain': 350,
                'tss': 65
            },
            {
                'days_ago': 5,
                'duration': 5400,  # 1.5 hours
                'distance': 38.2,
                'avg_power': 210,
                'avg_hr': 142,
                'max_hr': 172,
                'avg_cadence': 88,
                'elevation_gain': 520,
                'tss': 82
            },
            {
                'days_ago': 7,
                'duration': 2700,  # 45 min
                'distance': 18.5,
                'avg_power': 245,
                'avg_hr': 158,
                'max_hr': 178,
                'avg_cadence': 92,
                'elevation_gain': 180,
                'tss': 58
            },
            {
                'days_ago': 10,
                'duration': 7200,  # 2 hours
                'distance': 52.3,
                'avg_power': 200,
                'avg_hr': 138,
                'max_hr': 160,
                'avg_cadence': 82,
                'elevation_gain': 680,
                'tss': 95
            },
            {
                'days_ago': 12,
                'duration': 3300,  # 55 min
                'distance': 22.8,
                'avg_power': 230,
                'avg_hr': 150,
                'max_hr': 170,
                'avg_cadence': 86,
                'elevation_gain': 290,
                'tss': 68
            },
            {
                'days_ago': 14,
                'duration': 4500,  # 1.25 hours
                'distance': 32.5,
                'avg_power': 215,
                'avg_hr': 144,
                'max_hr': 168,
                'avg_cadence': 84,
                'elevation_gain': 420,
                'tss': 75
            },
            {
                'days_ago': 17,
                'duration': 3000,  # 50 min
                'distance': 20.2,
                'avg_power': 235,
                'avg_hr': 152,
                'max_hr': 174,
                'avg_cadence': 90,
                'elevation_gain': 240,
                'tss': 62
            },
            {
                'days_ago': 19,
                'duration': 6300,  # 1.75 hours
                'distance': 45.8,
                'avg_power': 205,
                'avg_hr': 140,
                'max_hr': 162,
                'avg_cadence': 83,
                'elevation_gain': 580,
                'tss': 88
            },
            {
                'days_ago': 23,
                'duration': 3900,  # 1.08 hours
                'distance': 28.5,
                'avg_power': 225,
                'avg_hr': 148,
                'max_hr': 169,
                'avg_cadence': 87,
                'elevation_gain': 380,
                'tss': 72
            },
            {
                'days_ago': 26,
                'duration': 5100,  # 1.42 hours
                'distance': 36.2,
                'avg_power': 218,
                'avg_hr': 146,
                'max_hr': 166,
                'avg_cadence': 85,
                'elevation_gain': 460,
                'tss': 80
            }
        ]
        
        for i, ride_data in enumerate(sample_rides, 1):
            ride_date = base_date - timedelta(days=ride_data['days_ago'])
            
            ride = Ride(
                user_id=demo_user.id,
                name=f"Morning Ride #{i}",
                date=ride_date,
                duration=ride_data['duration'],
                distance=ride_data['distance'],
                avg_power=ride_data['avg_power'],
                avg_heart_rate=ride_data['avg_hr'],
                max_heart_rate=ride_data['max_hr'],
                avg_cadence=ride_data['avg_cadence'],
                elevation_gain=ride_data['elevation_gain'],
                training_stress_score=ride_data['tss'],
                avg_speed=ride_data['distance'] / (ride_data['duration'] / 3600),  # km/h
                file_path=f"/uploads/sample_ride_{i}.fit"
            )
            
            db.session.add(ride)
            print(f"  Added ride {i}: {ride_data['distance']}km, {ride_data['avg_power']}W avg power")
        
        db.session.commit()
        print(f"\n✅ Successfully added {len(sample_rides)} sample rides to demo account!")

if __name__ == '__main__':
    add_sample_rides()

