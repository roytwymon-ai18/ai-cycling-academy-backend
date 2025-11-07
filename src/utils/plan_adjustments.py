"""
Training Plan Adjustment Functions for Coach Manee
Enables dynamic plan modifications based on user feedback
"""

from datetime import datetime, timedelta
from src.models.user import db
from src.models.training_plan import TrainingPlan, PlannedWorkout, PlanAdjustment

def adjust_workout_intensity(workout_id, new_tss, reason):
    """
    Adjust the TSS/intensity of a specific workout
    
    Args:
        workout_id: ID of the PlannedWorkout to adjust
        new_tss: New target TSS value
        reason: Explanation for the adjustment
    
    Returns:
        dict: Success status and details
    """
    try:
        workout = PlannedWorkout.query.get(workout_id)
        if not workout:
            return {'success': False, 'error': 'Workout not found'}
        
        old_tss = workout.target_tss
        workout.target_tss = new_tss
        
        # Record the adjustment
        adjustment = PlanAdjustment(
            plan_id=workout.plan_id,
            adjustment_type='intensity_change',
            target_date=workout.scheduled_date,
            old_value=str(old_tss),
            new_value=str(new_tss),
            reason=reason,
            created_at=datetime.utcnow()
        )
        
        db.session.add(adjustment)
        db.session.commit()
        
        return {
            'success': True,
            'workout': workout.name,
            'old_tss': old_tss,
            'new_tss': new_tss,
            'reason': reason
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}


def reschedule_workout(workout_id, new_date, reason):
    """
    Reschedule a workout to a different date
    
    Args:
        workout_id: ID of the PlannedWorkout to reschedule
        new_date: New scheduled date (datetime.date object)
        reason: Explanation for the reschedule
    
    Returns:
        dict: Success status and details
    """
    try:
        workout = PlannedWorkout.query.get(workout_id)
        if not workout:
            return {'success': False, 'error': 'Workout not found'}
        
        old_date = workout.scheduled_date
        workout.scheduled_date = new_date
        
        # Record the adjustment
        adjustment = PlanAdjustment(
            plan_id=workout.plan_id,
            adjustment_type='reschedule',
            target_date=old_date,
            old_value=old_date.strftime('%Y-%m-%d'),
            new_value=new_date.strftime('%Y-%m-%d'),
            reason=reason,
            created_at=datetime.utcnow()
        )
        
        db.session.add(adjustment)
        db.session.commit()
        
        return {
            'success': True,
            'workout': workout.name,
            'old_date': old_date.strftime('%Y-%m-%d'),
            'new_date': new_date.strftime('%Y-%m-%d'),
            'reason': reason
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}


def swap_workout_type(workout_id, new_workout_name, new_description, reason):
    """
    Change the type/content of a workout
    
    Args:
        workout_id: ID of the PlannedWorkout to modify
        new_workout_name: New workout name
        new_description: New workout description
        reason: Explanation for the swap
    
    Returns:
        dict: Success status and details
    """
    try:
        workout = PlannedWorkout.query.get(workout_id)
        if not workout:
            return {'success': False, 'error': 'Workout not found'}
        
        old_name = workout.name
        workout.name = new_workout_name
        workout.description = new_description
        
        # Record the adjustment
        adjustment = PlanAdjustment(
            plan_id=workout.plan_id,
            adjustment_type='workout_swap',
            target_date=workout.scheduled_date,
            old_value=old_name,
            new_value=new_workout_name,
            reason=reason,
            created_at=datetime.utcnow()
        )
        
        db.session.add(adjustment)
        db.session.commit()
        
        return {
            'success': True,
            'date': workout.scheduled_date.strftime('%Y-%m-%d'),
            'old_workout': old_name,
            'new_workout': new_workout_name,
            'reason': reason
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}


def add_rest_day(plan_id, date, reason):
    """
    Add a rest day to the plan
    
    Args:
        plan_id: ID of the TrainingPlan
        date: Date for the rest day
        reason: Explanation for adding rest
    
    Returns:
        dict: Success status and details
    """
    try:
        # Check if there's already a workout on this date
        existing_workout = PlannedWorkout.query.filter_by(
            plan_id=plan_id,
            scheduled_date=date
        ).first()
        
        if existing_workout:
            # Mark existing workout as skipped
            existing_workout.status = 'skipped'
            old_workout = existing_workout.name
        else:
            old_workout = 'No workout scheduled'
        
        # Record the adjustment
        adjustment = PlanAdjustment(
            plan_id=plan_id,
            adjustment_type='rest_day_added',
            target_date=date,
            old_value=old_workout,
            new_value='Rest Day',
            reason=reason,
            created_at=datetime.utcnow()
        )
        
        db.session.add(adjustment)
        db.session.commit()
        
        return {
            'success': True,
            'date': date.strftime('%Y-%m-%d'),
            'replaced_workout': old_workout,
            'reason': reason
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}


def adjust_weekly_volume(plan_id, week_number, tss_change_percent, reason):
    """
    Adjust the total TSS for a specific week
    
    Args:
        plan_id: ID of the TrainingPlan
        week_number: Week to adjust
        tss_change_percent: Percentage change (e.g., -10 for 10% reduction)
        reason: Explanation for the adjustment
    
    Returns:
        dict: Success status and details
    """
    try:
        workouts = PlannedWorkout.query.filter_by(
            plan_id=plan_id,
            week_number=week_number
        ).all()
        
        if not workouts:
            return {'success': False, 'error': 'No workouts found for this week'}
        
        multiplier = 1 + (tss_change_percent / 100)
        adjusted_count = 0
        
        for workout in workouts:
            if workout.target_tss:
                workout.target_tss = int(workout.target_tss * multiplier)
                adjusted_count += 1
        
        # Record the adjustment
        adjustment = PlanAdjustment(
            plan_id=plan_id,
            adjustment_type='weekly_volume_change',
            target_date=None,
            old_value=f'Week {week_number}',
            new_value=f'{tss_change_percent:+d}%',
            reason=reason,
            created_at=datetime.utcnow()
        )
        
        db.session.add(adjustment)
        db.session.commit()
        
        return {
            'success': True,
            'week': week_number,
            'workouts_adjusted': adjusted_count,
            'change_percent': tss_change_percent,
            'reason': reason
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}


def get_plan_adjustments(plan_id, limit=10):
    """
    Get recent adjustments made to a plan
    
    Args:
        plan_id: ID of the TrainingPlan
        limit: Maximum number of adjustments to return
    
    Returns:
        list: Recent adjustments
    """
    try:
        adjustments = PlanAdjustment.query.filter_by(
            plan_id=plan_id
        ).order_by(PlanAdjustment.created_at.desc()).limit(limit).all()
        
        return [{
            'type': adj.adjustment_type,
            'date': adj.target_date.strftime('%Y-%m-%d') if adj.target_date else 'N/A',
            'change': f'{adj.old_value} → {adj.new_value}',
            'reason': adj.reason,
            'when': adj.created_at.strftime('%Y-%m-%d %H:%M')
        } for adj in adjustments]
    except Exception as e:
        print(f"Error getting adjustments: {e}")
        return []
