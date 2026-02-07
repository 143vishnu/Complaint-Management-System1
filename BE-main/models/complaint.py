from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum
from .user import db

class ComplaintStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class ComplaintCategory(enum.Enum):
    TECHNICAL = "Technical"
    ACADEMIC = "Academic"
    HOSTEL_MESS = "Hostel/Mess"
    MAINTENANCE = "Maintenance"

class ComplaintPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Complaint(db.Model):
    __tablename__ = 'complaints'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum(ComplaintCategory), nullable=False)
    priority = db.Column(db.Enum(ComplaintPriority), nullable=False)
    status = db.Column(db.Enum(ComplaintStatus), default=ComplaintStatus.PENDING)
    
    # File attachments
    attachments = db.relationship('ComplaintAttachment', backref='complaint', lazy=True, cascade='all, delete-orphan')
    
    # Feedback relationship
    feedback = db.relationship('ComplaintFeedback', backref='complaint', uselist=False, lazy=True, cascade='all, delete-orphan')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # Admin response
    admin_response = db.Column(db.Text, nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    
    # New features
    is_anonymous = db.Column(db.Boolean, default=False)  # Anonymous complaints
    tags = db.Column(db.JSON, default=list)  # Complaint tags
    assigned_to_admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)  # Assigned admin
    
    # Admin notes and comments
    admin_notes = db.relationship('AdminNote', backref='complaint', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('ComplaintComment', backref='complaint', lazy=True, cascade='all, delete-orphan')
    
    # SLA tracking
    escalated = db.Column(db.Boolean, default=False)
    escalation_level = db.Column(db.Integer, default=0)  # 0=not escalated, 1=first escalation, 2=second, etc.
    last_escalation_at = db.Column(db.DateTime, nullable=True)
    sla_breach = db.Column(db.Boolean, default=False)
    
    # Video support (JSON array of video metadata)
    videos = db.Column(db.JSON, default=list)  # [{'url': str, 'public_id': str, 'duration': float, ...}]
    
    # Location data
    location = db.Column(db.JSON)  # {'latitude': float, 'longitude': float, 'address': str, ...}
    
    # Relationships
    user = db.relationship('User', backref='complaints')
    admin = db.relationship('Admin', foreign_keys=[admin_id], backref='handled_complaints')
    assigned_admin = db.relationship('Admin', foreign_keys=[assigned_to_admin_id], backref='assigned_complaints')
    
    def __init__(self, user_id, title, description, category, priority):
        self.user_id = user_id
        self.title = title
        self.description = description
        self.category = ComplaintCategory(category)
        self.priority = ComplaintPriority(priority)
        self.ticket_id = self.generate_ticket_id()
    
    def generate_ticket_id(self):
        """Generate unique ticket ID"""
        import random
        import string
        timestamp = datetime.now().strftime("%Y%m%d")
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"CMP{timestamp}{random_part}"
    
    def to_dict(self):
        """Convert complaint object to dictionary"""
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user and not self.is_anonymous else 'Anonymous User',
            'user_email': self.user.email if self.user and not self.is_anonymous else 'anonymous@system.local',
            'title': self.title,
            'description': self.description,
            'category': self.category.value,
            'priority': self.priority.value,
            'status': self.status.value,
            'attachments': [att.to_dict() for att in self.attachments],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'admin_response': self.admin_response,
            'admin_id': self.admin_id,
            'feedback': self.feedback.to_dict() if self.feedback else None,
            'is_anonymous': self.is_anonymous,
            'tags': self.tags,
            'assigned_to_admin_id': self.assigned_to_admin_id,
            'admin_notes': [note.to_dict() for note in self.admin_notes],
            'comments': [comment.to_dict() for comment in self.comments],
            'escalated': self.escalated,
            'escalation_level': self.escalation_level,
            'sla_breach': self.sla_breach,
            'videos': self.videos or [],
            'location': self.location
        }
    
    def __repr__(self):
        return f'<Complaint {self.ticket_id}>'

class ComplaintAttachment(db.Model):
    __tablename__ = 'complaint_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)  # Cloudinary URL
    file_type = db.Column(db.String(50), nullable=False)  # image, document, etc.
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    cloudinary_public_id = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert attachment object to dictionary"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_url': self.file_url,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.isoformat()
        }
    
    def __repr__(self):
        return f'<ComplaintAttachment {self.filename}>'

class ComplaintFeedback(db.Model):
    __tablename__ = 'complaint_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False, unique=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    feedback_text = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, complaint_id, rating, feedback_text=None):
        self.complaint_id = complaint_id
        self.rating = rating
        self.feedback_text = feedback_text
    
    def to_dict(self):
        """Convert feedback object to dictionary"""
        return {
            'id': self.id,
            'complaint_id': self.complaint_id,
            'rating': self.rating,
            'feedback_text': self.feedback_text,
            'submitted_at': self.submitted_at.isoformat()
        }
    
    def __repr__(self):
        return f'<ComplaintFeedback {self.complaint_id}>'


class AdminNote(db.Model):
    """Internal admin notes - not visible to users"""
    __tablename__ = 'admin_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    note_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    admin = db.relationship('Admin', backref='notes')
    
    def to_dict(self):
        return {
            'id': self.id,
            'complaint_id': self.complaint_id,
            'admin_id': self.admin_id,
            'admin_name': self.admin.name if self.admin else None,
            'note_text': self.note_text,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<AdminNote {self.id}>'


class ComplaintComment(db.Model):
    """Public comments/discussion thread - visible to users and admins"""
    __tablename__ = 'complaint_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    comment_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_admin_response = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User')
    admin = db.relationship('Admin', backref='public_comments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'complaint_id': self.complaint_id,
            'user_id': self.user_id,
            'admin_id': self.admin_id,
            'author_name': (self.admin.name if self.admin else self.user.name) if (self.admin or self.user) else 'Unknown',
            'author_type': 'admin' if self.is_admin_response else 'user',
            'comment_text': self.comment_text,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_admin_response': self.is_admin_response
        }
    
    def __repr__(self):
        return f'<ComplaintComment {self.id}>'


class CannedResponse(db.Model):
    """Pre-written response templates for admins"""
    __tablename__ = 'canned_responses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=True)  # e.g., 'General', 'Technical', 'Academic'
    created_by_admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    is_global = db.Column(db.Boolean, default=True)  # True = all admins can use, False = only creator
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    created_by_admin = db.relationship('Admin', backref='canned_responses')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'body': self.body,
            'category': self.category,
            'created_by_admin_id': self.created_by_admin_id,
            'created_by_admin_name': self.created_by_admin.name if self.created_by_admin else None,
            'is_global': self.is_global,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<CannedResponse {self.id}>'


class ComplaintTemplate(db.Model):
    """Quick complaint templates for users"""
    __tablename__ = 'complaint_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description_template = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum(ComplaintCategory), nullable=False)
    suggested_priority = db.Column(db.Enum(ComplaintPriority), default=ComplaintPriority.MEDIUM)
    is_active = db.Column(db.Boolean, default=True)
    usage_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description_template': self.description_template,
            'category': self.category.value,
            'suggested_priority': self.suggested_priority.value,
            'is_active': self.is_active,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<ComplaintTemplate {self.id}>'


class SLATracking(db.Model):
    """Track SLA metrics and violations"""
    __tablename__ = 'sla_tracking'
    
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False, unique=True)
    expected_resolution_time = db.Column(db.DateTime, nullable=False)  # Based on priority
    first_response_time = db.Column(db.DateTime, nullable=True)
    resolution_time = db.Column(db.DateTime, nullable=True)
    
    # Violations
    first_response_breached = db.Column(db.Boolean, default=False)
    resolution_breached = db.Column(db.Boolean, default=False)
    breach_notifications_sent = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    complaint = db.relationship('Complaint', backref='sla_tracking', uselist=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'complaint_id': self.complaint_id,
            'expected_resolution_time': self.expected_resolution_time.isoformat(),
            'first_response_time': self.first_response_time.isoformat() if self.first_response_time else None,
            'resolution_time': self.resolution_time.isoformat() if self.resolution_time else None,
            'first_response_breached': self.first_response_breached,
            'resolution_breached': self.resolution_breached,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<SLATracking {self.id}>'