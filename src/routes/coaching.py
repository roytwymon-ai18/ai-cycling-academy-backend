from flask import Blueprint, request, jsonify, session
from src.models.user import User, db
from src.models.ride import Ride
from src.models.chat_message import ChatMessage
from src.utils.ai_analysis import chat_with_ai_coach, generate_training_plan
from datetime import datetime, timedelta
import json

coaching_bp = Blueprint('coaching', __name__)

def require_auth():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

@coaching_bp.route('/coaching/chat', methods=['POST'])
def chat_with_coach():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
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
    if user.training_goals:
        context += f"Training Goals: {user.training_goals}\n"
    context += "\n"
    
    if recent_rides:
        context += "Recent rides (last 7 days):\n"
        for ride in recent_rides:
            context += f"- {ride.name}: {ride.avg_power}W avg, {ride.training_stress_score:.1f} TSS\n"
        context += "\n"
    
    # Add conversation history for continuity
    if chat_history:
        context += "Previous conversation context:\n"
        for msg in chat_history[-10:]:  # Last 10 messages for context
            context += f"{msg.role}: {msg.content[:100]}...\n"
        context += "\n"
    
    context += "Remember past conversations and provide personalized, contextual coaching advice.\n"
    
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

@coaching_bp.route('/coaching/suggested-goals', methods=['GET'])
def get_training_goals():
    """Get suggested training goals based on user profile and recent performance"""
    user = require_auth()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Analyze recent performance to suggest goals
    recent_rides = Ride.query.filter(
        Ride.user_id == user.id,
        Ride.date >= datetime.utcnow() - timedelta(days=30)
    ).all()
    
    suggested_goals = [
        {
            'id': 'ftp_improvement',
            'title': 'Increase FTP by 5-10%',
            'description': 'Structured plan to improve functional threshold power',
            'duration': '8-12 weeks',
            'suitable_for': 'All levels'
        },
        {
            'id': 'endurance_base',
            'title': 'Build Aerobic Base',
            'description': 'Focus on zone 2 endurance and fat adaptation',
            'duration': '6-8 weeks',
            'suitable_for': 'All levels'
        },
        {
            'id': 'vo2_max',
            'title': 'Improve VO2 Max',
            'description': 'High-intensity intervals to boost maximum oxygen uptake',
            'duration': '4-6 weeks',
            'suitable_for': 'Intermediate to advanced'
        },
        {
            'id': 'race_prep',
            'title': 'Race Preparation',
            'description': 'Event-specific training with tapering strategy',
            'duration': '12-16 weeks',
            'suitable_for': 'Competitive cyclists'
        }
    ]
    
    # Customize recommendations based on recent data
    if recent_rides:
        avg_intensity = sum(ride.intensity_factor for ride in recent_rides if ride.intensity_factor) / len([r for r in recent_rides if r.intensity_factor])
        if avg_intensity and avg_intensity < 0.7:
            # Low intensity suggests need for base building
            suggested_goals[1]['recommended'] = True
        elif avg_intensity and avg_intensity > 0.9:
            # High intensity suggests need for recovery/base
            suggested_goals[1]['recommended'] = True
        else:
            # Moderate intensity suggests ready for FTP work
            suggested_goals[0]['recommended'] = True
    
    return jsonify({
        'suggested_goals': suggested_goals,
        'custom_goal_option': True
    }), 200


