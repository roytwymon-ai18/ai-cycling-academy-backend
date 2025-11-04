from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    
    # Cycling profile
    current_ftp = db.Column(db.Integer)  # watts
    weight = db.Column(db.Float)  # kg
    max_heart_rate = db.Column(db.Integer)  # bpm
    resting_heart_rate = db.Column(db.Integer)  # bpm
    training_goals = db.Column(db.Text)  # User's training goals and objectives
    
    # Connected services
    strava_connected = db.Column(db.Boolean, default=False)
    strava_athlete_id = db.Column(db.String(50))
    google_connected = db.Column(db.Boolean, default=False)
    google_id = db.Column(db.String(100))
    
    # Training Plan Fields
    current_plan_id = db.Column(db.Integer)
    completed_plans = db.Column(db.Integer, default=0)
    total_training_weeks = db.Column(db.Integer, default=0)
    preferred_test_type = db.Column(db.String(20))  # 'ramp', '8_minute', '20_minute'
    training_experience = db.Column(db.String(20))  # 'beginner', 'intermediate', 'advanced'
    
    # Account info
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    subscription_tier = db.Column(db.String(20), default='free')  # free, basic, premium
    
    # Relationships
    rides = db.relationship('Ride', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'current_ftp': self.current_ftp,
            'weight': self.weight,
            'max_heart_rate': self.max_heart_rate,
            'resting_heart_rate': self.resting_heart_rate,
            'strava_connected': self.strava_connected,
            'google_connected': self.google_connected,
            'subscription_tier': self.subscription_tier,
            'training_goals': self.training_goals,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
