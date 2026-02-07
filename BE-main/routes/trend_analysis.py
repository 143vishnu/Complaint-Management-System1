"""
Trend Analysis and Analytics
Historical data, trend charts, and performance metrics
"""
from flask import Blueprint, request, jsonify
from models.complaint import Complaint
from models.user import db
from functools import wraps
import jwt
import os
from datetime import datetime, timedelta
from collections import defaultdict

trends_bp = Blueprint('trends', __name__, url_prefix='/api/trends')

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

def get_date_range(days=30):
    """Get date range for trend analysis"""
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date

@trends_bp.route('/complaints-over-time', methods=['GET'])
@token_required
def complaints_over_time():
    """
    Get complaint counts over time
    Daily aggregation for specified period
    """
    try:
        days = request.args.get('days', default=30, type=int)
        
        if days > 365:
            days = 365
        
        start_date, end_date = get_date_range(days)
        
        # Initialize daily counts
        daily_counts = {}
        current_date = start_date
        while current_date <= end_date:
            daily_counts[current_date.isoformat()] = {
                'date': current_date.isoformat(),
                'count': 0,
                'resolved': 0,
                'pending': 0,
                'escalated': 0
            }
            current_date += timedelta(days=1)
        
        # Count complaints
        all_complaints = Complaint.query.all()
        for complaint in all_complaints:
            if complaint.created_at:
                complaint_date = complaint.created_at.date()
                if start_date <= complaint_date <= end_date:
                    date_key = complaint_date.isoformat()
                    daily_counts[date_key]['count'] += 1
                    
                    if complaint.status == 'resolved':
                        daily_counts[date_key]['resolved'] += 1
                    elif complaint.status in ['pending', 'open']:
                        daily_counts[date_key]['pending'] += 1
                    
                    if hasattr(complaint, 'escalated') and complaint.escalated:
                        daily_counts[date_key]['escalated'] += 1
        
        # Convert to sorted list
        trend_data = sorted(daily_counts.values(), key=lambda x: x['date'])
        
        return jsonify({
            'success': True,
            'data': {
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'trends': trend_data,
                'total_complaints': len(all_complaints),
                'summary': {
                    'total_in_period': sum(d['count'] for d in trend_data),
                    'average_daily': round(sum(d['count'] for d in trend_data) / len(trend_data) if trend_data else 0, 2)
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error fetching complaint trends',
            'error': str(e)
        }), 500

@trends_bp.route('/category-trends', methods=['GET'])
@token_required
def category_trends():
    """
    Get trends by complaint category
    Shows volume and status distribution per category
    """
    try:
        days = request.args.get('days', default=30, type=int)
        start_date, end_date = get_date_range(days)
        
        # Initialize category data
        categories = {}
        
        all_complaints = Complaint.query.all()
        for complaint in all_complaints:
            if complaint.created_at:
                complaint_date = complaint.created_at.date()
                if start_date <= complaint_date <= end_date:
                    category = complaint.category or 'Uncategorized'
                    
                    if category not in categories:
                        categories[category] = {
                            'category': category,
                            'total': 0,
                            'resolved': 0,
                            'pending': 0,
                            'escalated': 0,
                            'percentage': 0
                        }
                    
                    categories[category]['total'] += 1
                    
                    if complaint.status == 'resolved':
                        categories[category]['resolved'] += 1
                    elif complaint.status in ['pending', 'open']:
                        categories[category]['pending'] += 1
                    
                    if hasattr(complaint, 'escalated') and complaint.escalated:
                        categories[category]['escalated'] += 1
        
        # Calculate percentages
        total_complaints = sum(c['total'] for c in categories.values())
        for category in categories.values():
            category['percentage'] = round((category['total'] / total_complaints * 100) if total_complaints > 0 else 0, 2)
            category['resolution_rate'] = round((category['resolved'] / category['total'] * 100) if category['total'] > 0 else 0, 2)
        
        # Sort by volume
        sorted_categories = sorted(categories.values(), key=lambda x: x['total'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'period_days': days,
                'categories': sorted_categories,
                'total_count': len(sorted_categories),
                'top_3': sorted_categories[:3]
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error fetching category trends',
            'error': str(e)
        }), 500

@trends_bp.route('/priority-trends', methods=['GET'])
@token_required
def priority_trends():
    """
    Get trends by priority level
    """
    try:
        days = request.args.get('days', default=30, type=int)
        start_date, end_date = get_date_range(days)
        
        # Initialize priority data
        priorities = {
            'high': {'priority': 'high', 'count': 0, 'resolved': 0, 'avg_resolution_time': 0},
            'medium': {'priority': 'medium', 'count': 0, 'resolved': 0, 'avg_resolution_time': 0},
            'low': {'priority': 'low', 'count': 0, 'resolved': 0, 'avg_resolution_time': 0}
        }
        
        all_complaints = Complaint.query.all()
        resolution_times = defaultdict(list)
        
        for complaint in all_complaints:
            if complaint.created_at:
                complaint_date = complaint.created_at.date()
                if start_date <= complaint_date <= end_date:
                    priority = complaint.priority or 'medium'
                    
                    if priority in priorities:
                        priorities[priority]['count'] += 1
                        
                        if complaint.status == 'resolved':
                            priorities[priority]['resolved'] += 1
                            
                            # Calculate resolution time
                            if hasattr(complaint, 'updated_at') and complaint.updated_at:
                                resolution_time = (complaint.updated_at - complaint.created_at).total_seconds() / 3600
                                resolution_times[priority].append(resolution_time)
        
        # Calculate averages
        for priority in priorities.values():
            times = resolution_times[priority.get('priority', 'medium')]
            if times:
                priority['avg_resolution_time'] = round(sum(times) / len(times), 2)
            priority['resolution_rate'] = round((priority['resolved'] / priority['count'] * 100) if priority['count'] > 0 else 0, 2)
        
        return jsonify({
            'success': True,
            'data': {
                'period_days': days,
                'priorities': list(priorities.values()),
                'summary': {
                    'total_high_priority': priorities['high']['count'],
                    'high_resolution_rate': priorities['high']['resolution_rate'],
                    'avg_high_resolution_hours': priorities['high']['avg_resolution_time']
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error fetching priority trends',
            'error': str(e)
        }), 500

@trends_bp.route('/status-distribution', methods=['GET'])
@token_required
def status_distribution():
    """
    Get overall status distribution
    """
    try:
        days = request.args.get('days', default=30, type=int)
        start_date, end_date = get_date_range(days)
        
        # Initialize status data
        statuses = {}
        
        all_complaints = Complaint.query.all()
        for complaint in all_complaints:
            if complaint.created_at:
                complaint_date = complaint.created_at.date()
                if start_date <= complaint_date <= end_date:
                    status = complaint.status or 'unknown'
                    statuses[status] = statuses.get(status, 0) + 1
        
        total = sum(statuses.values())
        status_data = []
        for status, count in statuses.items():
            status_data.append({
                'status': status,
                'count': count,
                'percentage': round((count / total * 100) if total > 0 else 0, 2)
            })
        
        # Sort by count descending
        status_data.sort(key=lambda x: x['count'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'period_days': days,
                'statuses': status_data,
                'total_complaints': total
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error fetching status distribution',
            'error': str(e)
        }), 500

@trends_bp.route('/comparison', methods=['GET'])
@token_required
def period_comparison():
    """
    Compare metrics between two periods
    Useful for trend analysis and growth metrics
    """
    try:
        current_days = request.args.get('current_days', default=30, type=int)
        
        # Current period
        current_start, current_end = get_date_range(current_days)
        
        # Previous period (same duration)
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=current_days)
        
        # Count complaints in each period
        all_complaints = Complaint.query.all()
        
        current_period = {'count': 0, 'resolved': 0}
        previous_period = {'count': 0, 'resolved': 0}
        
        for complaint in all_complaints:
            if complaint.created_at:
                complaint_date = complaint.created_at.date()
                
                if current_start <= complaint_date <= current_end:
                    current_period['count'] += 1
                    if complaint.status == 'resolved':
                        current_period['resolved'] += 1
                
                elif previous_start <= complaint_date <= previous_end:
                    previous_period['count'] += 1
                    if complaint.status == 'resolved':
                        previous_period['resolved'] += 1
        
        # Calculate growth rates
        count_growth = 0
        if previous_period['count'] > 0:
            count_growth = round(((current_period['count'] - previous_period['count']) / previous_period['count'] * 100), 2)
        
        resolution_growth = 0
        if previous_period['resolved'] > 0:
            resolution_growth = round(((current_period['resolved'] - previous_period['resolved']) / previous_period['resolved'] * 100), 2)
        
        return jsonify({
            'success': True,
            'data': {
                'current_period': {
                    'start': current_start.isoformat(),
                    'end': current_end.isoformat(),
                    'total_complaints': current_period['count'],
                    'resolved': current_period['resolved'],
                    'resolution_rate': round((current_period['resolved'] / current_period['count'] * 100) if current_period['count'] > 0 else 0, 2)
                },
                'previous_period': {
                    'start': previous_start.isoformat(),
                    'end': previous_end.isoformat(),
                    'total_complaints': previous_period['count'],
                    'resolved': previous_period['resolved'],
                    'resolution_rate': round((previous_period['resolved'] / previous_period['count'] * 100) if previous_period['count'] > 0 else 0, 2)
                },
                'growth_metrics': {
                    'complaint_growth_percentage': count_growth,
                    'resolution_growth_percentage': resolution_growth,
                    'trend': 'increasing' if count_growth > 0 else 'decreasing' if count_growth < 0 else 'stable'
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error comparing periods',
            'error': str(e)
        }), 500

@trends_bp.route('/dashboard', methods=['GET'])
@token_required
def analytics_dashboard():
    """
    Comprehensive analytics dashboard
    All key metrics in one endpoint
    """
    try:
        days = request.args.get('days', default=30, type=int)
        start_date, end_date = get_date_range(days)
        
        all_complaints = Complaint.query.all()
        period_complaints = [c for c in all_complaints if c.created_at and (start_date <= c.created_at.date() <= end_date)]
        
        # Calculate metrics
        total = len(period_complaints)
        resolved = len([c for c in period_complaints if c.status == 'resolved'])
        pending = len([c for c in period_complaints if c.status in ['pending', 'open']])
        escalated = len([c for c in period_complaints if hasattr(c, 'escalated') and c.escalated])
        
        # Category breakdown
        categories = {}
        for complaint in period_complaints:
            cat = complaint.category or 'Uncategorized'
            categories[cat] = categories.get(cat, 0) + 1
        
        return jsonify({
            'success': True,
            'data': {
                'period': {
                    'days': days,
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'metrics': {
                    'total_complaints': total,
                    'resolved': resolved,
                    'pending': pending,
                    'escalated': escalated,
                    'resolution_rate': round((resolved / total * 100) if total > 0 else 0, 2),
                    'escalation_rate': round((escalated / total * 100) if total > 0 else 0, 2)
                },
                'top_categories': sorted([(k, v) for k, v in categories.items()], key=lambda x: x[1], reverse=True)[:5]
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error generating dashboard',
            'error': str(e)
        }), 500
