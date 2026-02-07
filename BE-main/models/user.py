from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt
import enum

db = SQLAlchemy()

class RoleType(enum.Enum):
    STUDENT = "student"
    FACULTY = "faculty"

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum(RoleType), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # New fields for extended features
    phone_number = db.Column(db.String(20))  # For SMS notifications
    sms_notifications = db.Column(db.Boolean, default=False)  # SMS preference
    
    # 2FA fields
    twofa_enabled = db.Column(db.Boolean, default=False)
    twofa_method = db.Column(db.String(20))  # 'email' or 'totp'
    twofa_otp = db.Column(db.String(6))
    twofa_otp_expiry = db.Column(db.DateTime)
    totp_secret = db.Column(db.String(32))  # Base32 encoded secret for TOTP
    totp_verified = db.Column(db.Boolean, default=False)
    
    # Location data (JSON)
    location = db.Column(db.JSON)  # {'latitude': float, 'longitude': float, 'address': str}
    
    def __init__(self, name, email, password, role):
        self.name = name
        self.email = email
        self.set_password(password)
        self.role = RoleType(role)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role.value,
            'phone_number': self.phone_number,
            'twofa_enabled': self.twofa_enabled,
            'sms_notifications': self.sms_notifications,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<User {self.email}>'