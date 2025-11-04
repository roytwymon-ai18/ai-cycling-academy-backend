import os
from openai import OpenAI
import json

# Initialize OpenAI client (API key is pre-configured in environment)
client = OpenAI()

def analyze_ride_with_ai(ride):
    """
    Analyze a ride using AI and provide coaching insights
    """
    
    # Prepare ride data for analysis
    ride_data = {
        'name': ride.name,
        'duration': ride.duration,
        'distance': ride.distance,
        'avg_power': ride.avg_power,
        'max_power': ride.max_power,
        'normalized_power': ride.normalized_power,
        'ftp': ride.ftp,
        'intensity_factor': ride.intensity_factor,
        'training_stress_score': ride.training_stress_score,
        'avg_heart_rate': ride.avg_heart_rate,
        'max_heart_rate': ride.max_heart_rate,
        'avg_speed': ride.avg_speed,
        'avg_cadence': ride.avg_cadence,
        'elevation_gain': ride.elevation_gain,
        'power_zones': {
            'zone_1': ride.time_in_zone_1,
            'zone_2': ride.time_in_zone_2,
            'zone_3': ride.time_in_zone_3,
            'zone_4': ride.time_in_zone_4,
            'zone_5': ride.time_in_zone_5,
            'zone_6': ride.time_in_zone_6,
            'zone_7': ride.time_in_zone_7
        }
    }
    
    # Create analysis prompt
    prompt = f"""
    As an expert cycling coach, analyze this ride data and provide detailed insights:

    Ride Data:
    {json.dumps(ride_data, indent=2)}

    Please provide:
    1. Performance Analysis: Key metrics and what they indicate about fitness/effort
    2. Training Zones: Analysis of time spent in different power zones
    3. Strengths: What the rider did well in this session
    4. Areas for Improvement: Specific aspects to work on
    5. Recovery Recommendations: Based on training stress and intensity
    6. Next Training Focus: What type of training should follow this session

    Format your response as JSON with these sections:
    {{
        "performance_analysis": "detailed analysis",
        "zone_analysis": "power zone breakdown and insights",
        "strengths": ["strength 1", "strength 2"],
        "improvements": ["improvement 1", "improvement 2"],
        "recovery": "recovery recommendations",
        "next_focus": "next training recommendations"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are an expert cycling coach with deep knowledge of power-based training, physiology, and performance analysis. Provide detailed, actionable coaching advice."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        # Parse the AI response
        ai_response = response.choices[0].message.content
        
        # Try to parse as JSON, fallback to text if needed
        try:
            analysis_json = json.loads(ai_response)
            return {
                'analysis': analysis_json,
                'recommendations': analysis_json.get('next_focus', 'Continue with your current training plan.')
            }
        except json.JSONDecodeError:
            return {
                'analysis': {'raw_response': ai_response},
                'recommendations': 'Continue with your current training plan and monitor your progress.'
            }
            
    except Exception as e:
        print(f"AI analysis error: {e}")
        return {
            'analysis': {'error': 'Analysis temporarily unavailable'},
            'recommendations': 'Continue with your planned training and try analysis again later.'
        }

def generate_training_plan(user, goal, weeks=4):
    """
    Generate a structured training plan based on user profile and goals
    """
    
    user_profile = {
        'current_ftp': user.current_ftp,
        'weight': user.weight,
        'max_heart_rate': user.max_heart_rate,
        'resting_heart_rate': user.resting_heart_rate
    }
    
    prompt = f"""
    As an expert cycling coach, create a {weeks}-week structured training plan for this cyclist:

    Cyclist Profile:
    {json.dumps(user_profile, indent=2)}

    Training Goal: {goal}

    Create a periodized plan with:
    1. Weekly structure (days per week, workout types)
    2. Progressive overload and recovery weeks
    3. Specific workout descriptions with power zones
    4. Adaptation guidelines based on actual performance data

    Format as JSON:
    {{
        "plan_overview": "description of the plan approach",
        "weeks": [
            {{
                "week": 1,
                "focus": "week focus",
                "workouts": [
                    {{
                        "day": "Monday",
                        "type": "workout type",
                        "description": "detailed workout",
                        "duration": "minutes",
                        "intensity": "zone/percentage"
                    }}
                ]
            }}
        ],
        "adaptation_notes": "how to adapt based on performance data"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are an expert cycling coach specializing in power-based training and periodization. Create detailed, progressive training plans."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        ai_response = response.choices[0].message.content
        
        try:
            return json.loads(ai_response)
        except json.JSONDecodeError:
            return {'error': 'Failed to generate structured plan', 'raw_response': ai_response}
            
    except Exception as e:
        print(f"Training plan generation error: {e}")
        return {'error': 'Plan generation temporarily unavailable'}

def chat_with_ai_coach(user, message, context=None):
    """
    Chat interface with AI cycling coach
    """
    
    # Build context from user's recent rides and profile
    user_context = f"""
    Cyclist Profile:
    - Current FTP: {user.current_ftp or 'Unknown'}
    - Weight: {user.weight or 'Unknown'} kg
    - Max HR: {user.max_heart_rate or 'Unknown'} bpm
    - Subscription: {user.subscription_tier}
    """
    
    if context:
        user_context += f"\nRecent Activity Context:\n{context}"
    
    system_prompt = f"""
    You are an expert AI cycling coach. You have access to this cyclist's profile and training data:
    
    {user_context}
    
    Provide personalized, actionable coaching advice. Be encouraging but honest about areas for improvement. 
    Reference their specific data when relevant. Keep responses conversational but professional.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.8,
            max_tokens=800
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"AI chat error: {e}")
        return "I'm having trouble connecting right now. Please try again in a moment, or feel free to ask about your training data and goals."

