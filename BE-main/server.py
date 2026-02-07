from flask import Flask, jsonify
from flask_cors import CORS
from flask_mail import Mail
from models.user import db
from models.admin import Admin
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.complaints import complaints_bp
from routes.chatbot import chatbot_bp
from routes.features import features_bp
from routes.duplicate_detection import duplicate_bp
from routes.twofa import twofa_bp
from routes.sms_notifications import sms_bp
from routes.video_support import video_bp
from routes.location_based import location_bp
from routes.trend_analysis import trends_bp
from trained_models.standalone_ml import ml_bp
from utils.email_service import email_service
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    _neon_uri = os.getenv('NEON_URI')
    if not _neon_uri or '<' in _neon_uri:
        _neon_uri = 'sqlite:///app.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = _neon_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=[
        "http://localhost:5174",
        "http://localhost:5173",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:5178",
        "https://queriespro.vercel.app"
    ], supports_credentials=True, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # Initialize email service
    email_service.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(complaints_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(features_bp)
    app.register_blueprint(duplicate_bp)
    app.register_blueprint(twofa_bp)
    app.register_blueprint(sms_bp)
    app.register_blueprint(video_bp)
    app.register_blueprint(location_bp)
    app.register_blueprint(trends_bp)
    app.register_blueprint(ml_bp)
    
    # Health check endpoint
    @app.route('/', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'Server is running',
            'port': 6969
        }), 200
    
    # API root endpoint
    @app.route('/api', methods=['GET'])
    def api_root():
        return jsonify({
            'success': True,
            'message': 'Complaint Management System API',
            'version': '2.0.0',
            'endpoints': {
                'auth': {
                    'login': 'POST /api/auth/login',
                    'register': 'POST /api/auth/register',
                    'logout': 'POST /api/auth/logout'
                },
                'complaints': {
                    'list': 'GET /api/complaints',
                    'create': 'POST /api/complaints',
                    'get': 'GET /api/complaints/<id>',
                    'update': 'PUT /api/complaints/<id>'
                },
                'admin': {
                    'dashboard': 'GET /api/admin/dashboard',
                    'statistics': 'GET /api/admin/statistics'
                },
                'chatbot': {
                    'chat': 'POST /api/chatbot/chat'
                },
                'features': {
                    'tags': 'GET/POST/DELETE /api/features/complaints/<id>/tags',
                    'popular_tags': 'GET /api/features/tags/popular',
                    'admin_notes': 'GET/POST /api/features/complaints/<id>/notes',
                    'comments': 'GET/POST /api/features/complaints/<id>/comments',
                    'canned_responses': 'GET/POST/DELETE /api/features/canned-responses',
                    'templates': 'GET/POST /api/features/templates',
                    'export': 'GET /api/features/export/complaints',
                    'search': 'GET /api/features/search',
                    'assign': 'POST /api/features/complaints/<id>/assign',
                    'sla': 'GET /api/features/complaints/<id>/sla',
                    'escalate': 'POST /api/features/escalate-stale',
                    'anonymous': 'PUT /api/features/complaints/<id>/toggle-anonymous'
                }
            }
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': 'Endpoint not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500
    
    return app
app = create_app()
if __name__ == '__main__':
    app = create_app()
    
    # Create tables
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    
    print("Starting server on port 6969...")
    app.run(host='0.0.0.0', port=6969, debug=True)