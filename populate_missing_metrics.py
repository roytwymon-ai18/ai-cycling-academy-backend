#!/usr/bin/env python3
"""
Populate missing avg_speed, max_speed, and max_power for existing rides
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

from src.models.user import db
from src.models.ride import Ride
from src.main import app

def populate_missing_metrics():
    """Calculate and populate missing metrics for all rides"""
    with app.app_context():
        # Get all rides
        rides = Ride.query.all()
        
        updated_count = 0
        
        for ride in rides:
            updated = False
            
            # Calculate avg_speed if missing (distance / time)
            if ride.avg_speed is None or ride.avg_speed == 0:
                if ride.distance and ride.duration and ride.duration > 0:
                    # avg_speed in km/h = distance (km) / time (hours)
                    ride.avg_speed = round(ride.distance / (ride.duration / 3600), 1)
                    updated = True
                    print(f"  Set avg_speed to {ride.avg_speed} km/h for ride: {ride.name}")
            
            # Calculate max_speed if missing (estimate as 1.3x avg_speed)
            if ride.max_speed is None or ride.max_speed == 0:
                if ride.avg_speed and ride.avg_speed > 0:
                    ride.max_speed = round(ride.avg_speed * 1.3, 1)
                    updated = True
                    print(f"  Set max_speed to {ride.max_speed} km/h for ride: {ride.name}")
            
            # Calculate max_power if missing (estimate as 2.0x avg_power for sprints)
            if ride.max_power is None or ride.max_power == 0:
                if ride.avg_power and ride.avg_power > 0:
                    ride.max_power = int(ride.avg_power * 2.0)
                    updated = True
                    print(f"  Set max_power to {ride.max_power}W for ride: {ride.name}")
            
            if updated:
                updated_count += 1
        
        # Commit all changes
        if updated_count > 0:
            db.session.commit()
            print(f"\n✅ Successfully updated {updated_count} rides with missing metrics")
        else:
            print("\n✅ All rides already have complete metrics")

if __name__ == '__main__':
    print("Populating missing metrics for all rides...\n")
    populate_missing_metrics()

