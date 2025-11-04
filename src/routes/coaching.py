from flask import Blueprint, request, jsonify, session
from src.models.user import User, db
from src.models.ride import Ride
from src.models.chat_message import ChatMessage
from src.models.client_profile import ClientProfile
from src.utils.ai_analysis import chat_with_ai_coach, generate_training_plan
from datetime import datetime, timedelta
import json

coaching_bp = Blueprint('coaching', __name__)

# Onboarding interview questions
ONBOARDING_QUESTIONS = [
    {
        'step': 1,
        'question': "Hey! Before we talk goals or training plans, I want to hear the fun part first… What's your cycling story? How did bikes show up in your life?",
        'field': 'cycling_story',
        'follow_up': "That's awesome! I love hearing cycling origin stories. 🚴"
    },
    {
        'step': 2,
        'question': "What type of riding do you enjoy most right now — road, gravel, MTB, indoor trainer?",
        'field': 'rider_type'
    },
    {
        'step': 3,
        'question': "Describe your best recent ride. What made it great?",
        'field': 'best_ride_description'
    },
    {
        'step': 4,
        'question': "Any cycling victories or proud moments? Big or small.",
        'field': 'proud_moments'
    },
    {
        'step': 5,
        'question': "How often do you ride now, and what does a normal week look like?",
        'field': 'weekly_ride_frequency'
    },
    {
        'step': 6,
        'question': "Do you use any tech? Power meter, HR strap, GPS bike computer, or apps like Strava, Garmin, or TrainerRoad?",
        'field': 'tech_equipment'
    },
    {
        'step': 7,
        'question': "What are your cycling goals for the next 3–12 months? (Examples: faster group rides, climbing, endurance, crit racing, weight loss)",
        'field': 'primary_goals'
    },
    {
        'step': 8,
        'question': "Why are these goals important to you? What's the deeper motivation?",
        'field': 'deep_motivation'
    },
    {
        'step': 9,
        'question': "What are your current challenges — time, consistency, training knowledge, confidence, injuries?",
        'field': 'current_challenges'
    },
    {
        'step': 10,
        'question': "How many days per week could you realistically train — even on a busy week?",
        'field': 'training_availability'
    },
    {
        'step': 11,
        'question': "How do you like to be coached? (Tough love accountability / Collaborative partnership / Data-driven & analytical / Motivational & mindset)",
        'field': 'coaching_style_preference'
    },
    {
        'step': 12,
        'question': "If we crushed the next 12 months, what would success LOOK and FEEL like to you?",
        'field': 'success_vision'
    }
]

def require_auth():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

def get_or_create_profile(user):
    """Get existing profile or create new one"""
    profile = ClientProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        profile = ClientProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
    return profile

def generate_profile_summary(profile, user):
    """Use AI to generate skill assessment and action items"""
    prompt = f"""Based on this cyclist's onboarding interview, create a brief assessment and first 3 action items.

CYCLIST PROFILE:
- Rider Type: {profile.rider_type}
- Goals: {profile.primary_goals}
- Motivation: {profile.deep_motivation}
- Weekly Frequency: {profile.weekly_ride_frequency}
- Tech/Equipment: {profile.tech_equipment}
- Challenges: {profile.current_challenges}
- Training Availability: {profile.training_availability}
- Coaching Preference: {profile.coaching_style_preference}

Provide:
1. Skill + Fitness Assessment (2-3 sentences)
2. First 3 Action Items (specific, actionable)

Format as:
ASSESSMENT: [your assessment]
ACTIONS:
1. [action 1]
2. [action 2]
3. [action 3]
"""
    
    try:
        response = chat_with_ai_coach(user, prompt, "You are Coach Manee analyzing a new client's profile.")
        
        # Parse response
        if "ASSESSMENT:" in response and "ACTIONS:" in response:
            parts = response.split("ACTIONS:")
            assessment = parts[0].replace("ASSESSMENT:", "").strip()
            actions = parts[1].strip()
            
            profile.skill_fitness_assessment = assessment
            profile.action_items = actions
            db.session.commit()
    except Exception as e:
        print(f"Error generating profile summary: {e}")

@coaching_bp.route('/coaching/chat', methods=['POST'])
def chat_with_coach():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    # Get or create client profile
    profile = get_or_create_profile(user)
    
    # Check if onboarding is needed
    if not profile.onboarding_completed:
        # Handle onboarding interview
        current_step = profile.onboarding_step
        
        # Save user's response to previous question
        if current_step > 0 and current_step <= len(ONBOARDING_QUESTIONS):
            prev_question = ONBOARDING_QUESTIONS[current_step - 1]
            field_name = prev_question['field']
            setattr(profile, field_name, message)
            db.session.commit()
        
        # Save user message to history
        user_msg = ChatMessage(
            user_id=user.id,
            role='user',
            content=message
        )
        db.session.add(user_msg)
        
        # Move to next question
        next_step = current_step + 1
        
        if next_step <= len(ONBOARDING_QUESTIONS):
            # Ask next question
            next_question = ONBOARDING_QUESTIONS[next_step - 1]
            response = next_question['question']
            
            # Add follow-up if exists
            if current_step > 0 and 'follow_up' in ONBOARDING_QUESTIONS[current_step - 1]:
                response = ONBOARDING_QUESTIONS[current_step - 1]['follow_up'] + "\n\n" + response
            
            profile.onboarding_step = next_step
            db.session.commit()
        else:
            # Onboarding complete!
            profile.onboarding_completed = True
            db.session.commit()
            
            # Generate AI assessment and action items
            generate_profile_summary(profile, user)
            
            # Create completion message with profile summary
            response = f"""🎉 Awesome! I've got a great picture of who you are as a cyclist and what you want to achieve.

{profile.get_profile_summary()}

I'm excited to work with you! I'll remember everything we've discussed, and my coaching will get more personalized with every conversation.

What would you like to focus on first?"""
        
        # Save assistant response to history
        assistant_msg = ChatMessage(
            user_id=user.id,
            role='assistant',
            content=response
        )
        db.session.add(assistant_msg)
        db.session.commit()
        
        return jsonify({
            'response': response,
            'timestamp': datetime.utcnow().isoformat(),
            'onboarding_step': profile.onboarding_step,
            'onboarding_completed': profile.onboarding_completed
        }), 200
    
    # Normal coaching conversation (after onboarding)
    # Save user message to history
    user_msg = ChatMessage(
        user_id=user.id,
        role='user',
        content=message
    )
    db.session.add(user_msg)
    
    # Get conversation history (last 20 messages for context)
    chat_history = ChatMessage.query.filter_by(
        user_id=user.id
    ).order_by(ChatMessage.created_at.desc()).limit(20).all()
    chat_history.reverse()  # Chronological order
    
    # Get recent rides for context
    recent_rides = Ride.query.filter(
        Ride.user_id == user.id,
        Ride.date >= datetime.utcnow() - timedelta(days=7)
    ).order_by(Ride.date.desc()).limit(3).all()
    
    # Build context with user profile and history
    context = f"You are Coach Manee, a personalized AI cycling coach.\n"
    context += f"Athlete: {user.username}\n"
    context += f"FTP: {user.current_ftp}W\n"
    
    # Add client profile for personalization
    if profile.onboarding_completed:
        context += "\n" + profile.get_profile_summary() + "\n"
    
    if recent_rides:
        context += "\nRecent rides (last 7 days):\n"
        for ride in recent_rides:
            context += f"- {ride.name}: {ride.avg_power}W avg, {ride.training_stress_score:.1f} TSS\n"
        context += "\n"
    
    # Add conversation history for continuity
    if chat_history:
        context += "Previous conversation context:\n"
        for msg in chat_history[-10:]:  # Last 10 messages for context
            context += f"{msg.role}: {msg.content[:100]}...\n"
        context += "\n"
    
    context += "Remember past conversations and provide personalized, contextual coaching advice based on their profile.\n"
    
    try:
        response = chat_with_ai_coach(user, message, context)
        
        # Save assistant response to history
        assistant_msg = ChatMessage(
            user_id=user.id,
            role='assistant',
            content=response
        )
        db.session.add(assistant_msg)
        db.session.commit()
        
        return jsonify({
            'response': response,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Chat failed: {str(e)}'}), 500

@coaching_bp.route('/coaching/profile', methods=['GET'])
def get_client_profile():
    """Get the client's cycling profile"""
    user = require_auth()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    profile = get_or_create_profile(user)
    
    return jsonify({
        'profile': profile.to_dict(),
        'summary': profile.get_profile_summary() if profile.onboarding_completed else None
    }), 200

@coaching_bp.route('/coaching/chat/history', methods=['GET'])
def get_chat_history():
    """Retrieve chat history for the current user"""
    user = require_auth()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get all chat messages for this user
    messages = ChatMessage.query.filter_by(
        user_id=user.id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    return jsonify({
        'messages': [msg.to_dict() for msg in messages],
        'total_messages': len(messages)
    }), 200

@coaching_bp.route('/coaching/training-plan', methods=['POST'])
def create_training_plan():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    goal = data.get('goal', 'Improve general fitness')
    weeks = data.get('weeks', 4)
    
    try:
        plan = generate_training_plan(user, goal, weeks)
        return jsonify({
            'plan': plan,
            'created_at': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': f'Plan generation failed: {str(e)}'}), 500

@coaching_bp.route('/coaching/insights', methods=['GET'])
def get_coaching_insights():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get recent rides (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_rides = Ride.query.filter(
        Ride.user_id == user.id,
        Ride.date >= thirty_days_ago
    ).order_by(Ride.date.desc()).all()
    
    # Calculate summary stats
    total_tss = sum(r.training_stress_score or 0 for r in recent_rides)
    weekly_tss = total_tss / 4.3  # Approximate weeks in 30 days
    rides_per_week = len(recent_rides) / 4.3
    total_hours = sum(r.duration for r in recent_rides) / 3600
    
    # Generate insights based on goals and training
    insights = {
        'weekly_summary': f"{rides_per_week:.1f} rides/week, {total_hours:.1f} hours total",
        'training_load': f"{weekly_tss:.0f} TSS/week - {'Light' if weekly_tss < 250 else 'Moderate' if weekly_tss < 450 else 'High'} load"
    }
    
    if user.training_goals:
        insights['recommendation'] = f"Focus on: {user.training_goals}"
    else:
        insights['recommendation'] = "Set your training goals in Profile to get personalized recommendations"
    
    return jsonify({'insights': insights}), 200

@coaching_bp.route('/coaching/goals', methods=['GET', 'POST'])
def manage_goals():
    """Get or update user training goals"""
    user = require_auth()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if request.method == 'POST':
        # Update goals
        data = request.get_json()
        goals = data.get('goals', '').strip()
        user.training_goals = goals
        db.session.commit()
        return jsonify({
            'success': True,
            'goals': user.training_goals
        }), 200
    
    # GET - return current goals
    return jsonify({'goals': user.training_goals}), 200

