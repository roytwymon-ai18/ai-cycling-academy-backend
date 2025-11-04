from datetime import datetime
from src.models.user import db

class StravaToken(db.Model):
    __tablename__ = 'strava_tokens'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # OAuth tokens
    access_token = db.Column(db.String(255), nullable=False)
    refresh_token = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.Integer, nullable=False)  # Unix timestamp
    
    # Strava athlete info
    athlete_id = db.Column(db.BigInteger, nullable=False)
    athlete_username = db.Column(db.String(100))
    athlete_firstname = db.Column(db.String(100))
    athlete_lastname = db.Column(db.String(100))
    
    # Sync metadata
    last_sync = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('strava_token', uselist=False))
    
    def __repr__(self):
        return f'<StravaToken user_id={self.user_id} athlete_id={self.athlete_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'athlete_id': self.athlete_id,
            'athlete_username': self.athlete_username,
            'athlete_firstname': self.athlete_firstname,
            'athlete_lastname': self.athlete_lastname,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def is_expired(self):
        """Check if the access token is expired"""
        import time
        return time.time() >= self.expires_at

