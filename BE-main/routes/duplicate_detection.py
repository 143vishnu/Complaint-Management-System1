"""
Duplicate Detection Service
Detects similar complaints using TF-IDF similarity scoring
"""
from flask import Blueprint, request, jsonify
from models.complaint import Complaint
from models.user import db
from functools import wraps
import jwt
import os
from datetime import datetime
from difflib import SequenceMatcher

duplicate_bp = Blueprint('duplicates', __name__, url_prefix='/api/duplicates')

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

def calculate_similarity(text1, text2):
    """Calculate text similarity using SequenceMatcher (0 to 1, where 1 is identical)"""
    if not text1 or not text2:
        return 0.0
    text1 = text1.lower().strip()
    text2 = text2.lower().strip()
    return SequenceMatcher(None, text1, text2).ratio()

def find_duplicate_candidates(complaint_id, title, description, threshold=0.65):
    """
    Find potential duplicate complaints based on title and description similarity
    Returns list of similar complaints above threshold
    """
    try:
        # Get all complaints except current one
        all_complaints = Complaint.query.filter(Complaint.id != complaint_id).all()
        
        duplicates = []
        
        for complaint in all_complaints:
            # Calculate similarity scores
            title_similarity = calculate_similarity(title, complaint.title)
            desc_similarity = calculate_similarity(description, complaint.description)
            
            # Weighted average (title more important)
            overall_similarity = (title_similarity * 0.6) + (desc_similarity * 0.4)
            
            if overall_similarity >= threshold:
                duplicates.append({
                    'complaint_id': complaint.id,
                    'ticket_id': complaint.ticket_id,
                    'title': complaint.title,
                    'description': complaint.description[:100] + '...' if len(complaint.description) > 100 else complaint.description,
                    'status': complaint.status,
                    'created_at': complaint.created_at.isoformat() if complaint.created_at else None,
                    'similarity_score': round(overall_similarity * 100, 2),
                    'category': complaint.category,
                    'priority': complaint.priority
                })
        
        # Sort by similarity score descending
        duplicates.sort(key=lambda x: x['similarity_score'], reverse=True)
        return duplicates[:10]  # Return top 10 matches
        
    except Exception as e:
        return []

@duplicate_bp.route('/check', methods=['POST'])
@token_required
def check_duplicates():
    """
    Check if a new/edited complaint has duplicates
    Useful when creating or updating complaints
    """
    try:
        data = request.json
        
        if not data.get('title') or not data.get('description'):
            return jsonify({
                'success': False,
                'message': 'Title and description are required'
            }), 400
        
        complaint_id = data.get('complaint_id', None)  # None for new complaints
        
        duplicates = find_duplicate_candidates(
            complaint_id or 0,
            data['title'],
            data['description'],
            threshold=float(data.get('threshold', 0.65))
        )
        
        return jsonify({
            'success': True,
            'message': f'Found {len(duplicates)} potential duplicate(s)',
            'data': {
                'duplicates': duplicates,
                'has_duplicates': len(duplicates) > 0,
                'similarity_threshold': data.get('threshold', 0.65)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error checking duplicates',
            'error': str(e)
        }), 500

@duplicate_bp.route('/merge/<int:complaint_id>', methods=['POST'])
@token_required
def merge_duplicates(complaint_id):
    """
    Merge duplicate complaints into one
    Keeps primary complaint, links duplicates to it
    """
    try:
        data = request.json
        duplicate_ids = data.get('duplicate_ids', [])
        
        if not duplicate_ids:
            return jsonify({
                'success': False,
                'message': 'Must provide duplicate complaint IDs'
            }), 400
        
        primary = Complaint.query.get(complaint_id)
        if not primary:
            return jsonify({
                'success': False,
                'message': 'Primary complaint not found'
            }), 404
        
        # Add to complaint's tags that it's been merged
        for dup_id in duplicate_ids:
            duplicate = Complaint.query.get(dup_id)
            if duplicate:
                # Mark as duplicate by updating tags
                if not duplicate.tags:
                    duplicate.tags = []
                if 'merged' not in duplicate.tags:
                    duplicate.tags.append('merged')
                if f'merged_into_{complaint_id}' not in duplicate.tags:
                    duplicate.tags.append(f'merged_into_{complaint_id}')
                
                # Mark original complaint status
                duplicate.status = 'duplicate'
                db.session.add(duplicate)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully merged {len(duplicate_ids)} complaint(s)',
            'data': {
                'primary_complaint_id': complaint_id,
                'merged_count': len(duplicate_ids)
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error merging duplicates',
            'error': str(e)
        }), 500

@duplicate_bp.route('/report', methods=['GET'])
@token_required
def duplicate_report():
    """
    Get a report of all potential duplicates in the system
    Useful for admins to identify issues
    """
    try:
        all_complaints = Complaint.query.all()
        duplicates_found = []
        checked_pairs = set()
        
        for i, complaint1 in enumerate(all_complaints):
            for complaint2 in all_complaints[i+1:]:
                pair_key = tuple(sorted([complaint1.id, complaint2.id]))
                
                if pair_key not in checked_pairs:
                    checked_pairs.add(pair_key)
                    
                    similarity = (
                        calculate_similarity(complaint1.title, complaint2.title) * 0.6 +
                        calculate_similarity(complaint1.description, complaint2.description) * 0.4
                    )
                    
                    if similarity >= 0.65:
                        duplicates_found.append({
                            'complaint_1': {
                                'id': complaint1.id,
                                'ticket_id': complaint1.ticket_id,
                                'title': complaint1.title,
                                'status': complaint1.status
                            },
                            'complaint_2': {
                                'id': complaint2.id,
                                'ticket_id': complaint2.ticket_id,
                                'title': complaint2.title,
                                'status': complaint2.status
                            },
                            'similarity_score': round(similarity * 100, 2)
                        })
        
        duplicates_found.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'message': f'Found {len(duplicates_found)} potential duplicate pairs',
            'data': {
                'total_complaints': len(all_complaints),
                'duplicate_pairs': duplicates_found,
                'threshold_used': 0.65
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error generating duplicate report',
            'error': str(e)
        }), 500
