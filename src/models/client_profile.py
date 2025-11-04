from src.models.user import db
from datetime import datetime

class ClientProfile(db.Model):
    __tablename__ = 'client_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Onboarding status
    onboarding_completed = db.Column(db.Boolean, default=False)
    onboarding_step = db.Column(db.Integer, default=0)  # Track current interview question
    
    # Cycling Story & Background
    cycling_story = db.Column(db.Text)  # How they got into cycling
    rider_type = db.Column(db.String(100))  # road, gravel, MTB, indoor
    best_ride_description = db.Column(db.Text)
    proud_moments = db.Column(db.Text)
    
    # Current Situation
    weekly_ride_frequency = db.Column(db.String(100))
    typical_week_description = db.Column(db.Text)
    tech_equipment = db.Column(db.Text)  # Power meter, HR, GPS, apps
    
    # Goals & Motivation
    primary_goals = db.Column(db.Text)  # 3-12 month goals
    deep_motivation = db.Column(db.Text)  # The "why" behind goals
    success_vision = db.Column(db.Text)  # What success looks/feels like
    
    # Obstacles & Constraints
    current_challenges = db.Column(db.Text)
    training_availability = db.Column(db.String(100))  # Days per week
    injury_history = db.Column(db.Text)
    
    # Coaching Preferences
    coaching_style_preference = db.Column(db.String(100))  # tough love, collaborative, data-driven, motivational
    
    # Generated Profile Summary
    skill_fitness_assessment = db.Column(db.Text)
    action_items = db.Column(db.Text)  # First 3 action items
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('client_profile', uselist=False, lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'onboarding_completed': self.onboarding_completed,
            'onboarding_step': self.onboarding_step,
            'cycling_story': self.cycling_story,
            'rider_type': self.rider_type,
            'primary_goals': self.primary_goals,
            'deep_motivation': self.deep_motivation,
            'success_vision': self.success_vision,
            'current_challenges': self.current_challenges,
            'training_availability': self.training_availability,
            'coaching_style_preference': self.coaching_style_preference,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_profile_summary(self):
        """Generate a formatted profile summary for Coach Manee to use"""
        if not self.onboarding_completed:
            return None
            
        summary = f"""
CLIENT CYCLING PROFILE

🚴 Rider Type: {self.rider_type or 'Not specified'}

🎯 Primary Goals: {self.primary_goals or 'Not specified'}

💡 Deep Motivation: {self.deep_motivation or 'Not specified'}

🧩 Skill + Fitness: {self.skill_fitness_assessment or 'Assessment pending'}

🔧 Equipment + Data: {self.tech_equipment or 'Not specified'}

⏱ Training Availability: {self.training_availability or 'Not specified'}

⚠ Obstacles: {self.current_challenges or 'None identified'}

🧠 Coaching Style: {self.coaching_style_preference or 'Not specified'}

✅ Action Items: {self.action_items or 'To be determined'}
"""
        return summary.strip()

