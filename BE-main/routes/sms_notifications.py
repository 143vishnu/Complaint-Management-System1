"""
SMS Notifications using Twilio
Sends SMS alerts for complaint updates
"""
from flask import Blueprint, request, jsonify
from models.complaint import Complaint
from models.user import User, db
from models.admin import Admin
from functools import wraps
import jwt
import os
from datetime import datetime

sms_bp = Blueprint('sms', __name__, url_prefix='/api/sms')

# Try importing Twilio - optional dependency
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'success': False, 'message': 'Token is required'}), 401
        
        try:
            token = token.split(' ')[1] if ' ' in token else token
            jwt_secret = os.getenv('JWT_TOKEN')
            jwt.decode(token, jwt_secret, algorithms=['HS256'])
        except Exception as e:
            return jsonify({'success': False, 'message': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated

def get_twilio_client():
    """Initialize Twilio client"""
    if not TWILIO_AVAILABLE:
        return None
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    if not account_sid or not auth_token:
        return None
    
    return Client(account_sid, auth_token)

def send_sms_notification(phone_number, message):
    """
    Send SMS notification
    Returns: (success: bool, message: str)
    """
    try:
        if not TWILIO_AVAILABLE:
            return False, "Twilio not installed"
        
        client = get_twilio_client()
        if not client:
            return False, "Twilio credentials not configured"
        
        twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
        if not twilio_phone:
            return False, "Twilio phone number not configured"
        
        # Ensure phone number is in E.164 format
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number
        
        message = client.messages.create(
            body=message,
            from_=twilio_phone,
            to=phone_number
        )
        
        return True, f"SMS sent with SID: {message.sid}"
        
    except Exception as e:
        return False, str(e)

@sms_bp.route('/register', methods=['POST'])
@token_required
def register_phone():
    """
    Register phone number for SMS notifications
    """
    try:
        data = request.json
        user_id = data.get('user_id')
        phone_number = data.get('phone_number')
        
        if not phone_number:
            return jsonify({
                'success': False,
                'message': 'Phone number is required'
            }), 400
        
        # Validate phone format (basic check)
        phone_clean = ''.join(c for c in phone_number if c.isdigit())
        if len(phone_clean) < 10:
            return jsonify({
                'success': False,
                'message': 'Invalid phone number format'
            }), 400
        
        user = User.query.get(user_id)
        if not user:
            user = Admin.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Store phone number
        user.phone_number = phone_number
        user.sms_notifications = True
        db.session.add(user)
        db.session.commit()
        
        # Send verification SMS
        success, msg = send_sms_notification(
            phone_number,
            f"Welcome to Query Pro! Your phone is registered for SMS notifications. Reply with any complaints or questions!"
        )
        
        return jsonify({
            'success': success,
            'message': msg,
            'data': {
                'phone_registered': True,
                'sms_enabled': True
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error registering phone',
            'error': str(e)
        }), 500

@sms_bp.route('/send/complaint/<int:complaint_id>', methods=['POST'])
@token_required
def send_complaint_notification(complaint_id):
    """
    Send SMS notification about complaint status update
    """
    try:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({
                'success': False,
                'message': 'Complaint not found'
            }), 404
        
        user = User.query.get(complaint.user_id)
        if not user or not user.phone_number or not user.sms_notifications:
            return jsonify({
                'success': False,
                'message': 'User has not registered for SMS notifications'
            }), 400
        
        data = request.json or {}
        message_type = data.get('type', 'update')  # update, status_change, resolved
        
        # Build message based on type
        if message_type == 'status_change':
            sms_text = f"Complaint #{complaint.ticket_id} status changed to {complaint.status}."
        elif message_type == 'resolved':
            sms_text = f"Good news! Complaint #{complaint.ticket_id} has been resolved."
        elif message_type == 'escalated':
            sms_text = f"Complaint #{complaint.ticket_id} has been escalated for faster resolution."
        else:
            sms_text = f"Update on Complaint #{complaint.ticket_id}: {data.get('message', 'Your complaint has been updated.')} Reply STOP to unsubscribe."
        
        success, msg = send_sms_notification(user.phone_number, sms_text)
        
        return jsonify({
            'success': success,
            'message': msg,
            'data': {
                'complaint_id': complaint_id,
                'notification_sent': success
            }
        }), 200 if success else 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error sending notification',
            'error': str(e)
        }), 500

@sms_bp.route('/send/bulk', methods=['POST'])
@token_required
def send_bulk_sms():
    """
    Send bulk SMS to multiple users
    Useful for admin notifications
    """
    try:
        data = request.json
        user_ids = data.get('user_ids', [])
        message = data.get('message')
        
        if not user_ids or not message:
            return jsonify({
                'success': False,
                'message': 'User IDs and message are required'
            }), 400
        
        sent_count = 0
        failed_count = 0
        
        for user_id in user_ids:
            user = User.query.get(user_id)
            if not user:
                user = Admin.query.get(user_id)
            
            if user and user.phone_number and user.sms_notifications:
                success, _ = send_sms_notification(user.phone_number, message)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
        
        return jsonify({
            'success': True,
            'message': f'SMS sent to {sent_count} users',
            'data': {
                'total_users': len(user_ids),
                'sent': sent_count,
                'failed': failed_count
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error sending bulk SMS',
            'error': str(e)
        }), 500

@sms_bp.route('/preferences/<int:user_id>', methods=['GET', 'PUT'])
@token_required
def sms_preferences(user_id):
    """
    Get or update SMS notification preferences
    """
    try:
        user = User.query.get(user_id)
        if not user:
            user = Admin.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'data': {
                    'phone_number': user.phone_number,
                    'sms_notifications': user.sms_notifications,
                    'notification_types': {
                        'status_updates': True,
                        'escalations': True,
                        'resolutions': True,
                        'bulk_notifications': True
                    }
                }
            }), 200
        
        elif request.method == 'PUT':
            data = request.json
            
            if 'sms_notifications' in data:
                user.sms_notifications = data['sms_notifications']
            
            db.session.add(user)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'SMS preferences updated',
                'data': {
                    'sms_notifications': user.sms_notifications
                }
            }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error updating preferences',
            'error': str(e)
        }), 500

@sms_bp.route('/status', methods=['GET'])
def sms_service_status():
    """
    Check if SMS service is available
    """
    try:
        client = get_twilio_client()
        available = client is not None and TWILIO_AVAILABLE
        
        return jsonify({
            'success': True,
            'data': {
                'sms_available': available,
                'provider': 'Twilio' if available else 'Not configured',
                'status': 'Active' if available else 'Inactive'
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'data': {
                'sms_available': False,
                'status': 'Error',
                'error': str(e)
            }
        }), 500
