from src.models.user import User, db
from src.models.ride import Ride
from datetime import datetime, timedelta
import random
import json

def create_demo_user():
    """
    Create demo user 'user01' with realistic cycling data
    """
    
    # Create user01
    user = User(
        username='user01',
        email='user01@aicyclistacademy.com',
        current_ftp=285,  # Realistic FTP for competitive cyclist
        weight=75.0,      # kg
        max_heart_rate=190,
        resting_heart_rate=45,
        subscription_tier='premium'
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Generate 30 days of realistic ride data
    base_date = datetime.utcnow() - timedelta(days=30)
    
    # Training schedule: 5-6 rides per week with variety
    ride_types = [
        {'name': 'Easy Endurance', 'duration_range': (3600, 5400), 'intensity': 0.65, 'frequency': 0.3},
        {'name': 'Tempo Intervals', 'duration_range': (3600, 4800), 'intensity': 0.85, 'frequency': 0.2},
        {'name': 'VO2 Max Intervals', 'duration_range': (2700, 3600), 'intensity': 1.15, 'frequency': 0.15},
        {'name': 'Sweet Spot', 'duration_range': (3600, 5400), 'intensity': 0.90, 'frequency': 0.2},
        {'name': 'Recovery Ride', 'duration_range': (1800, 3600), 'intensity': 0.55, 'frequency': 0.15}
    ]
    
    for day in range(30):
        current_date = base_date + timedelta(days=day)
        
        # Skip some days (rest days)
        if random.random() < 0.25:  # 25% chance of rest day
            continue
            
        # Choose ride type
        ride_type = random.choices(ride_types, weights=[r['frequency'] for r in ride_types])[0]
        
        # Generate ride metrics
        duration = random.randint(*ride_type['duration_range'])
        avg_power = int(user.current_ftp * ride_type['intensity'] * random.uniform(0.95, 1.05))
        max_power = int(avg_power * random.uniform(1.8, 2.5))
        normalized_power = int(avg_power * random.uniform(1.05, 1.15))
        
        # Calculate other metrics
        intensity_factor = normalized_power / user.current_ftp if user.current_ftp else 0
        training_stress_score = (duration / 3600) * intensity_factor * intensity_factor * 100
        
        # Heart rate based on power
        hr_factor = 0.7 + (intensity_factor * 0.3)  # HR correlates with power
        avg_heart_rate = int(user.resting_heart_rate + (user.max_heart_rate - user.resting_heart_rate) * hr_factor)
        max_heart_rate = min(user.max_heart_rate, int(avg_heart_rate * 1.1))
        
        # Speed and distance (realistic for road cycling)
        avg_speed = random.uniform(28, 42)  # km/h
        distance = (avg_speed * duration) / 3600  # km
        
        # Cadence
        avg_cadence = random.randint(85, 95)
        
        # Elevation (varies by ride)
        elevation_gain = int(distance * random.uniform(8, 25))  # meters per km
        
        # Power zones distribution based on ride type
        total_time = duration
        if ride_type['name'] == 'Easy Endurance':
            zones = [0.6, 0.3, 0.1, 0, 0, 0, 0]  # Mostly Z1-Z2
        elif ride_type['name'] == 'Tempo Intervals':
            zones = [0.2, 0.3, 0.4, 0.1, 0, 0, 0]  # Focus on Z3-Z4
        elif ride_type['name'] == 'VO2 Max Intervals':
            zones = [0.1, 0.2, 0.2, 0.2, 0.3, 0, 0]  # High intensity Z5
        elif ride_type['name'] == 'Sweet Spot':
            zones = [0.1, 0.2, 0.6, 0.1, 0, 0, 0]  # Focus on Z3
        else:  # Recovery
            zones = [0.8, 0.2, 0, 0, 0, 0, 0]  # Mostly Z1
        
        # Convert to time in seconds
        zone_times = [int(total_time * z) for z in zones]
        
        # Create ride
        ride = Ride(
            user_id=user.id,
            name=f"{ride_type['name']} - {current_date.strftime('%b %d')}",
            date=current_date,
            duration=duration,
            distance=round(distance, 2),
            avg_power=avg_power,
            max_power=max_power,
            normalized_power=normalized_power,
            ftp=user.current_ftp,
            intensity_factor=round(intensity_factor, 3),
            training_stress_score=round(training_stress_score, 1),
            avg_heart_rate=avg_heart_rate,
            max_heart_rate=max_heart_rate,
            avg_speed=round(avg_speed, 1),
            max_speed=round(avg_speed * 1.3, 1),
            avg_cadence=avg_cadence,
            elevation_gain=elevation_gain,
            time_in_zone_1=zone_times[0],
            time_in_zone_2=zone_times[1],
            time_in_zone_3=zone_times[2],
            time_in_zone_4=zone_times[3],
            time_in_zone_5=zone_times[4],
            time_in_zone_6=zone_times[5],
            time_in_zone_7=zone_times[6]
        )
        
        # Add some AI analysis for recent rides
        if day >= 25:  # Last 5 rides have AI analysis
            analysis = {
                "performance_analysis": f"Strong {ride_type['name'].lower()} session with good power consistency.",
                "zone_analysis": f"Appropriate time distribution for {ride_type['name'].lower()} workout.",
                "strengths": ["Good power consistency", "Appropriate intensity"],
                "improvements": ["Consider longer intervals", "Focus on cadence smoothness"],
                "recovery": "24-48 hours easy spinning recommended" if intensity_factor > 0.8 else "Ready for next session",
                "next_focus": "Continue building aerobic base" if ride_type['name'] == 'Easy Endurance' else "Recovery ride recommended"
            }
            ride.ai_analysis = json.dumps(analysis)
            ride.ai_recommendations = analysis['next_focus']
            ride.analyzed_at = current_date + timedelta(minutes=30)
        
        db.session.add(ride)
    
    db.session.commit()
    print(f"Created demo user '{user.username}' with {len(user.rides)} rides")
    return user

