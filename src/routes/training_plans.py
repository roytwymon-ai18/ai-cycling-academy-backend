"""
Training Plan API Routes for AI Cycling Academy
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import User
from models.training_plan import (
    TrainingPlan, PlannedWorkout, WorkoutTemplate, 
    ProgressionLevel, PlanAdjustment, FTPTest, RiderFeedback
)
from utils.plan_generator import PlanGenerator
from src.utils.workout_library import WORKOUT_TEMPLATES as WORKOUT_LIBRARY
from utils.workout_file_io import WorkoutFileParser, WorkoutFileExporter, import_workout_file, export_workout_file
from src.models.user import db

training_plans_bp = Blueprint('training_plans', __name__)


# ===== TRAINING PLAN ROUTES =====

@training_plans_bp.route('/current', methods=['GET'])
def get_current_plan():
    """Get user's current active training plan"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    plan = TrainingPlan.query.filter_by(
        user_id=session['user_id'],
        is_active=True
    ).order_by(TrainingPlan.created_at.desc()).first()
    
    if not plan:
        return jsonify({'plan': None}), 200
    
    return jsonify({
        'plan': {
            'id': plan.id,
            'goal_type': plan.goal_type,
            'duration_weeks': plan.duration_weeks,
            'start_date': plan.start_date.isoformat(),
            'end_date': plan.end_date.isoformat(),
            'weekly_hours': plan.weekly_hours,
            'rides_per_week': plan.rides_per_week,
            'current_ftp': plan.current_ftp,
            'target_ftp': plan.target_ftp,
            'base_weeks': plan.base_weeks,
            'build_weeks': plan.build_weeks,
            'specialty_weeks': plan.specialty_weeks,
            'is_active': plan.is_active,
            'completion_percentage': plan.completion_percentage,
            'created_at': plan.created_at.isoformat()
        }
    })


@training_plans_bp.route('/create', methods=['POST'])
def create_training_plan():
    """Generate a new personalized training plan"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.json
    
    # Validate required fields
    required_fields = ['goal_type', 'duration_weeks', 'rides_per_week', 'hours_per_week']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        # Generate training plan
        generator = PlanGenerator(user)
        plan = generator.generate_plan(
            goal_type=data['goal_type'],
            duration_weeks=int(data['duration_weeks']),
            rides_per_week=int(data['rides_per_week']),
            hours_per_week=float(data['hours_per_week']),
            training_days=data.get('training_days', [1, 3, 5, 0]),  # Mon, Wed, Fri, Sun
            target_ftp=data.get('target_ftp'),
            target_event_date=data.get('target_event_date')
        )
        
        return jsonify({
            'success': True,
            'plan': {
                'id': plan.id,
                'goal_type': plan.goal_type,
                'duration_weeks': plan.duration_weeks,
                'start_date': plan.start_date.isoformat(),
                'end_date': plan.end_date.isoformat(),
                'weekly_hours': plan.weekly_hours,
                'rides_per_week': plan.rides_per_week,
                'current_ftp': plan.current_ftp,
                'target_ftp': plan.target_ftp,
                'base_weeks': plan.base_weeks,
                'build_weeks': plan.build_weeks,
                'specialty_weeks': plan.specialty_weeks
            }
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@training_plans_bp.route('/<int:plan_id>', methods=['GET'])
def get_training_plan(plan_id):
    """Get training plan details"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    plan = TrainingPlan.query.get(plan_id)
    if not plan or plan.user_id != session['user_id']:
        return jsonify({'error': 'Plan not found'}), 404
    
    return jsonify({
        'id': plan.id,
        'goal_type': plan.goal_type,
        'duration_weeks': plan.duration_weeks,
        'start_date': plan.start_date.isoformat(),
        'end_date': plan.end_date.isoformat(),
        'weekly_hours': plan.weekly_hours,
        'rides_per_week': plan.rides_per_week,
        'current_ftp': plan.current_ftp,
        'target_ftp': plan.target_ftp,
        'base_weeks': plan.base_weeks,
        'build_weeks': plan.build_weeks,
        'specialty_weeks': plan.specialty_weeks,
        'is_active': plan.is_active,
        'completion_percentage': plan.completion_percentage,
        'created_at': plan.created_at.isoformat()
    })


@training_plans_bp.route('/<int:plan_id>/workouts', methods=['GET'])
def get_plan_workouts(plan_id):
    """Get all workouts for a training plan"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    plan = TrainingPlan.query.get(plan_id)
    if not plan or plan.user_id != session['user_id']:
        return jsonify({'error': 'Plan not found'}), 404
    
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    week_number = request.args.get('week')
    
    # Build query
    query = PlannedWorkout.query.filter_by(training_plan_id=plan_id)
    
    if start_date:
        query = query.filter(PlannedWorkout.scheduled_date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(PlannedWorkout.scheduled_date <= datetime.fromisoformat(end_date))
    if week_number:
        query = query.filter_by(week_number=int(week_number))
    
    workouts = query.order_by(PlannedWorkout.scheduled_date).all()
    
    return jsonify({
        'workouts': [{
            'id': w.id,
            'scheduled_date': w.scheduled_date.isoformat(),
            'week_number': w.week_number,
            'phase': w.phase,
            'workout_name': w.workout_name,
            'workout_type': w.workout_type,
            'primary_zone': w.primary_zone,
            'planned_duration': w.planned_duration,
            'planned_tss': w.planned_tss,
            'is_completed': w.is_completed,
            'is_skipped': w.is_skipped,
            'actual_duration': w.actual_duration,
            'actual_tss': w.actual_tss,
            'completion_date': w.completion_date.isoformat() if w.completion_date else None
        } for w in workouts]
    })


@training_plans_bp.route('/<int:plan_id>/adjust', methods=['PUT'])
def adjust_training_plan(plan_id):
    """Adjust training plan based on performance or feedback"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    plan = TrainingPlan.query.get(plan_id)
    if not plan or plan.user_id != session['user_id']:
        return jsonify({'error': 'Plan not found'}), 404
    
    data = request.json
    adjustment_type = data.get('adjustment_type')  # 'volume', 'intensity', 'recovery', 'extend'
    reason = data.get('reason', '')
    
    try:
        # Create adjustment record
        adjustment = PlanAdjustment(
            training_plan_id=plan_id,
            adjustment_type=adjustment_type,
            reason=reason,
            changes_made=data.get('changes', {}),
            affected_workouts=data.get('affected_workouts', [])
        )
        db.session.add(adjustment)
        
        # Apply adjustments based on type
        if adjustment_type == 'volume':
            # Reduce or increase weekly TSS
            volume_change = data.get('volume_change_percent', 0)
            # TODO: Implement volume adjustment logic
            
        elif adjustment_type == 'intensity':
            # Adjust progression levels
            intensity_change = data.get('intensity_change', 0)
            # TODO: Implement intensity adjustment logic
            
        elif adjustment_type == 'recovery':
            # Add recovery week
            # TODO: Implement recovery week insertion
            pass
            
        elif adjustment_type == 'extend':
            # Extend plan duration
            additional_weeks = data.get('additional_weeks', 1)
            plan.end_date += timedelta(weeks=additional_weeks)
            plan.duration_weeks += additional_weeks
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'adjustment_id': adjustment.id,
            'message': 'Plan adjusted successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@training_plans_bp.route('/<int:plan_id>', methods=['DELETE'])
def delete_training_plan(plan_id):
    """Delete a training plan"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    plan = TrainingPlan.query.get(plan_id)
    if not plan or plan.user_id != session['user_id']:
        return jsonify({'error': 'Plan not found'}), 404
    
    try:
        # Delete all related workouts
        PlannedWorkout.query.filter_by(training_plan_id=plan_id).delete()
        
        # Delete all adjustments
        PlanAdjustment.query.filter_by(training_plan_id=plan_id).delete()
        
        # Delete the plan
        db.session.delete(plan)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Plan deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ===== WORKOUT LIBRARY ROUTES =====

@training_plans_bp.route('/workouts/library', methods=['GET'])
def get_workout_library():
    """Browse workout library with filters"""
    # Get filter parameters
    zone = request.args.get('zone')
    workout_type = request.args.get('type')
    min_duration = request.args.get('min_duration', type=int)
    max_duration = request.args.get('max_duration', type=int)
    phase = request.args.get('phase')
    difficulty_min = request.args.get('difficulty_min', type=float)
    difficulty_max = request.args.get('difficulty_max', type=float)
    
    # Filter workouts
    filtered_workouts = WORKOUT_LIBRARY.copy()
    
    if zone:
        filtered_workouts = [w for w in filtered_workouts if w.get('primary_zone') == zone]
    if workout_type:
        filtered_workouts = [w for w in filtered_workouts if w.get('workout_type') == workout_type]
    if min_duration:
        filtered_workouts = [w for w in filtered_workouts if w.get('duration', 0) >= min_duration]
    if max_duration:
        filtered_workouts = [w for w in filtered_workouts if w.get('duration', 0) <= max_duration]
    if difficulty_min:
        filtered_workouts = [w for w in filtered_workouts if w.get('difficulty_score', 0) >= difficulty_min]
    if difficulty_max:
        filtered_workouts = [w for w in filtered_workouts if w.get('difficulty_score', 0) <= difficulty_max]
    if phase:
        phase_field = f'suitable_for_{phase}'
        filtered_workouts = [w for w in filtered_workouts if w.get(phase_field, False)]
    
    return jsonify({
        'workouts': [{
            'name': w['name'],
            'short_name': w['short_name'],
            'description': w['description'],
            'primary_zone': w['primary_zone'],
            'workout_type': w['workout_type'],
            'duration': w['duration'],
            'estimated_tss': w['estimated_tss'],
            'difficulty_score': w['difficulty_score'],
            'tags': w.get('tags', [])
        } for w in filtered_workouts],
        'total': len(filtered_workouts)
    })


@training_plans_bp.route('/workouts/<workout_name>', methods=['GET'])
def get_workout_details(workout_name):
    """Get detailed workout information"""
    workout = next((w for w in WORKOUT_LIBRARY if w['short_name'] == workout_name), None)
    
    if not workout:
        return jsonify({'error': 'Workout not found'}), 404
    
    return jsonify(workout)


@training_plans_bp.route('/workouts/import', methods=['POST'])
def import_workout():
    """Import workout from file (.mrc, .erg, .zwo)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    file_type = request.form.get('file_type')  # mrc, erg, zwo
    
    if not file_type:
        # Detect from extension
        filename = file.filename.lower()
        if filename.endswith('.mrc'):
            file_type = 'mrc'
        elif filename.endswith('.erg'):
            file_type = 'erg'
        elif filename.endswith('.zwo'):
            file_type = 'zwo'
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
    
    try:
        # Read file content
        content = file.read().decode('utf-8')
        
        # Parse workout
        parser = WorkoutFileParser()
        user = User.query.get(session['user_id'])
        
        if file_type == 'mrc':
            workout = parser.parse_mrc(content, user.current_ftp)
        elif file_type == 'erg':
            workout = parser.parse_erg(content, user.current_ftp)
        elif file_type == 'zwo':
            workout = parser.parse_zwo(content)
        else:
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save to workout templates (optional)
        # For now, just return the parsed workout
        
        return jsonify({
            'success': True,
            'workout': workout
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@training_plans_bp.route('/workouts/<workout_name>/export/<format>', methods=['GET'])
def export_workout(workout_name, format):
    """Export workout to file format"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Find workout
    workout = next((w for w in WORKOUT_LIBRARY if w['short_name'] == workout_name), None)
    if not workout:
        return jsonify({'error': 'Workout not found'}), 404
    
    # Get user FTP for ERG export
    user = User.query.get(session['user_id'])
    
    try:
        exporter = WorkoutFileExporter()
        
        if format == 'mrc':
            content = exporter.export_to_mrc(workout)
            mimetype = 'text/plain'
            filename = f"{workout['short_name'].replace(' ', '_')}.mrc"
        elif format == 'erg':
            content = exporter.export_to_erg(workout, user.current_ftp)
            mimetype = 'text/plain'
            filename = f"{workout['short_name'].replace(' ', '_')}.erg"
        elif format == 'zwo':
            content = exporter.export_to_zwo(workout)
            mimetype = 'application/xml'
            filename = f"{workout['short_name'].replace(' ', '_')}.zwo"
        elif format == 'json':
            content = exporter.export_to_json(workout)
            mimetype = 'application/json'
            filename = f"{workout['short_name'].replace(' ', '_')}.json"
        else:
            return jsonify({'error': 'Unsupported export format'}), 400
        
        from flask import Response
        return Response(
            content,
            mimetype=mimetype,
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===== PLANNED WORKOUT ROUTES =====

@training_plans_bp.route('/planned-workouts/<int:workout_id>', methods=['GET'])
def get_planned_workout(workout_id):
    """Get planned workout details"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    workout = PlannedWorkout.query.get(workout_id)
    if not workout:
        return jsonify({'error': 'Workout not found'}), 404
    
    # Verify ownership
    plan = TrainingPlan.query.get(workout.training_plan_id)
    if plan.user_id != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'id': workout.id,
        'scheduled_date': workout.scheduled_date.isoformat(),
        'week_number': workout.week_number,
        'phase': workout.phase,
        'workout_name': workout.workout_name,
        'workout_type': workout.workout_type,
        'primary_zone': workout.primary_zone,
        'planned_duration': workout.planned_duration,
        'planned_tss': workout.planned_tss,
        'intervals': workout.intervals,
        'is_completed': workout.is_completed,
        'is_skipped': workout.is_skipped,
        'actual_duration': workout.actual_duration,
        'actual_tss': workout.actual_tss,
        'actual_avg_power': workout.actual_avg_power,
        'completion_date': workout.completion_date.isoformat() if workout.completion_date else None,
        'rpe': workout.rpe,
        'notes': workout.notes
    })


@training_plans_bp.route('/planned-workouts/<int:workout_id>/complete', methods=['POST'])
def complete_planned_workout(workout_id):
    """Mark workout as completed with actual data"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    workout = PlannedWorkout.query.get(workout_id)
    if not workout:
        return jsonify({'error': 'Workout not found'}), 404
    
    # Verify ownership
    plan = TrainingPlan.query.get(workout.training_plan_id)
    if plan.user_id != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    
    try:
        workout.is_completed = True
        workout.completion_date = datetime.utcnow()
        workout.actual_duration = data.get('actual_duration', workout.planned_duration)
        workout.actual_tss = data.get('actual_tss', workout.planned_tss)
        workout.actual_avg_power = data.get('actual_avg_power')
        workout.rpe = data.get('rpe')
        workout.notes = data.get('notes', '')
        
        # Update plan completion percentage
        total_workouts = PlannedWorkout.query.filter_by(training_plan_id=plan.id).count()
        completed_workouts = PlannedWorkout.query.filter_by(
            training_plan_id=plan.id,
            is_completed=True
        ).count()
        plan.completion_percentage = (completed_workouts / total_workouts) * 100
        
        db.session.commit()
        
        # TODO: Update progression levels based on performance
        
        return jsonify({
            'success': True,
            'message': 'Workout marked as completed'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@training_plans_bp.route('/planned-workouts/<int:workout_id>/skip', methods=['POST'])
def skip_planned_workout(workout_id):
    """Skip a planned workout"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    workout = PlannedWorkout.query.get(workout_id)
    if not workout:
        return jsonify({'error': 'Workout not found'}), 404
    
    # Verify ownership
    plan = TrainingPlan.query.get(workout.training_plan_id)
    if plan.user_id != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    
    try:
        workout.is_skipped = True
        workout.notes = data.get('reason', 'Skipped')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Workout marked as skipped'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ===== FTP TEST ROUTES =====

@training_plans_bp.route('/ftp-tests/schedule', methods=['POST'])
def schedule_ftp_test():
    """Schedule an FTP test"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    
    try:
        test = FTPTest(
            user_id=session['user_id'],
            test_type=data.get('test_type', 'ramp'),
            scheduled_date=datetime.fromisoformat(data['scheduled_date']),
            context=data.get('context', '')
        )
        db.session.add(test)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'test_id': test.id,
            'scheduled_date': test.scheduled_date.isoformat()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@training_plans_bp.route('/ftp-tests/<int:test_id>/complete', methods=['POST'])
def complete_ftp_test(test_id):
    """Submit FTP test results"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    test = FTPTest.query.get(test_id)
    if not test or test.user_id != session['user_id']:
        return jsonify({'error': 'Test not found'}), 404
    
    data = request.json
    
    try:
        user = User.query.get(session['user_id'])
        old_ftp = user.current_ftp
        
        test.measured_power = data['measured_power']
        test.calculated_ftp = data['calculated_ftp']
        test.completed_date = datetime.utcnow()
        test.ftp_change = data['calculated_ftp'] - old_ftp
        test.notes = data.get('notes', '')
        
        # Update user's FTP
        user.current_ftp = data['calculated_ftp']
        
        db.session.commit()
        
        # TODO: Recalculate all future planned workouts with new FTP
        
        return jsonify({
            'success': True,
            'old_ftp': old_ftp,
            'new_ftp': data['calculated_ftp'],
            'change': data['calculated_ftp'] - old_ftp,
            'change_percent': ((data['calculated_ftp'] - old_ftp) / old_ftp) * 100
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@training_plans_bp.route('/ftp-tests/history', methods=['GET'])
def get_ftp_test_history():
    """Get FTP test history"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    tests = FTPTest.query.filter_by(
        user_id=session['user_id']
    ).filter(
        FTPTest.completed_date.isnot(None)
    ).order_by(FTPTest.completed_date.desc()).all()
    
    return jsonify({
        'tests': [{
            'id': t.id,
            'test_type': t.test_type,
            'scheduled_date': t.scheduled_date.isoformat(),
            'completed_date': t.completed_date.isoformat(),
            'measured_power': t.measured_power,
            'calculated_ftp': t.calculated_ftp,
            'ftp_change': t.ftp_change,
            'notes': t.notes
        } for t in tests]
    })


# ===== RIDER FEEDBACK ROUTES =====

@training_plans_bp.route('/rider-feedback/daily', methods=['POST'])
def submit_daily_feedback():
    """Submit daily readiness check-in"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    
    try:
        feedback = RiderFeedback(
            user_id=session['user_id'],
            date=datetime.utcnow().date(),
            overall_feeling=data.get('overall_feeling', 5),
            sleep_quality=data.get('sleep_quality', 5),
            soreness_level=data.get('soreness_level', 5),
            motivation_level=data.get('motivation_level', 5),
            stress_level=data.get('stress_level', 5),
            health_status=data.get('health_status', 'healthy'),
            work_load=data.get('work_load', 'normal'),
            travel_status=data.get('travel_status', False),
            time_available=data.get('time_available', 'normal'),
            notes=data.get('notes', '')
        )
        db.session.add(feedback)
        db.session.commit()
        
        # TODO: Use feedback to adjust today's workout recommendation
        
        return jsonify({
            'success': True,
            'feedback_id': feedback.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@training_plans_bp.route('/rider-feedback/recent', methods=['GET'])
def get_recent_feedback():
    """Get recent rider feedback"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    days = request.args.get('days', 7, type=int)
    start_date = datetime.utcnow().date() - timedelta(days=days)
    
    feedback = RiderFeedback.query.filter(
        and_(
            RiderFeedback.user_id == session['user_id'],
            RiderFeedback.date >= start_date
        )
    ).order_by(RiderFeedback.date.desc()).all()
    
    return jsonify({
        'feedback': [{
            'date': f.date.isoformat(),
            'overall_feeling': f.overall_feeling,
            'sleep_quality': f.sleep_quality,
            'soreness_level': f.soreness_level,
            'motivation_level': f.motivation_level,
            'stress_level': f.stress_level,
            'health_status': f.health_status,
            'notes': f.notes
        } for f in feedback]
    })


# ===== PROGRESSION LEVEL ROUTES =====

@training_plans_bp.route('/progression-levels', methods=['GET'])
def get_progression_levels():
    """Get current progression levels"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get most recent progression level for each zone
    levels = {}
    for zone in ['recovery', 'endurance', 'tempo', 'sweet_spot', 'threshold', 'vo2max', 'anaerobic']:
        latest = ProgressionLevel.query.filter_by(
            user_id=session['user_id'],
            zone=zone
        ).order_by(ProgressionLevel.updated_at.desc()).first()
        
        if latest:
            levels[zone] = {
                'level': latest.level,
                'updated_at': latest.updated_at.isoformat()
            }
        else:
            levels[zone] = {
                'level': 3.0,  # Default starting level
                'updated_at': None
            }
    
    return jsonify({'levels': levels})


@training_plans_bp.route('/progression-levels/history', methods=['GET'])
def get_progression_level_history():
    """Get progression level history"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    zone = request.args.get('zone')
    days = request.args.get('days', 90, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = ProgressionLevel.query.filter(
        and_(
            ProgressionLevel.user_id == session['user_id'],
            ProgressionLevel.updated_at >= start_date
        )
    )
    
    if zone:
        query = query.filter_by(zone=zone)
    
    history = query.order_by(ProgressionLevel.updated_at).all()
    
    return jsonify({
        'history': [{
            'zone': h.zone,
            'level': h.level,
            'updated_at': h.updated_at.isoformat(),
            'reason': h.reason
        } for h in history]
    })

