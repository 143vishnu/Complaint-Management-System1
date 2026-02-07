"""
Two-Factor Authentication (2FA) Implementation
Supports Email OTP and TOTP (Time-based One-Time Password)
"""
from flask import Blueprint, request, jsonify
from models.user import User, db
from models.admin import Admin
from utils.email_service import EmailService
from functools import wraps
import jwt
import os
from datetime import datetime, timedelta
import random
import string
import pyotp

twofa_bp = Blueprint('twofa', __name__, url_prefix='/api/2fa')

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

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

@twofa_bp.route('/enable/email', methods=['POST'])
@token_required
def enable_email_otp():
    """
    Enable email-based 2FA for user
    Sends a verification OTP to email
    """
    try:
        data = request.json
        user_id = data.get('user_id')
        email = data.get('email')
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            user = Admin.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Generate OTP
        otp = generate_otp()
        
        # Store OTP (with 10-minute expiry)
        user.twofa_otp = otp
        user.twofa_otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        user.twofa_method = 'email'
        user.twofa_enabled = False  # Not verified yet
        db.session.add(user)
        db.session.commit()
        
        # Send OTP via email
        email_service = EmailService()
        subject = "Your 2FA Verification Code"
        body = f"""
        Hello {user.name},
        
        Your 2FA verification code is: {otp}
        This code will expire in 10 minutes.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        Query Pro Team
        """
        
        email_sent, message = email_service.send_email(email, subject, body)
        
        if email_sent:
            return jsonify({
                'success': True,
                'message': 'OTP sent to your email',
                'data': {
                    'session_id': f'2fa_verify_{user_id}_{datetime.utcnow().timestamp()}'
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to send OTP: {message}'
            }), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error enabling 2FA',
            'error': str(e)
        }), 500

@twofa_bp.route('/verify/email', methods=['POST'])
@token_required
def verify_email_otp():
    """
    Verify email OTP and enable 2FA
    """
    try:
        data = request.json
        user_id = data.get('user_id')
        otp = data.get('otp')
        
        if not otp:
            return jsonify({
                'success': False,
                'message': 'OTP is required'
            }), 400
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            user = Admin.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Check OTP validity
        if not user.twofa_otp or user.twofa_otp != otp:
            return jsonify({
                'success': False,
                'message': 'Invalid OTP'
            }), 400
        
        # Check expiry
        if user.twofa_otp_expiry < datetime.utcnow():
            return jsonify({
                'success': False,
                'message': 'OTP expired'
            }), 400
        
        # Enable 2FA
        user.twofa_enabled = True
        user.twofa_otp = None
        user.twofa_otp_expiry = None
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Email 2FA enabled successfully',
            'data': {
                'twofa_enabled': True,
                'method': 'email'
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error verifying OTP',
            'error': str(e)
        }), 500

@twofa_bp.route('/enable/totp', methods=['POST'])
@token_required
def enable_totp():
    """
    Enable TOTP (Google Authenticator) based 2FA
    Returns QR code and secret for scanning
    """
    try:
        data = request.json
        user_id = data.get('user_id')
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            user = Admin.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Generate TOTP secret
        totp_secret = pyotp.random_base32()
        
        # Create TOTP object
        totp = pyotp.TOTP(totp_secret)
        
        # Generate provisioning URL for QR code
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name='Query Pro'
        )
        
        # Store secret (not verified yet)
        user.totp_secret = totp_secret
        user.totp_verified = False
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'TOTP setup initiated',
            'data': {
                'secret': totp_secret,
                'qr_uri': provisioning_uri,
                'instructions': 'Scan this QR code with Google Authenticator or similar app'
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error enabling TOTP',
            'error': str(e)
        }), 500

@twofa_bp.route('/verify/totp', methods=['POST'])
@token_required
def verify_totp():
    """
    Verify TOTP code and enable TOTP 2FA
    """
    try:
        data = request.json
        user_id = data.get('user_id')
        code = data.get('code')
        
        if not code:
            return jsonify({
                'success': False,
                'message': 'TOTP code is required'
            }), 400
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            user = Admin.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        if not user.totp_secret:
            return jsonify({
                'success': False,
                'message': 'TOTP not initiated for this user'
            }), 400
        
        # Verify code
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code):
            return jsonify({
                'success': False,
                'message': 'Invalid TOTP code'
            }), 400
        
        # Enable TOTP 2FA
        user.twofa_enabled = True
        user.twofa_method = 'totp'
        user.totp_verified = True
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'TOTP 2FA enabled successfully',
            'data': {
                'twofa_enabled': True,
                'method': 'totp'
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error verifying TOTP',
            'error': str(e)
        }), 500

@twofa_bp.route('/disable', methods=['POST'])
@token_required
def disable_twofa():
    """
    Disable 2FA for user
    """
    try:
        data = request.json
        user_id = data.get('user_id')
        password = data.get('password')  # Require password to disable
        
        if not password:
            return jsonify({
                'success': False,
                'message': 'Password required to disable 2FA'
            }), 400
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            user = Admin.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Verify password
        if not user.check_password(password):
            return jsonify({
                'success': False,
                'message': 'Invalid password'
            }), 401
        
        # Disable 2FA
        user.twofa_enabled = False
        user.twofa_method = None
        user.twofa_otp = None
        user.totp_secret = None
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '2FA disabled successfully',
            'data': {
                'twofa_enabled': False
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error disabling 2FA',
            'error': str(e)
        }), 500

@twofa_bp.route('/status/<int:user_id>', methods=['GET'])
@token_required
def get_twofa_status(user_id):
    """
    Get 2FA status for user
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
        
        return jsonify({
            'success': True,
            'data': {
                'twofa_enabled': user.twofa_enabled,
                'twofa_method': user.twofa_method,
                'has_totp_secret': bool(user.totp_secret),
                'last_updated': user.updated_at.isoformat() if hasattr(user, 'updated_at') else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error fetching 2FA status',
            'error': str(e)
        }), 500
