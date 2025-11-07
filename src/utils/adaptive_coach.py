"""
Adaptive AI Coach with Training Plan Modification Capabilities
Uses OpenAI function calling to enable Coach Manee to adjust training plans
"""

from openai import OpenAI
import json
from datetime import datetime, timedelta
from src.utils.plan_adjustments import (
    adjust_workout_intensity,
    reschedule_workout,
    swap_workout_type,
    add_rest_day,
    adjust_weekly_volume,
    get_plan_adjustments
)

# Initialize OpenAI client
client = OpenAI()

# Define available functions for Coach Manee
COACH_FUNCTIONS = [
    {
        "name": "adjust_workout_intensity",
        "description": "Modify the intensity (TSS) of a specific workout based on athlete feedback about fatigue, readiness, or life circumstances",
        "parameters": {
            "type": "object",
            "properties": {
                "workout_id": {
                    "type": "integer",
                    "description": "The ID of the workout to adjust"
                },
                "new_tss": {
                    "type": "integer",
                    "description": "The new target TSS value"
                },
                "reason": {
                    "type": "string",
                    "description": "Clear explanation for why this adjustment is being made based on athlete feedback"
                }
            },
            "required": ["workout_id", "new_tss", "reason"]
        }
    },
    {
        "name": "reschedule_workout",
        "description": "Move a workout to a different date due to scheduling conflicts, fatigue, or strategic planning",
        "parameters": {
            "type": "object",
            "properties": {
                "workout_id": {
                    "type": "integer",
                    "description": "The ID of the workout to reschedule"
                },
                "new_date": {
                    "type": "string",
                    "description": "The new date in YYYY-MM-DD format"
                },
                "reason": {
                    "type": "string",
                    "description": "Explanation for the reschedule"
                }
            },
            "required": ["workout_id", "new_date", "reason"]
        }
    },
    {
        "name": "swap_workout_type",
        "description": "Replace a workout with a different type (e.g., swap intervals for endurance due to fatigue)",
        "parameters": {
            "type": "object",
            "properties": {
                "workout_id": {
                    "type": "integer",
                    "description": "The ID of the workout to modify"
                },
                "new_workout_name": {
                    "type": "string",
                    "description": "Name of the new workout"
                },
                "new_description": {
                    "type": "string",
                    "description": "Description of the new workout structure"
                },
                "reason": {
                    "type": "string",
                    "description": "Why this swap is beneficial"
                }
            },
            "required": ["workout_id", "new_workout_name", "new_description", "reason"]
        }
    },
    {
        "name": "add_rest_day",
        "description": "Add a rest day when athlete shows signs of fatigue or overtraining",
        "parameters": {
            "type": "object",
            "properties": {
                "plan_id": {
                    "type": "integer",
                    "description": "The ID of the training plan"
                },
                "date": {
                    "type": "string",
                    "description": "Date for the rest day in YYYY-MM-DD format"
                },
                "reason": {
                    "type": "string",
                    "description": "Why rest is needed based on athlete feedback"
                }
            },
            "required": ["plan_id", "date", "reason"]
        }
    },
    {
        "name": "adjust_weekly_volume",
        "description": "Increase or decrease the total training load for a week",
        "parameters": {
            "type": "object",
            "properties": {
                "plan_id": {
                    "type": "integer",
                    "description": "The ID of the training plan"
                },
                "week_number": {
                    "type": "integer",
                    "description": "Which week to adjust"
                },
                "tss_change_percent": {
                    "type": "integer",
                    "description": "Percentage change in TSS (e.g., -10 for 10% reduction, +15 for 15% increase)"
                },
                "reason": {
                    "type": "string",
                    "description": "Rationale for the volume adjustment"
                }
            },
            "required": ["plan_id", "week_number", "tss_change_percent", "reason"]
        }
    }
]

# Map function names to actual functions
FUNCTION_MAP = {
    "adjust_workout_intensity": adjust_workout_intensity,
    "reschedule_workout": lambda workout_id, new_date, reason: reschedule_workout(
        workout_id, 
        datetime.strptime(new_date, '%Y-%m-%d').date(), 
        reason
    ),
    "swap_workout_type": swap_workout_type,
    "add_rest_day": lambda plan_id, date, reason: add_rest_day(
        plan_id,
        datetime.strptime(date, '%Y-%m-%d').date(),
        reason
    ),
    "adjust_weekly_volume": adjust_weekly_volume
}


def chat_with_adaptive_coach(user, message, context, active_plan=None):
    """
    Chat with Coach Manee with ability to modify training plans
    
    Args:
        user: User object
        message: User's message
        context: Training context (profile, rides, plan info)
        active_plan: Active TrainingPlan object (if exists)
    
    Returns:
        tuple: (response_text, adjustments_made)
    """
    
    # Build system prompt with coaching personality and capabilities
    system_prompt = f"""You are Coach Manee, a legendary cycling coach with 30+ years of experience coaching World Champions, Olympians, and national champions.

{context}

You have the ability to modify the athlete's training plan based on their feedback. When an athlete mentions:
- Fatigue, tiredness, or feeling run down → Consider reducing intensity or adding rest
- Feeling great, strong, or ready for more → Consider increasing intensity
- Schedule conflicts or life events → Reschedule workouts
- Specific workout concerns → Swap workout types

IMPORTANT COACHING PRINCIPLES:
1. Listen carefully to the athlete's feedback about how they're feeling
2. Make adjustments that support their long-term goals, not just short-term comfort
3. Explain your reasoning when making changes
4. Be conservative with increases, aggressive with recovery when needed
5. Track patterns - if you've made multiple fatigue-related adjustments, address the bigger picture

When you make a plan adjustment, explain:
- What you're changing
- Why you're making this change
- How it supports their goals
- What they should monitor going forward

Be conversational, supportive, and demonstrate deep coaching expertise."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ]
    
    adjustments_made = []
    
    try:
        # First API call with function calling enabled
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            functions=COACH_FUNCTIONS if active_plan else None,
            function_call="auto" if active_plan else "none",
            temperature=0.7,
            max_tokens=1000
        )
        
        response_message = response.choices[0].message
        
        # Check if the model wants to call a function
        if response_message.function_call:
            function_name = response_message.function_call.name
            function_args = json.loads(response_message.function_call.arguments)
            
            print(f"Coach Manee calling function: {function_name} with args: {function_args}")
            
            # Execute the function
            function_to_call = FUNCTION_MAP.get(function_name)
            if function_to_call:
                function_response = function_to_call(**function_args)
                adjustments_made.append({
                    'function': function_name,
                    'args': function_args,
                    'result': function_response
                })
                
                # Add function response to messages
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": function_name,
                        "arguments": response_message.function_call.arguments
                    }
                })
                messages.append({
                    "role": "function",
                    "name": function_name,
                    "content": json.dumps(function_response)
                })
                
                # Get final response from the model
                second_response = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                final_response = second_response.choices[0].message.content
            else:
                final_response = "I wanted to make an adjustment but encountered a technical issue. Let me know how you're feeling and we can discuss your training."
        else:
            # No function call, just return the response
            final_response = response_message.content
        
        return final_response, adjustments_made
        
    except Exception as e:
        print(f"Adaptive coach error: {e}")
        return "I'm having trouble connecting right now. Please try again in a moment.", []


def get_adjustment_summary(plan_id):
    """
    Get a summary of recent plan adjustments for context
    
    Args:
        plan_id: ID of the training plan
    
    Returns:
        str: Formatted summary of adjustments
    """
    adjustments = get_plan_adjustments(plan_id, limit=5)
    
    if not adjustments:
        return "No recent adjustments to this plan."
    
    summary = "Recent Plan Adjustments:\n"
    for adj in adjustments:
        summary += f"- {adj['when']}: {adj['type']} - {adj['change']} ({adj['reason']})\n"
    
    return summary
