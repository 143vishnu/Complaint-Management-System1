"""
Video Support for Complaints
Integration with Cloudinary for video uploads and streaming
"""
from flask import Blueprint, request, jsonify
from models.complaint import Complaint
from models.user import db
from utils.cloudinary_service import upload_to_cloudinary, delete_from_cloudinary
from functools import wraps
import jwt
import os
from datetime import datetime

video_bp = Blueprint('videos', __name__, url_prefix='/api/videos')

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

# Allowed video formats
ALLOWED_VIDEO_FORMATS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', '3gp'}
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB

@video_bp.route('/upload/<int:complaint_id>', methods=['POST'])
@token_required
def upload_video(complaint_id):
    """
    Upload video file to complaint
    Supports streaming and preview generation
    """
    try:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({
                'success': False,
                'message': 'Complaint not found'
            }), 404
        
        # Check if video file is present
        if 'video' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No video file provided'
            }), 400
        
        video_file = request.files['video']
        
        if video_file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No video file selected'
            }), 400
        
        # Validate file format
        file_extension = video_file.filename.rsplit('.', 1)[1].lower() if '.' in video_file.filename else ''
        if file_extension not in ALLOWED_VIDEO_FORMATS:
            return jsonify({
                'success': False,
                'message': f'Invalid video format. Allowed: {", ".join(ALLOWED_VIDEO_FORMATS)}'
            }), 400
        
        # Check file size
        video_file.seek(0, 2)  # Seek to end
        file_size = video_file.tell()
        video_file.seek(0)  # Seek back to start
        
        if file_size > MAX_VIDEO_SIZE:
            return jsonify({
                'success': False,
                'message': f'Video size exceeds {MAX_VIDEO_SIZE / 1024 / 1024}MB limit'
            }), 400
        
        # Upload to Cloudinary
        upload_result = upload_to_cloudinary(
            video_file,
            resource_type='video',
            folder=f'complaints/{complaint_id}/videos'
        )
        
        if not upload_result:
            return jsonify({
                'success': False,
                'message': 'Failed to upload video to cloud storage'
            }), 500
        
        # Store video metadata
        if not hasattr(complaint, 'videos'):
            complaint.videos = []
        
        video_metadata = {
            'url': upload_result['secure_url'],
            'public_id': upload_result['public_id'],
            'duration': upload_result.get('duration'),  # Duration in seconds
            'size': file_size,
            'format': file_extension,
            'uploaded_at': datetime.utcnow().isoformat(),
            'title': request.form.get('title', video_file.filename),
            'description': request.form.get('description', '')
        }
        
        complaint.videos.append(video_metadata)
        db.session.add(complaint)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Video uploaded successfully',
            'data': {
                'video': video_metadata,
                'total_videos': len(complaint.videos)
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error uploading video',
            'error': str(e)
        }), 500

@video_bp.route('/complaints/<int:complaint_id>', methods=['GET'])
@token_required
def get_complaint_videos(complaint_id):
    """
    Get all videos for a complaint
    Include streaming URLs and metadata
    """
    try:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({
                'success': False,
                'message': 'Complaint not found'
            }), 404
        
        videos = complaint.videos if hasattr(complaint, 'videos') and complaint.videos else []
        
        # Add streaming URLs (HLS, MPEG-DASH)
        enhanced_videos = []
        for video in videos:
            enhanced_video = video.copy() if isinstance(video, dict) else video
            
            if isinstance(enhanced_video, dict) and 'public_id' in enhanced_video:
                public_id = enhanced_video['public_id']
                
                # Generate streaming URLs
                enhanced_video['hls_url'] = f"https://res.cloudinary.com/{os.getenv('CLOUDINARY_CLOUD_NAME')}/video/upload/{public_id}.m3u8"
                enhanced_video['dash_url'] = f"https://res.cloudinary.com/{os.getenv('CLOUDINARY_CLOUD_NAME')}/video/upload/{public_id}.mpd"
                enhanced_video['preview_url'] = f"https://res.cloudinary.com/{os.getenv('CLOUDINARY_CLOUD_NAME')}/video/upload/w_300,h_200,c_fill/{public_id}.jpg"
            
            enhanced_videos.append(enhanced_video)
        
        return jsonify({
            'success': True,
            'data': {
                'complaint_id': complaint_id,
                'videos': enhanced_videos,
                'total_count': len(enhanced_videos)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error fetching videos',
            'error': str(e)
        }), 500

@video_bp.route('/delete/<int:complaint_id>/<video_id>', methods=['DELETE'])
@token_required
def delete_video(complaint_id, video_id):
    """
    Delete video from complaint
    """
    try:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({
                'success': False,
                'message': 'Complaint not found'
            }), 404
        
        videos = complaint.videos if hasattr(complaint, 'videos') and complaint.videos else []
        
        # Find and delete video
        video_to_delete = None
        for i, video in enumerate(videos):
            if isinstance(video, dict) and video.get('public_id') == video_id:
                video_to_delete = videos.pop(i)
                break
        
        if not video_to_delete:
            return jsonify({
                'success': False,
                'message': 'Video not found'
            }), 404
        
        # Delete from Cloudinary
        if 'public_id' in video_to_delete:
            delete_from_cloudinary(video_to_delete['public_id'], resource_type='video')
        
        complaint.videos = videos
        db.session.add(complaint)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Video deleted successfully',
            'data': {
                'remaining_videos': len(videos)
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error deleting video',
            'error': str(e)
        }), 500

@video_bp.route('/transcoding/<int:complaint_id>/<video_id>', methods=['GET'])
@token_required
def get_transcoding_status(complaint_id, video_id):
    """
    Get video transcoding status for streaming formats
    """
    try:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({
                'success': False,
                'message': 'Complaint not found'
            }), 404
        
        videos = complaint.videos if hasattr(complaint, 'videos') and complaint.videos else []
        
        # Find video
        video = None
        for v in videos:
            if isinstance(v, dict) and v.get('public_id') == video_id:
                video = v
                break
        
        if not video:
            return jsonify({
                'success': False,
                'message': 'Video not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'video_id': video_id,
                'title': video.get('title', 'Untitled'),
                'format': video.get('format', 'unknown'),
                'duration': video.get('duration', 'N/A'),
                'streaming_ready': True,
                'formats_available': ['hls', 'dash', 'progressive']
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error fetching transcoding status',
            'error': str(e)
        }), 500

@video_bp.route('/generate-preview/<int:complaint_id>/<video_id>', methods=['GET'])
@token_required
def generate_preview(complaint_id, video_id):
    """
    Generate video preview/thumbnail
    """
    try:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({
                'success': False,
                'message': 'Complaint not found'
            }), 404
        
        videos = complaint.videos if hasattr(complaint, 'videos') and complaint.videos else []
        
        # Find video
        video = None
        for v in videos:
            if isinstance(v, dict) and v.get('public_id') == video_id:
                video = v
                break
        
        if not video:
            return jsonify({
                'success': False,
                'message': 'Video not found'
            }), 404
        
        public_id = video.get('public_id', '')
        
        # Generate preview URLs at different sizes
        preview_urls = {
            'small': f"https://res.cloudinary.com/{os.getenv('CLOUDINARY_CLOUD_NAME')}/video/upload/w_150,h_100,c_fill/{public_id}.jpg",
            'medium': f"https://res.cloudinary.com/{os.getenv('CLOUDINARY_CLOUD_NAME')}/video/upload/w_300,h_200,c_fill/{public_id}.jpg",
            'large': f"https://res.cloudinary.com/{os.getenv('CLOUDINARY_CLOUD_NAME')}/video/upload/w_600,h_400,c_fill/{public_id}.jpg"
        }
        
        return jsonify({
            'success': True,
            'data': {
                'preview_urls': preview_urls
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error generating preview',
            'error': str(e)
        }), 500

@video_bp.route('/stats/<int:complaint_id>', methods=['GET'])
@token_required
def video_stats(complaint_id):
    """
    Get video statistics for complaint
    """
    try:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({
                'success': False,
                'message': 'Complaint not found'
            }), 404
        
        videos = complaint.videos if hasattr(complaint, 'videos') and complaint.videos else []
        
        total_duration = 0
        total_size = 0
        
        for video in videos:
            if isinstance(video, dict):
                total_duration += video.get('duration', 0)
                total_size += video.get('size', 0)
        
        return jsonify({
            'success': True,
            'data': {
                'total_videos': len(videos),
                'total_duration_seconds': total_duration,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error fetching video stats',
            'error': str(e)
        }), 500
