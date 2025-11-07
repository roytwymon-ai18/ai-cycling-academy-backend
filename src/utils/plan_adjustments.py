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
            user_id=workout.user_id,
            adjustment_type='intensity_change',
            trigger_reason=reason,
            trigger_data={'workout_id': workout_id, 'rpe_feedback': True},
            changes_made={
                'workout_name': workout.name,
                'old_tss': old_tss,
                'new_tss': new_tss,
                'change_percent': round(((new_tss / old_tss) - 1) * 100, 1)
            },
            affected_workouts=[workout_id],
            estimated_impact=f"Reduced training load by {old_tss - new_tss} TSS to allow recovery"
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
            user_id=workout.user_id,
            adjustment_type='reschedule',
            trigger_reason=reason,
            trigger_data={'workout_id': workout_id, 'schedule_conflict': True},
            changes_made={
                'workout_name': workout.name,
                'old_date': old_date.strftime('%Y-%m-%d'),
                'new_date': new_date.strftime('%Y-%m-%d'),
                'days_moved': (new_date - old_date).days
            },
            affected_workouts=[workout_id],
            estimated_impact=f"Workout moved {(new_date - old_date).days} days to accommodate schedule"
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
            user_id=workout.user_id,
            adjustment_type='workout_swap',
            trigger_reason=reason,
            trigger_data={'workout_id': workout_id, 'fatigue_driven': True},
            changes_made={
                'old_workout': old_name,
                'new_workout': new_workout_name,
                'new_description': new_description,
                'date': workout.scheduled_date.strftime('%Y-%m-%d')
            },
            affected_workouts=[workout_id],
            estimated_impact=f"Changed workout type to better match athlete readiness"
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
        
        # Get user_id from plan
        plan = TrainingPlan.query.get(plan_id)
        
        # Record the adjustment
        adjustment = PlanAdjustment(
            plan_id=plan_id,
            user_id=plan.user_id,
            adjustment_type='rest_day_added',
            trigger_reason=reason,
            trigger_data={'date': date.strftime('%Y-%m-%d'), 'overtraining_prevention': True},
            changes_made={
                'replaced_workout': old_workout,
                'new_status': 'Rest Day',
                'date': date.strftime('%Y-%m-%d')
            },
            affected_workouts=[existing_workout.id] if existing_workout else [],
            estimated_impact="Added recovery day to prevent overtraining"
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
        
        # Get user_id from plan
        plan = TrainingPlan.query.get(plan_id)
        
        # Record the adjustment
        adjustment = PlanAdjustment(
            plan_id=plan_id,
            user_id=plan.user_id,
            adjustment_type='weekly_volume_change',
            trigger_reason=reason,
            trigger_data={
                'week_number': week_number,
                'change_percent': tss_change_percent,
                'workouts_affected': adjusted_count
            },
            changes_made={
                'week': week_number,
                'volume_change': f'{tss_change_percent:+d}%',
                'workouts_adjusted': adjusted_count
            },
            affected_workouts=[w.id for w in workouts],
            estimated_impact=f"Weekly training load adjusted by {tss_change_percent:+d}% for recovery/progression"
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
        ).order_by(PlanAdjustment.adjustment_date.desc()).limit(limit).all()
        
        return [{
            'type': adj.adjustment_type,
            'changes': adj.changes_made,
            'reason': adj.trigger_reason,
            'impact': adj.estimated_impact,
            'when': adj.adjustment_date.strftime('%Y-%m-%d %H:%M'),
            'affected_workouts': adj.affected_workouts
        } for adj in adjustments]
    except Exception as e:
        print(f"Error getting adjustments: {e}")
        return []
