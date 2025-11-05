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
            'avg_weighted_power': 0,
            'avg_intensity': 0,
            'avg_speed': 0,
            'max_speed': 0,
            'max_power': 0,
            'total_tss': 0,
            'total_work_kj': 0,
            'total_calories': 0,
            'rides_per_week': 0,
            'hours_per_week': 0,
            'weekly_tss': [],
            'power_zones': [],
            'insights': [],
            'progress_comparison': {},
            'monthly_stats': []
        }), 200
    
    # Calculate summary statistics
    total_rides = len(rides)
    total_distance = sum(r.distance for r in rides if r.distance)  # Already in km
    avg_power = sum(r.avg_power for r in rides if r.avg_power) / len([r for r in rides if r.avg_power]) if any(r.avg_power for r in rides) else 0
    total_tss = sum(r.training_stress_score or 0 for r in rides)
    total_duration = sum(r.duration for r in rides)
    
    # NEW FEATURE 5: Calculate weighted average power (estimated)
    avg_weighted_power = calculate_estimated_weighted_power(rides)
    
    # NEW FEATURE 6: Calculate work done and calories
    total_work_kj = calculate_total_work(rides)
    total_calories = round(total_work_kj)  # kJ to kcal is approximately 1:1
    
    # Calculate speed and power metrics
    avg_speed = calculate_avg_speed(rides)
    max_speed = calculate_max_speed(rides)
    max_power = calculate_max_power(rides)
    
    # NEW FEATURE 1: Calculate average intensity
    avg_intensity = calculate_avg_intensity(rides, user.current_ftp)
    
    # Calculate per-week averages
    weeks = days / 7
    rides_per_week = total_rides / weeks if weeks > 0 else 0
    hours_per_week = (total_duration / 3600) / weeks if weeks > 0 else 0
    
    # Calculate weekly TSS trend
    weekly_tss = calculate_weekly_tss(rides, days)
    
    # Calculate power zones distribution (simplified)
    power_zones = calculate_power_zones(rides, user.current_ftp)
    
    # NEW FEATURE 2: Progress comparison
    progress_comparison = calculate_progress_comparison(user, rides, days)
    
    # NEW FEATURE 4: Monthly stats breakdown
    monthly_stats = calculate_monthly_stats(user, days)
    
    # NEW FEATURE 3: Enhanced insights with progress data
    insights = generate_enhanced_insights(rides, user, total_tss, rides_per_week, hours_per_week, progress_comparison)
    
    return jsonify({
        'total_rides': total_rides,
        'total_distance': round(total_distance, 1),
        'avg_power': round(avg_power, 0),
        'avg_weighted_power': round(avg_weighted_power, 0),
        'avg_intensity': round(avg_intensity, 1),
        'avg_speed': round(avg_speed, 1),
        'max_speed': round(max_speed, 1),
        'max_power': round(max_power, 0),
        'total_tss': round(total_tss, 0),
        'total_work_kj': round(total_work_kj, 1),
        'total_calories': total_calories,
        'rides_per_week': round(rides_per_week, 1),
        'hours_per_week': round(hours_per_week, 1),
        'weekly_tss': weekly_tss,
        'power_zones': power_zones,
        'insights': insights,
        'progress_comparison': progress_comparison,
        'monthly_stats': monthly_stats
    }), 200


# Calculate average speed across all rides
def calculate_avg_speed(rides):
    """Calculate average speed across all rides in km/h"""
    if not rides:
        return 0
    
    speeds = [r.avg_speed for r in rides if r.avg_speed and r.avg_speed > 0]
    return sum(speeds) / len(speeds) if speeds else 0


# Calculate maximum speed across all rides
def calculate_max_speed(rides):
    """Calculate maximum speed achieved across all rides in km/h"""
    if not rides:
        return 0
    
    speeds = [r.max_speed for r in rides if r.max_speed and r.max_speed > 0]
    return max(speeds) if speeds else 0


# Calculate maximum power (peak) across all rides
def calculate_max_power(rides):
    """Calculate maximum power (peak) achieved across all rides in watts"""
    if not rides:
        return 0
    
    powers = [r.max_power for r in rides if r.max_power and r.max_power > 0]
    return max(powers) if powers else 0


# NEW FEATURE 5: Estimate weighted average power
def calculate_estimated_weighted_power(rides):
    """Estimate weighted average power from existing ride data.
    
    Since we don't have second-by-second power data, we estimate weighted power
    using normalized_power if available, or by applying a multiplier to avg_power.
    
    For varied terrain rides, weighted power is typically 5-15% higher than average power.
    We use normalized_power if available (which is similar to weighted power),
    otherwise estimate it as avg_power * 1.08 (8% higher).
    """
    if not rides:
        return 0
    
    weighted_powers = []
    
    for ride in rides:
        # First try to use normalized_power if available (already stored in DB)
        if ride.normalized_power and ride.normalized_power > 0:
            weighted_powers.append(ride.normalized_power)
        # Otherwise estimate from average power
        elif ride.avg_power and ride.avg_power > 0:
            # Estimate: weighted power is typically 8% higher than average for varied rides
            # For very steady rides (like indoor trainer), it would be closer to 1.0
            # We use 1.08 as a reasonable middle ground
            estimated_weighted = ride.avg_power * 1.08
            weighted_powers.append(estimated_weighted)
    
    return sum(weighted_powers) / len(weighted_powers) if weighted_powers else 0


# NEW FEATURE 6: Calculate total work done
def calculate_total_work(rides):
    """Calculate total work done in kilojoules.
    
    Work (kJ) = Average Power (W) × Duration (seconds) / 1000
    
    This is the most accurate way to calculate energy expenditure with a power meter.
    1 kJ ≈ 1 kcal (the conversion is actually 1 kJ = 0.239 kcal, but for cycling
    the body's efficiency means 1 kJ of work ≈ 1 kcal burned).
    """
    total_kj = 0
    
    for ride in rides:
        if ride.avg_power and ride.avg_power > 0 and ride.duration:
            # Work = Power × Time
            # Convert to kJ by dividing by 1000
            ride_work_kj = (ride.avg_power * ride.duration) / 1000
            total_kj += ride_work_kj
    
    return total_kj


# NEW FEATURE 1: Calculate average intensity across all rides
def calculate_avg_intensity(rides, ftp):
    """Calculate average intensity (% of FTP) across all rides"""
    if not ftp or ftp == 0:
        return 0
    
    intensities = []
    for ride in rides:
        if ride.avg_power and ride.avg_power > 0:
            intensity = (ride.avg_power / ftp) * 100
            intensities.append(intensity)
    
    return sum(intensities) / len(intensities) if intensities else 0


# NEW FEATURE 2: Progress comparison
def calculate_progress_comparison(user, current_rides, days):
    """Compare current period performance to previous periods"""
    comparison = {}
    
    # Define comparison periods
    now = datetime.utcnow()
    current_start = now - timedelta(days=days)
    
    # Get previous period data (same length as current period)
    previous_start = current_start - timedelta(days=days)
    previous_rides = Ride.query.filter(
        Ride.user_id == user.id,
        Ride.date >= previous_start,
        Ride.date < current_start
    ).all()
    
    # Calculate metrics for both periods
    current_metrics = calculate_period_metrics(current_rides, user.current_ftp)
    previous_metrics = calculate_period_metrics(previous_rides, user.current_ftp)
    
    # Calculate changes
    comparison['distance'] = {
        'current': round(current_metrics['distance'], 1),
        'previous': round(previous_metrics['distance'], 1),
        'change': round(current_metrics['distance'] - previous_metrics['distance'], 1),
        'change_percent': calculate_percent_change(previous_metrics['distance'], current_metrics['distance'])
    }
    
    comparison['avg_power'] = {
        'current': round(current_metrics['avg_power'], 0),
        'previous': round(previous_metrics['avg_power'], 0),
        'change': round(current_metrics['avg_power'] - previous_metrics['avg_power'], 0),
        'change_percent': calculate_percent_change(previous_metrics['avg_power'], current_metrics['avg_power'])
    }
    
    comparison['avg_intensity'] = {
        'current': round(current_metrics['avg_intensity'], 1),
        'previous': round(previous_metrics['avg_intensity'], 1),
        'change': round(current_metrics['avg_intensity'] - previous_metrics['avg_intensity'], 1),
        'change_percent': calculate_percent_change(previous_metrics['avg_intensity'], current_metrics['avg_intensity'])
    }
    
    comparison['total_tss'] = {
        'current': round(current_metrics['total_tss'], 0),
        'previous': round(previous_metrics['total_tss'], 0),
        'change': round(current_metrics['total_tss'] - previous_metrics['total_tss'], 0),
        'change_percent': calculate_percent_change(previous_metrics['total_tss'], current_metrics['total_tss'])
    }
    
    comparison['ride_count'] = {
        'current': current_metrics['ride_count'],
        'previous': previous_metrics['ride_count'],
        'change': current_metrics['ride_count'] - previous_metrics['ride_count']
    }
    
    return comparison


def calculate_period_metrics(rides, ftp):
    """Calculate aggregate metrics for a period"""
    if not rides:
        return {
            'distance': 0,
            'avg_power': 0,
            'avg_intensity': 0,
            'total_tss': 0,
            'ride_count': 0
        }
    
    total_distance = sum(r.distance for r in rides if r.distance)
    
    power_rides = [r for r in rides if r.avg_power]
    avg_power = sum(r.avg_power for r in power_rides) / len(power_rides) if power_rides else 0
    
    avg_intensity = calculate_avg_intensity(rides, ftp)
    
    total_tss = sum(r.training_stress_score or 0 for r in rides)
    
    return {
        'distance': total_distance,
        'avg_power': avg_power,
        'avg_intensity': avg_intensity,
        'total_tss': total_tss,
        'ride_count': len(rides)
    }


def calculate_percent_change(old_value, new_value):
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 0 if new_value == 0 else 100
    return round(((new_value - old_value) / old_value) * 100, 1)


# NEW FEATURE 4: Monthly stats breakdown
def calculate_monthly_stats(user, days):
    """Calculate month-by-month statistics"""
    now = datetime.utcnow()
    months_data = []
    
    # Get data for last 6 months or requested period
    num_months = min(6, max(1, int(days / 30)))
    
    for i in range(num_months):
        # Calculate month boundaries
        month_end = now - timedelta(days=i * 30)
        month_start = now - timedelta(days=(i + 1) * 30)
        
        # Get rides for this month
        month_rides = Ride.query.filter(
            Ride.user_id == user.id,
            Ride.date >= month_start,
            Ride.date < month_end
        ).all()
        
        if month_rides:
            metrics = calculate_period_metrics(month_rides, user.current_ftp)
            
            # Calculate speed and power metrics for the month
            month_avg_speed = calculate_avg_speed(month_rides)
            month_max_speed = calculate_max_speed(month_rides)
            month_max_power = calculate_max_power(month_rides)
            
            months_data.insert(0, {
                'month': month_start.strftime('%b %Y'),
                'rides': metrics['ride_count'],
                'distance': round(metrics['distance'], 1),
                'avg_power': round(metrics['avg_power'], 0),
                'avg_speed': round(month_avg_speed, 1),
                'max_speed': round(month_max_speed, 1),
                'max_power': round(month_max_power, 0),
                'total_tss': round(metrics['total_tss'], 0)
            })
    
    return months_data


# NEW FEATURE 3: Enhanced insights with progress comparison
def generate_enhanced_insights(rides, user, total_tss, rides_per_week, hours_per_week, progress_comparison):
    """Generate enhanced performance insights with progress comparisons"""
    insights = []
    
    # Training consistency insight
    if rides_per_week >= 4:
        insights.append({
            'type': 'consistency',
            'level': 'positive',
            'message': f"Excellent consistency! You're averaging {rides_per_week:.1f} rides per week."
        })
    elif rides_per_week >= 2:
        insights.append({
            'type': 'consistency',
            'level': 'neutral',
            'message': f"Good training frequency at {rides_per_week:.1f} rides per week. Consider adding 1-2 more rides for faster progress."
        })
    else:
        insights.append({
            'type': 'consistency',
            'level': 'warning',
            'message': f"Training frequency is low at {rides_per_week:.1f} rides per week. Aim for at least 3 rides per week for steady improvement."
        })
    
    # Progress insight - Power
    if progress_comparison.get('avg_power'):
        power_change = progress_comparison['avg_power']['change']
        power_change_pct = progress_comparison['avg_power']['change_percent']
        
        if power_change > 5 and power_change_pct > 2:
            insights.append({
                'type': 'progress',
                'level': 'positive',
                'message': f"Power is trending up! Your average power increased by {abs(power_change):.0f}W ({abs(power_change_pct):.1f}%) compared to the previous period."
            })
        elif power_change < -5 and power_change_pct < -2:
            insights.append({
                'type': 'progress',
                'level': 'warning',
                'message': f"Average power has decreased by {abs(power_change):.0f}W ({abs(power_change_pct):.1f}%). Consider adding more recovery or checking for fatigue."
            })
    
    # Progress insight - Distance
    if progress_comparison.get('distance'):
        distance_change = progress_comparison['distance']['change']
        distance_change_pct = progress_comparison['distance']['change_percent']
        
        if distance_change > 10 and distance_change_pct > 10:
            insights.append({
                'type': 'volume',
                'level': 'positive',
                'message': f"Great work! You've increased your riding volume by {abs(distance_change):.1f} km ({abs(distance_change_pct):.1f}%) compared to the previous period."
            })
        elif distance_change < -10 and distance_change_pct < -10:
            insights.append({
                'type': 'volume',
                'level': 'neutral',
                'message': f"Your riding volume decreased by {abs(distance_change):.1f} km ({abs(distance_change_pct):.1f}%). This might be intentional recovery or a sign to get back on the bike."
            })
    
    # Training load insight with context
    weekly_tss = total_tss / (len(rides) / max(rides_per_week, 1)) if rides_per_week > 0 else 0
    
    if weekly_tss > 450:
        recovery_days = 5
        insights.append({
            'type': 'training_load',
            'level': 'warning',
            'message': f"High training load ({weekly_tss:.0f} TSS/week). You need approximately {recovery_days} days to fully recover. Make sure you're getting adequate rest."
        })
    elif weekly_tss > 250:
        recovery_days = 3
        insights.append({
            'type': 'training_load',
            'level': 'positive',
            'message': f"Moderate training load ({weekly_tss:.0f} TSS/week) with ~{recovery_days} days recovery time - good balance for steady improvement."
        })
    elif weekly_tss > 100:
        recovery_days = 2
        insights.append({
            'type': 'training_load',
            'level': 'neutral',
            'message': f"Light training load ({weekly_tss:.0f} TSS/week) with ~{recovery_days} days recovery time. Consider gradually increasing volume for faster FTP gains."
        })
    
    # Intensity insight
    if progress_comparison.get('avg_intensity'):
        current_intensity = progress_comparison['avg_intensity']['current']
        
        if current_intensity > 85:
            insights.append({
                'type': 'intensity',
                'level': 'warning',
                'message': f"Your average ride intensity is high at {current_intensity:.0f}% of FTP. Balance hard efforts with easier recovery rides."
            })
        elif current_intensity >= 65 and current_intensity <= 75:
            insights.append({
                'type': 'intensity',
                'level': 'positive',
                'message': f"Perfect intensity balance at {current_intensity:.0f}% of FTP - ideal for building aerobic endurance."
            })
    
    # Goals-based insight
    if user.training_goals:
        insights.append({
            'type': 'goals',
            'level': 'neutral',
            'message': f"Keep working towards your goal: {user.training_goals}"
        })
    
    return insights


def calculate_weekly_tss(rides, days):
    """Calculate TSS and other metrics per week for chart"""
    weeks = min(int(days / 7), 12)  # Max 12 weeks for chart
    weekly_data = []
    
    now = datetime.utcnow()
    for week in range(weeks):
        week_start = now - timedelta(days=(week + 1) * 7)
        week_end = now - timedelta(days=week * 7)
        
        week_rides = [r for r in rides if week_start <= r.date < week_end]
        week_tss = sum(r.training_stress_score or 0 for r in week_rides)
        
        # Calculate speed metrics for the week
        week_avg_speed = calculate_avg_speed(week_rides)
        week_max_speed = calculate_max_speed(week_rides)
        week_max_power = calculate_max_power(week_rides)
        
        weekly_data.insert(0, {
            'week': weeks - week,
            'tss': round(week_tss, 1),
            'avg_speed': round(week_avg_speed, 1),
            'max_speed': round(week_max_speed, 1),
            'max_power': round(week_max_power, 0)
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
    """DEPRECATED: Use generate_enhanced_insights instead"""
    # Keep for backwards compatibility
    return generate_enhanced_insights(rides, user, total_tss, rides_per_week, hours_per_week, {})




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


