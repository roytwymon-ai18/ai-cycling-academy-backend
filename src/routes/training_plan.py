from flask import Blueprint, request, jsonify, session
from src.models.user import User, db
from src.models.ride import Ride
from src.models.client_profile import ClientProfile
from datetime import datetime, timedelta
from openai import OpenAI

training_plan_bp = Blueprint('training_plan', __name__)

def require_auth():
    """Check if user is authenticated"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


@training_plan_bp.route('/training-plan/generate', methods=['POST'])
def generate_training_plan():
    """Generate a dynamic 7-day training plan based on user goals and recent rides"""
    user = require_auth()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json() or {}
    
    # Get or create user profile
    profile = ClientProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        profile = ClientProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
    
    # Get recent rides (last 14 days)
    two_weeks_ago = datetime.utcnow() - timedelta(days=14)
    recent_rides = Ride.query.filter(
        Ride.user_id == user.id,
        Ride.date >= two_weeks_ago
    ).order_by(Ride.date.desc()).all()
    
    # Generate plan using AI
    try:
        print(f"Generating training plan for user {user.id}...")
        plan = generate_ai_training_plan(user, profile, recent_rides, data)
        print(f"Plan generated successfully: {plan.get('week_focus', 'No focus')}")
        return jsonify(plan), 200
    except Exception as e:
        import traceback
        print(f"Error generating training plan: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Failed to generate training plan: {str(e)}'}), 500


@training_plan_bp.route('/training-plan/current', methods=['GET'])
def get_current_training_plan():
    """Get the current 7-day training plan"""
    user = require_auth()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get or create user profile
    profile = ClientProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        profile = ClientProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
    
    # Get recent rides for context
    two_weeks_ago = datetime.utcnow() - timedelta(days=14)
    recent_rides = Ride.query.filter(
        Ride.user_id == user.id,
        Ride.date >= two_weeks_ago
    ).order_by(Ride.date.desc()).all()
    
    # Generate fresh plan
    try:
        plan = generate_ai_training_plan(user, profile, recent_rides, {})
        return jsonify(plan), 200
    except Exception as e:
        print(f"Error getting training plan: {str(e)}")
        return jsonify({'error': 'Failed to get training plan'}), 500


def generate_ai_training_plan(user, profile, recent_rides, user_params):
    """Generate a 7-day training plan using AI based on user goals and recent activity"""
    client = OpenAI()
    
    # Build user context
    user_context = f"""
User Profile:
- Goals: {profile.primary_goals or user.training_goals or 'General fitness improvement'}
- Rider Type: {profile.rider_type or 'Road cycling'}
- Training Availability: {profile.training_availability or '4-5 days per week'}
- Current FTP: {user.current_ftp or 'Not set'}W
- Experience Level: {user.training_experience or 'Intermediate'}
"""
    
    # Build recent activity context
    if recent_rides:
        total_rides = len(recent_rides)
        total_distance = sum(r.distance for r in recent_rides)
        total_time = sum(r.duration for r in recent_rides) / 3600  # hours
        avg_tss = sum(r.training_stress_score or 0 for r in recent_rides) / total_rides if total_rides > 0 else 0
        
        activity_context = f"""
Recent Activity (Last 14 days):
- Total Rides: {total_rides}
- Total Distance: {total_distance:.1f} km ({total_distance * 0.621371:.1f} miles)
- Total Time: {total_time:.1f} hours
- Average TSS per ride: {avg_tss:.0f}
- Rides per week: {total_rides / 2:.1f}
"""
        
        # Add last ride details
        if recent_rides:
            last_ride = recent_rides[0]
            activity_context += f"""
Last Ride:
- Date: {last_ride.date.strftime('%Y-%m-%d') if last_ride.date else 'Unknown'}
- Distance: {last_ride.distance:.1f} km
- Duration: {last_ride.duration // 60} minutes
"""
            if last_ride.avg_power:
                activity_context += f"- Avg Power: {last_ride.avg_power}W\n"
            if last_ride.training_stress_score:
                activity_context += f"- TSS: {last_ride.training_stress_score}\n"
    else:
        activity_context = """
Recent Activity (Last 14 days):
- No rides recorded yet
- This is a new training plan to get started
"""
    
    # Get user-specified parameters
    target_ftp = user_params.get('target_ftp', user.current_ftp)
    plan_duration = user_params.get('duration', 12)  # weeks
    rides_per_week = user_params.get('rides_per_week', 4)
    hours_per_week = user_params.get('hours_per_week', 6)
    
    # Create prompt with elite coaching methodology
    coaching_methodology = """
COACHING METHODOLOGY & BEST PRACTICES:

1. PERIODIZATION PRINCIPLES (Joe Friel, Hunter Allen, Andrew Coggan):
   - Base Phase: Build aerobic endurance (65-75% FTP, Zone 2)
   - Build Phase: Develop threshold and VO2max (85-105% FTP, Zones 3-5)
   - Peak Phase: Race-specific intensity with reduced volume
   - Recovery: 3:1 or 4:1 work-to-recovery ratio (3-4 weeks hard, 1 week easy)

2. TRAINING ZONES (Based on FTP):
   - Zone 1 (Active Recovery): <55% FTP
   - Zone 2 (Endurance): 56-75% FTP - aerobic base building
   - Zone 3 (Tempo): 76-90% FTP - sustainable power
   - Zone 4 (Threshold): 91-105% FTP - lactate threshold
   - Zone 5 (VO2max): 106-120% FTP - maximal aerobic
   - Zone 6 (Anaerobic): 121-150% FTP - anaerobic capacity
   - Zone 7 (Neuromuscular): >150% FTP - sprint power

3. WEEKLY STRUCTURE (British Cycling, USA Cycling):
   - 2-3 high-intensity sessions per week maximum
   - 1-2 long endurance rides (Zone 2)
   - 1-2 recovery/rest days
   - Hard days followed by easy days
   - Quality over quantity - avoid junk miles

4. WORKOUT TYPES BY DISCIPLINE:
   Road Racing:
   - Sweet Spot: 88-93% FTP, 2x20min or 3x15min
   - Threshold: 95-105% FTP, 2x8min or 3x8min
   - VO2max: 110-120% FTP, 5x5min or 4x8min
   
   Time Trial/Triathlon:
   - Sustained threshold: 95-100% FTP, 2x20-30min
   - Race pace intervals: 100-105% FTP, 3x10-15min
   - Aerobic endurance: 65-75% FTP, 2-4 hours
   
   Gran Fondo/Endurance:
   - Long Zone 2: 65-75% FTP, 3-6 hours
   - Tempo: 80-85% FTP, 2x30min or 3x20min
   - Climbing repeats: 85-95% FTP, varied duration
   
   Criterium/Track:
   - Short intervals: 120-150% FTP, 30s-2min
   - Anaerobic capacity: 150%+ FTP, 15-30s sprints
   - Race simulation: varied intensity

5. TSS GUIDELINES (Training Stress Score):
   - Beginner: 200-400 TSS/week
   - Intermediate: 400-600 TSS/week
   - Advanced: 600-900 TSS/week
   - Elite: 900-1200+ TSS/week
   - Single workout: 50-150 TSS typical

6. RECOVERY PRINCIPLES:
   - Easy week every 3-4 weeks (50-60% normal volume)
   - 24-48 hours between hard sessions
   - Active recovery rides: <55% FTP, 30-60min
   - Sleep, nutrition, hydration are critical

7. PROGRESSION:
   - Increase volume OR intensity, never both simultaneously
   - 10% rule: increase weekly volume by max 10%
   - Build fitness gradually over 8-12 week blocks
"""

    prompt = f"""{coaching_methodology}

As an expert cycling coach trained in the methodologies of Joe Friel, Hunter Allen, Andrew Coggan, and elite programs like British Cycling and USA Cycling, create a detailed 7-day training plan for the next week.

{user_context}

{activity_context}

Plan Parameters:
- Target FTP: {target_ftp}W
- Overall Plan Duration: {plan_duration} weeks
- Target Rides per Week: {rides_per_week}
- Target Hours per Week: {hours_per_week}

Create a 7-day plan (starting tomorrow) following these requirements:

1. Apply proper periodization based on where they are in their training cycle
2. Use correct training zones and intensities based on FTP
3. Follow the 3:1 or 4:1 work-to-recovery ratio
4. Include discipline-specific workouts aligned with their goals
5. Calculate realistic TSS for each workout and weekly total
6. Ensure proper recovery between hard sessions
7. Make workouts progressive and purposeful

Format as JSON:
{{
  "week_focus": "Brief description of this week's training focus and periodization phase",
  "weekly_tss_target": estimated total TSS for the week (realistic based on their current volume),
  "periodization_phase": "Base/Build/Peak/Recovery",
  "days": [
    {{
      "day": "Monday",
      "date": "YYYY-MM-DD",
      "workout_type": "Rest/Recovery/Endurance/Tempo/Threshold/VO2max/Anaerobic/Sprint",
      "duration_minutes": 0,
      "intensity": "Zone X (XX-XX% FTP)",
      "tss": estimated TSS for this workout,
      "description": "Detailed workout with specific intervals, rest periods, and structure",
      "focus": "Physiological adaptation and purpose",
      "coaching_notes": "Key execution points and what to focus on"
    }},
    ...
  ]
}}

IMPORTANT: Base all recommendations on proven training science. Be specific with intervals (e.g., '3x8min @ 95-100% FTP, 4min recovery'). Ensure the plan is realistic and sustainable."""
    
    # Call OpenAI API
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are Coach Manee, a legendary cycling coach with over 30 years of experience at the highest levels of competitive cycling. You've coached World Champions, Olympians, and national champions across all cycling disciplines. Your training plans are based on proven methodologies from Joe Friel, Hunter Allen, Andrew Coggan, and your own decades of pioneering experience. You understand periodization, training zones, TSS, and how to balance intensity with recovery. Your plans have produced amazing results for athletes at all levels. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        import json
        plan_data = json.loads(response.choices[0].message.content)
        
        # Add dates to each day
        today = datetime.utcnow().date()
        for i, day in enumerate(plan_data.get('days', [])):
            day_date = today + timedelta(days=i+1)
            day['date'] = day_date.isoformat()
            day['day'] = day_date.strftime('%A')
        
        return plan_data
        
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        # Return a basic fallback plan
        return generate_fallback_plan()


def generate_fallback_plan():
    """Generate a science-based fallback plan following elite coaching principles"""
    today = datetime.utcnow().date()
    days = []
    
    # Base phase training week following periodization principles
    workout_schedule = [
        {
            "type": "Endurance",
            "duration": 60,
            "intensity": "Zone 2 (65-75% FTP)",
            "tss": 50,
            "description": "60min Zone 2 endurance ride. Maintain steady aerobic pace. Focus on smooth pedaling at 85-95 RPM.",
            "focus": "Aerobic base development",
            "coaching_notes": "Keep power steady in Zone 2. This builds mitochondrial density and fat oxidation."
        },
        {
            "type": "Rest",
            "duration": 0,
            "intensity": "N/A",
            "tss": 0,
            "description": "Complete rest day. Focus on recovery, nutrition, and sleep.",
            "focus": "Recovery and adaptation",
            "coaching_notes": "Rest is when your body adapts and gets stronger. Don't skip it."
        },
        {
            "type": "Threshold",
            "duration": 75,
            "intensity": "Zone 4 (91-105% FTP)",
            "tss": 85,
            "description": "Warm-up 15min Zone 2, then 3x8min @ 95-100% FTP with 4min recovery between intervals, cool-down 10min.",
            "focus": "Lactate threshold development",
            "coaching_notes": "These intervals should feel 'comfortably hard'. Maintain consistent power throughout each interval."
        },
        {
            "type": "Recovery",
            "duration": 45,
            "intensity": "Zone 1 (<55% FTP)",
            "tss": 20,
            "description": "45min easy spin. Keep intensity very low. Focus on leg turnover and recovery.",
            "focus": "Active recovery",
            "coaching_notes": "This should feel ridiculously easy. The goal is blood flow for recovery, not fitness."
        },
        {
            "type": "Sweet Spot",
            "duration": 90,
            "intensity": "Zone 3 (88-93% FTP)",
            "tss": 75,
            "description": "Warm-up 15min, then 2x20min @ 88-93% FTP with 5min recovery, cool-down 10min.",
            "focus": "Sweet spot training - high training stimulus with manageable fatigue",
            "coaching_notes": "Sweet spot is the 'sweet spot' between endurance and threshold. Very effective for building FTP."
        },
        {
            "type": "Rest",
            "duration": 0,
            "intensity": "N/A",
            "tss": 0,
            "description": "Rest day to prepare for weekend long ride.",
            "focus": "Recovery",
            "coaching_notes": "Save your energy for tomorrow's long ride."
        },
        {
            "type": "Long Endurance",
            "duration": 150,
            "intensity": "Zone 2 (65-75% FTP)",
            "tss": 120,
            "description": "2.5 hour Zone 2 endurance ride. Maintain steady aerobic pace. Practice nutrition and hydration strategies.",
            "focus": "Aerobic endurance and metabolic efficiency",
            "coaching_notes": "Long rides build aerobic capacity and teach your body to burn fat. Stay in Zone 2 even when it feels easy."
        }
    ]
    
    for i, workout in enumerate(workout_schedule):
        day_date = today + timedelta(days=i+1)
        days.append({
            "day": day_date.strftime('%A'),
            "date": day_date.isoformat(),
            "workout_type": workout["type"],
            "duration_minutes": workout["duration"],
            "intensity": workout["intensity"],
            "tss": workout["tss"],
            "description": workout["description"],
            "focus": workout["focus"],
            "coaching_notes": workout["coaching_notes"]
        })
    
    return {
        "week_focus": "Base phase training - building aerobic endurance and threshold power following periodization principles",
        "weekly_tss_target": 350,
        "periodization_phase": "Base",
        "days": days
    }

