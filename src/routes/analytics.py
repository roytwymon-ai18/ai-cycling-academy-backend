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
    total_distance = sum(r.distance for r in rides) / 1000  # Convert to km
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

