from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Ride(db.Model):
    __tablename__ = 'rides'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Basic ride info
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    name = db.Column(db.String(200), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # seconds
    distance = db.Column(db.Float, nullable=False)  # kilometers
    
    # Power metrics
    avg_power = db.Column(db.Integer)  # watts
    max_power = db.Column(db.Integer)  # watts
    normalized_power = db.Column(db.Integer)  # watts
    ftp = db.Column(db.Integer)  # watts
    intensity_factor = db.Column(db.Float)
    training_stress_score = db.Column(db.Float)
    
    # Heart rate metrics
    avg_heart_rate = db.Column(db.Integer)  # bpm
    max_heart_rate = db.Column(db.Integer)  # bpm
    
    # Speed and cadence
    avg_speed = db.Column(db.Float)  # km/h
    max_speed = db.Column(db.Float)  # km/h
    avg_cadence = db.Column(db.Integer)  # rpm
    
    # Elevation
    elevation_gain = db.Column(db.Integer)  # meters
    
    # Power zones (time in seconds)
    time_in_zone_1 = db.Column(db.Integer, default=0)
    time_in_zone_2 = db.Column(db.Integer, default=0)
    time_in_zone_3 = db.Column(db.Integer, default=0)
    time_in_zone_4 = db.Column(db.Integer, default=0)
    time_in_zone_5 = db.Column(db.Integer, default=0)
    time_in_zone_6 = db.Column(db.Integer, default=0)
    time_in_zone_7 = db.Column(db.Integer, default=0)
    
    # AI analysis
    ai_analysis = db.Column(db.Text)  # JSON string of AI insights
    ai_recommendations = db.Column(db.Text)  # AI coaching recommendations
    analyzed_at = db.Column(db.DateTime)
    
    # File data
    file_path = db.Column(db.String(500))  # path to original file
    
    def __repr__(self):
        return f'<Ride {self.name} - {self.date}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat() if self.date else None,
            'name': self.name,
            'duration': self.duration,
            'distance': self.distance,
            'avg_power': self.avg_power,
            'max_power': self.max_power,
            'normalized_power': self.normalized_power,
            'ftp': self.ftp,
            'intensity_factor': self.intensity_factor,
            'training_stress_score': self.training_stress_score,
            'avg_heart_rate': self.avg_heart_rate,
            'max_heart_rate': self.max_heart_rate,
            'avg_speed': self.avg_speed,
            'max_speed': self.max_speed,
            'avg_cadence': self.avg_cadence,
            'elevation_gain': self.elevation_gain,
            'time_in_zone_1': self.time_in_zone_1,
            'time_in_zone_2': self.time_in_zone_2,
            'time_in_zone_3': self.time_in_zone_3,
            'time_in_zone_4': self.time_in_zone_4,
            'time_in_zone_5': self.time_in_zone_5,
            'time_in_zone_6': self.time_in_zone_6,
            'time_in_zone_7': self.time_in_zone_7,
            'ai_analysis': self.ai_analysis,
            'ai_recommendations': self.ai_recommendations,
            'analyzed_at': self.analyzed_at.isoformat() if self.analyzed_at else None
        }

