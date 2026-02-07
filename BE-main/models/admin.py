from datetime import datetime
import bcrypt
from .user import db

class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    number = db.Column(db.String(15), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
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
    
    def __init__(self, name, number, email, password):
        self.name = name
        self.number = number
        self.email = email
        self.set_password(password)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self):
        """Convert admin object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'number': self.number,
            'email': self.email,
            'phone_number': self.phone_number,
            'twofa_enabled': self.twofa_enabled,
            'sms_notifications': self.sms_notifications,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Admin {self.email}>'