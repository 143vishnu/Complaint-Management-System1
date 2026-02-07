"""
Advanced Features Routes
- Tags, Admin Notes, Canned Responses, Templates, Comments
- Export, Search, Assignment, SLA Tracking, Auto-escalation
"""

from flask import Blueprint, request, jsonify, make_response
from models.complaint import (
    Complaint, AdminNote, ComplaintComment, CannedResponse, 
    ComplaintTemplate, SLATracking, ComplaintStatus, db
)
from models.user import User
from models.admin import Admin
import jwt
import os
from functools import wraps
from datetime import datetime, timedelta
import csv
import io

features_bp = Blueprint('features', __name__, url_prefix='/api/features')

def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Token is missing'
            }), 401
        
        try:
            data = jwt.decode(token, os.getenv('JWT_TOKEN'), algorithms=['HS256'])
            current_user_id = data.get('user_id') or data.get('admin_id')
            current_user_role = data.get('role')
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Token is invalid'}), 401
        
        return f(current_user_id, current_user_role, *args, **kwargs)
    
    return decorated

# ===================== TAGS MANAGEMENT =====================

@features_bp.route('/complaints/<int:complaint_id>/tags', methods=['GET'])
@token_required
def get_tags(current_user_id, current_user_role, complaint_id):
    """Get tags for a complaint"""
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        
        if current_user_role in ['student', 'faculty']:
            if complaint.user_id != current_user_id:
                return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        return jsonify({
            'success': True,
            'data': {'tags': complaint.tags}
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@features_bp.route('/complaints/<int:complaint_id>/tags', methods=['POST'])
@token_required
def add_tags(current_user_id, current_user_role, complaint_id):
    """Add tags to a complaint (admin only)"""
    if current_user_role != 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        data = request.get_json()
        tags = data.get('tags', [])
        
        if not isinstance(tags, list):
            return jsonify({'success': False, 'message': 'Tags must be a list'}), 400
        
        # Validate tags
        tags = [str(tag).strip() for tag in tags if tag]
        
        complaint.tags = list(set(complaint.tags + tags))  # Add unique tags
        complaint.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tags added successfully',
            'data': {'tags': complaint.tags}
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@features_bp.route('/complaints/<int:complaint_id>/tags/<tag>', methods=['DELETE'])
@token_required
def remove_tag(current_user_id, current_user_role, complaint_id, tag):
    """Remove a tag from complaint (admin only)"""
    if current_user_role != 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        complaint.tags = [t for t in complaint.tags if t != tag]
        complaint.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tag removed successfully',
            'data': {'tags': complaint.tags}
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ===================== ADMIN NOTES (Private) =====================

@features_bp.route('/complaints/<int:complaint_id>/notes', methods=['GET'])
@token_required
def get_admin_notes(current_user_id, current_user_role, complaint_id):
    """Get admin notes for a complaint (admin only)"""
    if current_user_role != 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        notes = AdminNote.query.filter_by(complaint_id=complaint_id).order_by(AdminNote.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': {'notes': [note.to_dict() for note in notes]}
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@features_bp.route('/complaints/<int:complaint_id>/notes', methods=['POST'])
@token_required
def add_admin_note(current_user_id, current_user_role, complaint_id):
    """Add admin note to a complaint"""
    if current_user_role != 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        data = request.get_json()
        note_text = data.get('note_text', '').strip()
        
        if not note_text:
            return jsonify({'success': False, 'message': 'Note text is required'}), 400
        
        admin = Admin.query.get(current_user_id)
        note = AdminNote(
            complaint_id=complaint_id,
            admin_id=current_user_id,
            note_text=note_text
        )
        
        db.session.add(note)
        complaint.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Note added successfully',
            'data': {'note': note.to_dict()}
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ===================== COMMENTS (Public Discussion) =====================

@features_bp.route('/complaints/<int:complaint_id>/comments', methods=['GET'])
@token_required
def get_comments(current_user_id, current_user_role, complaint_id):
    """Get comments/discussion thread for a complaint"""
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        comments = ComplaintComment.query.filter_by(complaint_id=complaint_id).order_by(ComplaintComment.created_at.asc()).all()
        
        return jsonify({
            'success': True,
            'data': {'comments': [comment.to_dict() for comment in comments]}
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@features_bp.route('/complaints/<int:complaint_id>/comments', methods=['POST'])
@token_required
def add_comment(current_user_id, current_user_role, complaint_id):
    """Add comment to complaint discussion"""
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        data = request.get_json()
        comment_text = data.get('comment_text', '').strip()
        
        if not comment_text:
            return jsonify({'success': False, 'message': 'Comment text is required'}), 400
        
        if len(comment_text) < 3:
            return jsonify({'success': False, 'message': 'Comment must be at least 3 characters'}), 400
        
        is_admin = current_user_role == 'admin'
        
        comment = ComplaintComment(
            complaint_id=complaint_id,
            user_id=current_user_id if not is_admin else None,
            admin_id=current_user_id if is_admin else None,
            comment_text=comment_text,
            is_admin_response=is_admin
        )
        
        db.session.add(comment)
        complaint.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Comment added successfully',
            'data': {'comment': comment.to_dict()}
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ===================== CANNED RESPONSES (Admin Templates) =====================

@features_bp.route('/canned-responses', methods=['GET'])
@token_required
def get_canned_responses(current_user_id, current_user_role):
    """Get available canned response templates"""
    if current_user_role != 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        category = request.args.get('category', None)
        query = CannedResponse.query.filter_by(is_global=True)
        
        if category:
            query = query.filter_by(category=category)
        
        responses = query.order_by(CannedResponse.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': {'responses': [resp.to_dict() for resp in responses]}
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@features_bp.route('/canned-responses', methods=['POST'])
@token_required
def create_canned_response(current_user_id, current_user_role):
    """Create a new canned response template"""
    if current_user_role != 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        body = data.get('body', '').strip()
        category = data.get('category', '').strip()
        is_global = data.get('is_global', True)
        
        if not title or not body:
            return jsonify({'success': False, 'message': 'Title and body are required'}), 400
        
        response = CannedResponse(
            title=title,
            body=body,
            category=category if category else None,
            created_by_admin_id=current_user_id,
            is_global=is_global
        )
        
        db.session.add(response)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Canned response created successfully',
            'data': {'response': response.to_dict()}
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@features_bp.route('/canned-responses/<int:response_id>', methods=['DELETE'])
@token_required
def delete_canned_response(current_user_id, current_user_role, response_id):
    """Delete a canned response"""
    if current_user_role != 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        response = CannedResponse.query.get_or_404(response_id)
        
        # Only creator or global admins can delete
        if response.created_by_admin_id != current_user_id:
            return jsonify({'success': False, 'message': 'You can only delete your own responses'}), 403
        
        db.session.delete(response)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Canned response deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ===================== COMPLAINT TEMPLATES (User Quick Submit) =====================

@features_bp.route('/templates', methods=['GET'])
@token_required
def get_templates(current_user_id, current_user_role):
    """Get available complaint templates"""
    try:
        templates = ComplaintTemplate.query.filter_by(is_active=True).order_by(ComplaintTemplate.title).all()
        
        return jsonify({
            'success': True,
            'data': {'templates': [template.to_dict() for template in templates]}
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@features_bp.route('/templates', methods=['POST'])
@token_required
def create_template(current_user_id, current_user_role):
    """Create a new complaint template (admin only)"""
    if current_user_role != 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        description_template = data.get('description_template', '').strip()
        category = data.get('category', 'Technical')
        suggested_priority = data.get('suggested_priority', 'medium')
        
        if not title or not description_template:
            return jsonify({'success': False, 'message': 'Title and description_template are required'}), 400
        
        from models.complaint import ComplaintCategory, ComplaintPriority
        
        template = ComplaintTemplate(
            title=title,
            description_template=description_template,
            category=ComplaintCategory(category),
            suggested_priority=ComplaintPriority(suggested_priority)
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Template created successfully',
            'data': {'template': template.to_dict()}
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ===================== EXPORT TO CSV =====================

@features_bp.route('/export/complaints', methods=['GET'])
@token_required
def export_complaints_csv(current_user_id, current_user_role):
    """Export complaints to CSV"""
    try:
        if current_user_role == 'admin':
            complaints = Complaint.query.all()
        else:
            complaints = Complaint.query.filter_by(user_id=current_user_id).all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Ticket ID', 'Title', 'Category', 'Priority', 'Status',
            'User', 'Created At', 'Updated At', 'Tags', 'Escalated'
        ])
        
        # Data rows
        for complaint in complaints:
            writer.writerow([
                complaint.ticket_id,
                complaint.title,
                complaint.category.value,
                complaint.priority.value,
                complaint.status.value,
                complaint.user.name if complaint.user and not complaint.is_anonymous else 'Anonymous',
                complaint.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                complaint.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                ', '.join(complaint.tags),
                'Yes' if complaint.escalated else 'No'
            ])
        
        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename=complaints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response.headers["Content-Type"] = "text/csv"
        
        return response
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===================== ADVANCED SEARCH =====================

@features_bp.route('/search', methods=['GET'])
@token_required
def search_complaints(current_user_id, current_user_role):
    """Advanced search for complaints"""
    try:
        query_text = request.args.get('q', '').strip()
        category = request.args.get('category', None)
        priority = request.args.get('priority', None)
        status = request.args.get('status', None)
        tags = request.args.get('tags', '').split(',') if request.args.get('tags') else []
        page = request.args.get('page', 1, type=int)
        
        query = Complaint.query
        
        # User can only search their own complaints unless admin
        if current_user_role in ['student', 'faculty']:
            query = query.filter_by(user_id=current_user_id)
        
        # Full-text search in title and description
        if query_text:
            query = query.filter(
                (Complaint.title.ilike(f'%{query_text}%')) |
                (Complaint.description.ilike(f'%{query_text}%')) |
                (Complaint.ticket_id.ilike(f'%{query_text}%'))
            )
        
        # Filters
        if category:
            from models.complaint import ComplaintCategory
            query = query.filter_by(category=ComplaintCategory(category))
        
        if priority:
            from models.complaint import ComplaintPriority
            query = query.filter_by(priority=ComplaintPriority(priority))
        
        if status:
            from models.complaint import ComplaintStatus
            query = query.filter_by(status=ComplaintStatus(status))
        
        # Tag filter - complaints must have ALL specified tags
        if tags and any(tag.strip() for tag in tags):
            valid_tags = [tag.strip() for tag in tags if tag.strip()]
            for tag in valid_tags:
                query = query.filter(Complaint.tags.contains(tag))
        
        # Paginate
        results = query.order_by(Complaint.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'complaints': [c.to_dict() for c in results.items],
                'pagination': {
                    'page': page,
                    'per_page': 10,
                    'total': results.total,
                    'pages': results.pages
                }
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===================== COMPLAINT ASSIGNMENT =====================

@features_bp.route('/complaints/<int:complaint_id>/assign', methods=['POST'])
@token_required
def assign_complaint(current_user_id, current_user_role, complaint_id):
    """Assign complaint to an admin"""
    if current_user_role != 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        data = request.get_json()
        admin_id = data.get('admin_id')
        
        if not admin_id:
            return jsonify({'success': False, 'message': 'admin_id is required'}), 400
        
        admin = Admin.query.get_or_404(admin_id)
        
        complaint.assigned_to_admin_id = admin_id
        complaint.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Complaint assigned to {admin.name}',
            'data': {'complaint': complaint.to_dict()}
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ===================== SLA TRACKING =====================

@features_bp.route('/complaints/<int:complaint_id>/sla', methods=['GET'])
@token_required
def get_sla_tracking(current_user_id, current_user_role, complaint_id):
    """Get SLA tracking information"""
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        sla = SLATracking.query.filter_by(complaint_id=complaint_id).first()
        
        if sla:
            return jsonify({
                'success': True,
                'data': {'sla': sla.to_dict()}
            }), 200
        else:
            return jsonify({
                'success': True,
                'data': {'sla': None}
            }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===================== AUTO-ESCALATION =====================

@features_bp.route('/escalate-stale', methods=['POST'])
@token_required
def escalate_stale_complaints(current_user_id, current_user_role):
    """Auto-escalate complaints pending for > 24 hours (admin only)"""
    if current_user_role != 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        from models.complaint import ComplaintStatus
        
        # Find complaints pending for > 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        stale_complaints = Complaint.query.filter(
            Complaint.status == ComplaintStatus.PENDING,
            Complaint.created_at < cutoff_time,
            Complaint.escalated == False
        ).all()
        
        escalated_count = 0
        for complaint in stale_complaints:
            complaint.escalated = True
            complaint.escalation_level += 1
            complaint.last_escalation_at = datetime.utcnow()
            escalated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{escalated_count} complaints escalated',
            'data': {'escalated_count': escalated_count}
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ===================== ANONYMOUS COMPLAINTS =====================

@features_bp.route('/complaints/<int:complaint_id>/toggle-anonymous', methods=['PUT'])
@token_required
def toggle_anonymous(current_user_id, current_user_role, complaint_id):
    """Toggle anonymous status of complaint"""
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        
        # Only user who submitted or admin can toggle
        if current_user_role in ['student', 'faculty']:
            if complaint.user_id != current_user_id:
                return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        complaint.is_anonymous = not complaint.is_anonymous
        complaint.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Complaint is now {"anonymous" if complaint.is_anonymous else "public"}',
            'data': {'is_anonymous': complaint.is_anonymous}
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ===================== POPULAR TAGS =====================

@features_bp.route('/tags/popular', methods=['GET'])
@token_required
def get_popular_tags(current_user_id, current_user_role):
    """Get most popular tags across all complaints"""
    try:
        all_complaints = Complaint.query.all()
        tag_counts = {}
        
        for complaint in all_complaints:
            for tag in complaint.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Sort by frequency
        popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return jsonify({
            'success': True,
            'data': {'tags': [{'name': tag, 'count': count} for tag, count in popular_tags]}
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
