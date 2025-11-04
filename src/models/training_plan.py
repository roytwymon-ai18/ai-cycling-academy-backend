from datetime import datetime
from src.models.user import db

class TrainingPlan(db.Model):
    __tablename__ = 'training_plans'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Plan Configuration
    name = db.Column(db.String(200))
    goal = db.Column(db.Text)
    goal_type = db.Column(db.String(50))  # 'ftp_increase', 'century_ride', 'race_prep', 'general_fitness'
    
    # Timeline
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    target_event_date = db.Column(db.DateTime)
    
    # Initial Fitness
    baseline_ftp = db.Column(db.Integer)
    baseline_weight = db.Column(db.Float)
    
    # Target Fitness
    target_ftp = db.Column(db.Integer)
    target_weight = db.Column(db.Float)
    
    # Plan Structure
    total_weeks = db.Column(db.Integer)
    base_weeks = db.Column(db.Integer)
    build_weeks = db.Column(db.Integer)
    specialty_weeks = db.Column(db.Integer)
    
    # Training Volume
    weekly_hours_available = db.Column(db.Float)
    rides_per_week = db.Column(db.Integer)
    training_days = db.Column(db.JSON)  # [1, 3, 4, 6] = Tue, Thu, Fri, Sun
    
    # Status
    status = db.Column(db.String(20), default='active')
    current_week = db.Column(db.Integer, default=1)
    current_phase = db.Column(db.String(20))
    
    # Adaptation Tracking
    last_ftp_test = db.Column(db.DateTime)
    next_ftp_test = db.Column(db.DateTime)
    adaptation_score = db.Column(db.Float, default=0.0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workouts = db.relationship('PlannedWorkout', backref='plan', lazy=True, cascade='all, delete-orphan')
    adjustments = db.relationship('PlanAdjustment', backref='plan', lazy=True)


class PlannedWorkout(db.Model):
    __tablename__ = 'planned_workouts'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('training_plans.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Scheduling
    scheduled_date = db.Column(db.Date, nullable=False)
    week_number = db.Column(db.Integer)
    phase = db.Column(db.String(20))
    
    # Workout Details
    workout_template_id = db.Column(db.Integer, db.ForeignKey('workout_templates.id'))
    name = db.Column(db.String(200))
    description = db.Column(db.Text)
    
    # Intensity
    primary_zone = db.Column(db.String(20))
    secondary_zone = db.Column(db.String(20))
    
    # Duration
    planned_duration = db.Column(db.Integer)  # seconds
    planned_tss = db.Column(db.Float)
    
    # Workout Structure
    intervals = db.Column(db.JSON)
    
    # Progression
    progression_level = db.Column(db.Float)
    difficulty_score = db.Column(db.Float)
    
    # Completion Status
    status = db.Column(db.String(20), default='scheduled')
    completed_ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'))
    
    # Performance Tracking
    actual_duration = db.Column(db.Integer)
    actual_tss = db.Column(db.Float)
    completion_percentage = db.Column(db.Float)
    success_rating = db.Column(db.String(20))
    
    # Rider Feedback
    pre_workout_readiness = db.Column(db.Integer)
    post_workout_rpe = db.Column(db.Integer)
    post_workout_notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)


class WorkoutTemplate(db.Model):
    __tablename__ = 'workout_templates'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Template Info
    name = db.Column(db.String(200), nullable=False)
    short_name = db.Column(db.String(100))
    description = db.Column(db.Text)
    
    # Classification
    primary_zone = db.Column(db.String(20))
    secondary_zone = db.Column(db.String(20))
    workout_type = db.Column(db.String(50))
    
    # Difficulty
    min_progression_level = db.Column(db.Float)
    max_progression_level = db.Column(db.Float)
    difficulty_score = db.Column(db.Float)
    
    # Duration
    duration = db.Column(db.Integer)
    work_duration = db.Column(db.Integer)
    
    # TSS
    estimated_tss = db.Column(db.Float)
    intensity_factor = db.Column(db.Float)
    
    # Workout Structure
    intervals = db.Column(db.JSON, nullable=False)
    
    # Phase Suitability
    suitable_for_base = db.Column(db.Boolean, default=False)
    suitable_for_build = db.Column(db.Boolean, default=False)
    suitable_for_specialty = db.Column(db.Boolean, default=False)
    
    # Tags
    tags = db.Column(db.JSON)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ProgressionLevel(db.Model):
    __tablename__ = 'progression_levels'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Zone Levels (1.0 - 10.0)
    recovery_level = db.Column(db.Float, default=3.0)
    endurance_level = db.Column(db.Float, default=3.0)
    tempo_level = db.Column(db.Float, default=3.0)
    sweet_spot_level = db.Column(db.Float, default=3.0)
    threshold_level = db.Column(db.Float, default=3.0)
    vo2max_level = db.Column(db.Float, default=3.0)
    anaerobic_level = db.Column(db.Float, default=3.0)
    
    # Last Updated
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # History
    history = db.Column(db.JSON)


class PlanAdjustment(db.Model):
    __tablename__ = 'plan_adjustments'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('training_plans.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Adjustment Details
    adjustment_date = db.Column(db.DateTime, default=datetime.utcnow)
    adjustment_type = db.Column(db.String(50))
    
    # Trigger
    trigger_reason = db.Column(db.Text)
    trigger_data = db.Column(db.JSON)
    
    # Changes Made
    changes_made = db.Column(db.JSON)
    
    # Impact
    affected_workouts = db.Column(db.JSON)
    estimated_impact = db.Column(db.Text)


class FTPTest(db.Model):
    __tablename__ = 'ftp_tests'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('training_plans.id'))
    
    # Test Details
    test_date = db.Column(db.DateTime, nullable=False)
    test_type = db.Column(db.String(20))
    
    # Results
    measured_power = db.Column(db.Integer)
    calculated_ftp = db.Column(db.Integer)
    previous_ftp = db.Column(db.Integer)
    ftp_change = db.Column(db.Integer)
    ftp_change_percent = db.Column(db.Float)
    
    # Test Data
    test_data = db.Column(db.JSON)
    
    # Context
    weeks_since_last_test = db.Column(db.Integer)
    training_phase = db.Column(db.String(20))
    
    # Notes
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class RiderFeedback(db.Model):
    __tablename__ = 'rider_feedback'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Daily Check-In
    feedback_date = db.Column(db.Date, nullable=False)
    
    # Readiness Metrics (1-5 scale)
    overall_feeling = db.Column(db.Integer)
    sleep_quality = db.Column(db.Integer)
    muscle_soreness = db.Column(db.Integer)
    motivation = db.Column(db.Integer)
    
    # Stress Level
    stress_level = db.Column(db.String(20))
    
    # Health Status
    illness = db.Column(db.Boolean, default=False)
    illness_description = db.Column(db.Text)
    injury = db.Column(db.Boolean, default=False)
    injury_description = db.Column(db.Text)
    
    # Life Factors
    work_stress = db.Column(db.String(20))
    travel = db.Column(db.Boolean, default=False)
    time_available = db.Column(db.String(20))
    
    # Free Text
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

