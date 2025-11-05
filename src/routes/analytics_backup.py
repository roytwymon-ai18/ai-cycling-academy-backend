from flask import Blueprint, jsonify, request, session
from src.models.user import User, db
from src.models.ride import Ride
from datetime import datetime, timedelta
from sqlalchemy import func

analytics_bp = Blueprint('analytics', __name__)

def require_auth():
    """Check if user is authenticated"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

@analytics_bp.route('/analytics', methods=['GET'])
def get_analytics():
    """Get performance analytics for specified time range"""
    user = require_auth()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get time range from query parameter (default 30 days)
    days = int(request.args.get('days', 30))
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get rides in time range
    rides = Ride.query.filter(
        Ride.user_id == user.id,
        Ride.date >= start_date
    ).order_by(Ride.date.asc()).all()
    
    if not rides:
        return jsonify({
            'total_rides': 0,
            'total_distance': 0,
            'avg_power': 0,
            'total_tss': 0,
            'rides_per_week': 0,
            'hours_per_week': 0,
            'weekly_tss': [],
            'power_zones': [],
            'insights': []
        }), 200
    
    # Calculate summary statistics
    total_rides = len(rides)
    total_distance = sum(r.distance for r in rides if r.distance)  # Already in km
    avg_power = sum(r.avg_power for r in rides if r.avg_power) / len([r for r in rides if r.avg_power]) if any(r.avg_power for r in rides) else 0
    total_tss = sum(r.training_stress_score or 0 for r in rides)
    total_duration = sum(r.duration for r in rides)
    
    # Calculate per-week averages
    weeks = days / 7
    rides_per_week = total_rides / weeks if weeks > 0 else 0
    hours_per_week = (total_duration / 3600) / weeks if weeks > 0 else 0
    
    # Calculate weekly TSS trend
    weekly_tss = calculate_weekly_tss(rides, days)
    
    # Calculate power zones distribution (simplified)
    power_zones = calculate_power_zones(rides, user.current_ftp)
    
    # Generate insights
    insights = generate_insights(rides, user, total_tss, rides_per_week, hours_per_week)
    
    return jsonify({
        'total_rides': total_rides,
        'total_distance': round(total_distance, 1),
        'avg_power': round(avg_power, 0),
        'total_tss': round(total_tss, 0),
        'rides_per_week': round(rides_per_week, 1),
        'hours_per_week': round(hours_per_week, 1),
        'weekly_tss': weekly_tss,
        'power_zones': power_zones,
        'insights': insights
    }), 200

def calculate_weekly_tss(rides, days):
    """Calculate TSS per week for chart"""
    weeks = min(int(days / 7), 12)  # Max 12 weeks for chart
    weekly_data = []
    
    now = datetime.utcnow()
    for week in range(weeks):
        week_start = now - timedelta(days=(week + 1) * 7)
        week_end = now - timedelta(days=week * 7)
        
        week_rides = [r for r in rides if week_start <= r.date < week_end]
        week_tss = sum(r.training_stress_score or 0 for r in week_rides)
        
        weekly_data.insert(0, {
            'week': weeks - week,
            'tss': round(week_tss, 1)
        })
    
    return weekly_data

def calculate_power_zones(rides, ftp):
    """Calculate time spent in each power zone"""
    # Simplified calculation - in production, would analyze second-by-second data
    zones = [
        {'zone': 'Z1', 'percentage': 0},
        {'zone': 'Z2', 'percentage': 0},
        {'zone': 'Z3', 'percentage': 0},
        {'zone': 'Z4', 'percentage': 0},
        {'zone': 'Z5', 'percentage': 0},
        {'zone': 'Z6', 'percentage': 0}
    ]
    
    if not ftp or not rides:
        return zones
    
    # Estimate distribution based on average power
    for ride in rides:
        if not ride.avg_power:
            continue
        
        power_ratio = ride.avg_power / ftp
        
        # Assign to zone based on average power
        if power_ratio < 0.55:
            zones[0]['percentage'] += ride.duration
        elif power_ratio < 0.75:
            zones[1]['percentage'] += ride.duration
        elif power_ratio < 0.90:
            zones[2]['percentage'] += ride.duration
        elif power_ratio < 1.05:
            zones[3]['percentage'] += ride.duration
        elif power_ratio < 1.20:
            zones[4]['percentage'] += ride.duration
        else:
            zones[5]['percentage'] += ride.duration
    
    # Convert to percentages
    total_time = sum(z['percentage'] for z in zones)
    if total_time > 0:
        for zone in zones:
            zone['percentage'] = round((zone['percentage'] / total_time) * 100, 1)
    
    return zones

def generate_insights(rides, user, total_tss, rides_per_week, hours_per_week):
    """Generate performance insights based on data"""
    insights = []
    
    # Training consistency insight
    if rides_per_week >= 4:
        insights.append(f"Excellent consistency! You're averaging {rides_per_week:.1f} rides per week.")
    elif rides_per_week >= 2:
        insights.append(f"Good training frequency at {rides_per_week:.1f} rides per week. Consider adding 1-2 more rides for faster progress.")
    else:
        insights.append(f"Training frequency is low at {rides_per_week:.1f} rides per week. Aim for at least 3 rides per week for steady improvement.")
    
    # Training load insight
    weekly_tss = total_tss / (len(rides) / max(rides_per_week, 1)) if rides_per_week > 0 else 0
    if weekly_tss > 450:
        insights.append(f"High training load ({weekly_tss:.0f} TSS/week). Make sure you're recovering adequately to avoid burnout.")
    elif weekly_tss > 250:
        insights.append(f"Moderate training load ({weekly_tss:.0f} TSS/week) - good balance for steady improvement.")
    else:
        insights.append(f"Light training load ({weekly_tss:.0f} TSS/week). Consider increasing volume gradually for faster FTP gains.")
    
    # Power progression insight
    if len(rides) >= 5:
        recent_rides = sorted(rides, key=lambda r: r.date, reverse=True)[:5]
        recent_avg_power = sum(r.avg_power for r in recent_rides if r.avg_power) / len([r for r in recent_rides if r.avg_power]) if any(r.avg_power for r in recent_rides) else 0
        
        older_rides = sorted(rides, key=lambda r: r.date)[: min(5, len(rides) - 5)]
        if older_rides:
            older_avg_power = sum(r.avg_power for r in older_rides if r.avg_power) / len([r for r in older_rides if r.avg_power]) if any(r.avg_power for r in older_rides) else 0
            
            if recent_avg_power > older_avg_power * 1.05:
                insights.append(f"Power is trending up! Recent rides average {recent_avg_power:.0f}W vs {older_avg_power:.0f}W earlier.")
            elif recent_avg_power < older_avg_power * 0.95:
                insights.append(f"Power has decreased recently. Consider adding more recovery or checking for fatigue.")
    
    # Goals-based insight
    if user.training_goals:
        insights.append(f"Keep working towards your goal: {user.training_goals}")
    
    return insights




@analytics_bp.route('/analytics/last-ride-analysis', methods=['GET'])
def get_last_ride_analysis():
    """Get AI-powered analysis of the user's most recent ride"""
    user = require_auth()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get the most recent ride
    last_ride = Ride.query.filter_by(user_id=user.id).order_by(Ride.date.desc()).first()
    
    if not last_ride:
        return jsonify({'ride': None, 'analysis': None}), 200
    
    # Get user's profile for personalized insights
    from src.models.client_profile import ClientProfile
    profile = ClientProfile.query.filter_by(user_id=user.id).first()
    
    # Generate AI analysis
    try:
        analysis = generate_ride_analysis(last_ride, profile, user)
    except Exception as e:
        print(f"Error generating ride analysis: {str(e)}")
        analysis = "Analysis temporarily unavailable. Your ride data has been recorded successfully."
    
    # Format ride data
    ride_data = {
        'id': last_ride.id,
        'name': last_ride.name,
        'date': last_ride.date.isoformat() if last_ride.date else None,
        'distance': last_ride.distance,  # in km
        'duration': last_ride.duration,  # in seconds
        'avg_power': last_ride.avg_power,
        'avg_heart_rate': last_ride.avg_heart_rate,
        'avg_cadence': last_ride.avg_cadence,
        'training_stress_score': last_ride.training_stress_score,
        'elevation_gain': last_ride.elevation_gain
    }
    
    return jsonify({
        'ride': ride_data,
        'analysis': analysis
    }), 200


def generate_ride_analysis(ride, profile, user):
    """Generate AI-powered analysis of a ride based on user's goals"""
    import os
    from openai import OpenAI
    
    # Initialize OpenAI client (API key from environment)
    client = OpenAI()
    
    # Build context about the user
    user_context = ""
    if profile:
        if profile.primary_goals:
            user_context += f"User's goals: {profile.primary_goals}\n"
        if profile.rider_type:
            user_context += f"Rider type: {profile.rider_type}\n"
        if profile.training_availability:
            user_context += f"Training availability: {profile.training_availability}\n"
        if profile.current_ftp:
            user_context += f"Current FTP: {profile.current_ftp}W\n"
    
    # Build ride metrics
    ride_metrics = f"""
Ride: {ride.name}
Date: {ride.date.strftime('%Y-%m-%d') if ride.date else 'Unknown'}
Distance: {ride.distance:.1f} km ({ride.distance * 0.621371:.1f} miles)
Duration: {ride.duration // 60} minutes
"""
    
    if ride.avg_power:
        ride_metrics += f"Average Power: {ride.avg_power}W\n"
        if profile and profile.current_ftp:
            intensity = (ride.avg_power / profile.current_ftp) * 100
            ride_metrics += f"Intensity: {intensity:.0f}% of FTP\n"
    
    if ride.avg_heart_rate:
        ride_metrics += f"Average Heart Rate: {ride.avg_heart_rate} bpm\n"
    
    if ride.avg_cadence:
        ride_metrics += f"Average Cadence: {ride.avg_cadence} rpm\n"
    
    if ride.training_stress_score:
        ride_metrics += f"Training Stress Score (TSS): {ride.training_stress_score}\n"
    
    if ride.elevation_gain:
        ride_metrics += f"Elevation Gain: {ride.elevation_gain}m ({ride.elevation_gain * 3.28084:.0f} feet)\n"
    
    # Create prompt for AI analysis
    prompt = f"""As an expert cycling coach, analyze this ride and provide comprehensive insights to help the athlete achieve their goals.

{user_context}

{ride_metrics}

Provide a thorough analysis covering:
1. Overall performance assessment
2. Intensity and effort level
3. How this ride aligns with their stated goals
4. Specific strengths demonstrated
5. Areas for improvement
6. Actionable recommendations for their next training session

Be specific, encouraging, and data-driven. Keep the tone professional but friendly. Limit response to 250 words."""
    
    # Call OpenAI API
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are Coach Manee, a legendary cycling coach with over 30 years of experience coaching at the highest levels of competitive cycling. You've guided numerous athletes to World Championship and Olympic medals, developed countless national champions, and pioneered training methodologies that have revolutionized the sport. Your expertise spans all cycling disciplines. You combine cutting-edge sports science with decades of real-world coaching wisdom to provide insightful, personalized training analysis."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        raise

