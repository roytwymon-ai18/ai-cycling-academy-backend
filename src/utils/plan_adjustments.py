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


def override_with_unplanned_activity(workout_id, activity_description, estimated_tss, estimated_duration, reason):
    """
    Replace a scheduled workout with an unplanned activity (group ride, event, etc.)
    
    Args:
        workout_id: ID of the PlannedWorkout to override
        activity_description: Description of the unplanned activity
        estimated_tss: Estimated TSS of the activity
        estimated_duration: Estimated duration in minutes
        reason: Why the user is doing this activity
    
    Returns:
        dict: Success status and details
    """
    try:
        workout = PlannedWorkout.query.get(workout_id)
        if not workout:
            return {'success': False, 'error': 'Workout not found'}
        
        old_workout = workout.name
        old_tss = workout.target_tss
        
        # Update the workout to reflect the override
        workout.name = f"Override: {activity_description}"
        workout.description = f"User-initiated activity override. Original workout: {old_workout}"
        workout.target_tss = estimated_tss
        workout.planned_duration = estimated_duration * 60  # Convert to seconds
        workout.status = 'overridden'
        
        # Record the adjustment
        adjustment = PlanAdjustment(
            plan_id=workout.plan_id,
            user_id=workout.user_id,
            adjustment_type='user_override',
            trigger_reason=reason,
            trigger_data={
                'workout_id': workout_id,
                'activity_type': 'unplanned_activity',
                'user_initiated': True
            },
            changes_made={
                'original_workout': old_workout,
                'override_activity': activity_description,
                'original_tss': old_tss,
                'estimated_tss': estimated_tss,
                'tss_difference': estimated_tss - old_tss if old_tss else 0,
                'date': workout.scheduled_date.strftime('%Y-%m-%d')
            },
            affected_workouts=[workout_id],
            estimated_impact=f"Replaced structured workout with real-world activity. TSS change: {estimated_tss - old_tss if old_tss else 0:+.0f}"
        )
        
        db.session.add(adjustment)
        db.session.commit()
        
        return {
            'success': True,
            'date': workout.scheduled_date.strftime('%Y-%m-%d'),
            'original_workout': old_workout,
            'override_activity': activity_description,
            'tss_change': estimated_tss - old_tss if old_tss else 0,
            'reason': reason,
            'recommendation': 'Coach will adjust surrounding workouts to accommodate this change'
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}


def add_priority_event(plan_id, event_date, event_name, event_type, estimated_tss, notes):
    """
    Add a priority event (race, gran fondo, group ride) to the plan
    
    Args:
        plan_id: ID of the TrainingPlan
        event_date: Date of the event
        event_name: Name of the event
        event_type: Type (race, gran_fondo, group_ride, century, etc.)
        estimated_tss: Expected TSS of the event
        notes: Additional details
    
    Returns:
        dict: Success status and details
    """
    try:
        plan = TrainingPlan.query.get(plan_id)
        if not plan:
            return {'success': False, 'error': 'Training plan not found'}
        
        # Check if there's already a workout on this date
        existing_workout = PlannedWorkout.query.filter_by(
            plan_id=plan_id,
            scheduled_date=event_date
        ).first()
        
        if existing_workout:
            # Override the existing workout
            old_workout = existing_workout.name
            existing_workout.name = f"EVENT: {event_name}"
            existing_workout.description = f"{event_type.upper()} - {notes}"
            existing_workout.target_tss = estimated_tss
            existing_workout.status = 'priority_event'
            workout_id = existing_workout.id
        else:
            # Create new workout for the event
            new_workout = PlannedWorkout(
                plan_id=plan_id,
                user_id=plan.user_id,
                scheduled_date=event_date,
                name=f"EVENT: {event_name}",
                description=f"{event_type.upper()} - {notes}",
                target_tss=estimated_tss,
                status='priority_event'
            )
            db.session.add(new_workout)
            db.session.flush()
            workout_id = new_workout.id
            old_workout = 'None'
        
        # Record the adjustment
        adjustment = PlanAdjustment(
            plan_id=plan_id,
            user_id=plan.user_id,
            adjustment_type='priority_event_added',
            trigger_reason=f"User added priority event: {event_name}",
            trigger_data={
                'event_name': event_name,
                'event_type': event_type,
                'event_date': event_date.strftime('%Y-%m-%d'),
                'user_initiated': True
            },
            changes_made={
                'event_name': event_name,
                'event_type': event_type,
                'date': event_date.strftime('%Y-%m-%d'),
                'replaced_workout': old_workout,
                'estimated_tss': estimated_tss
            },
            affected_workouts=[workout_id],
            estimated_impact=f"Priority event added. Plan will be adjusted to taper before and recover after."
        )
        
        db.session.add(adjustment)
        db.session.commit()
        
        return {
            'success': True,
            'event_name': event_name,
            'event_date': event_date.strftime('%Y-%m-%d'),
            'replaced_workout': old_workout,
            'recommendation': 'Coach will adjust training to taper before event and plan recovery after'
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}


def rebalance_week_around_override(plan_id, week_number, override_tss_delta, reason):
    """
    Rebalance the rest of a week after a workout override
    
    Args:
        plan_id: ID of the TrainingPlan
        week_number: Week to rebalance
        override_tss_delta: TSS difference from the override (+/-)
        reason: Explanation for rebalancing
    
    Returns:
        dict: Success status and details
    """
    try:
        # Get all non-overridden workouts in the week
        workouts = PlannedWorkout.query.filter(
            PlannedWorkout.plan_id == plan_id,
            PlannedWorkout.week_number == week_number,
            PlannedWorkout.status.in_(['scheduled', 'pending'])
        ).all()
        
        if not workouts:
            return {'success': False, 'error': 'No workouts available to rebalance'}
        
        # Distribute the TSS adjustment across remaining workouts
        tss_per_workout = override_tss_delta / len(workouts)
        adjusted_count = 0
        
        for workout in workouts:
            if workout.target_tss:
                new_tss = max(30, workout.target_tss - tss_per_workout)  # Don't go below 30 TSS
                workout.target_tss = int(new_tss)
                adjusted_count += 1
        
        # Record the adjustment
        plan = TrainingPlan.query.get(plan_id)
        adjustment = PlanAdjustment(
            plan_id=plan_id,
            user_id=plan.user_id,
            adjustment_type='weekly_rebalance',
            trigger_reason=reason,
            trigger_data={
                'week_number': week_number,
                'override_tss_delta': override_tss_delta,
                'workouts_adjusted': adjusted_count
            },
            changes_made={
                'week': week_number,
                'tss_redistributed': override_tss_delta,
                'workouts_adjusted': adjusted_count,
                'adjustment_per_workout': round(tss_per_workout, 1)
            },
            affected_workouts=[w.id for w in workouts],
            estimated_impact=f"Rebalanced weekly load to accommodate user override"
        )
        
        db.session.add(adjustment)
        db.session.commit()
        
        return {
            'success': True,
            'week': week_number,
            'workouts_adjusted': adjusted_count,
            'tss_redistributed': override_tss_delta,
            'reason': reason
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}
