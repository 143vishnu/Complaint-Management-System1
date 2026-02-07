"""
Location-Based Complaints
Geolocation tracking, mapping, and location-based filtering
"""
from flask import Blueprint, request, jsonify
from models.complaint import Complaint
from models.user import db
from functools import wraps
import jwt
import os
from datetime import datetime
from math import radians, cos, sin, asin, sqrt

location_bp = Blueprint('locations', __name__, url_prefix='/api/locations')

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

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates in kilometers
    Using Haversine formula
    """
    try:
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Earth radius in km
        
        return c * r
    except:
        return None

@location_bp.route('/add/<int:complaint_id>', methods=['POST'])
@token_required
def add_location(complaint_id):
    """
    Add or update location data for a complaint
    Accepts coordinates, address, and location name
    """
    try:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({
                'success': False,
                'message': 'Complaint not found'
            }), 404
        
        data = request.json
        
        # Validate coordinates
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if latitude is None or longitude is None:
            return jsonify({
                'success': False,
                'message': 'Latitude and longitude are required'
            }), 400
        
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid coordinates'
            }), 400
        
        # Validate coordinate ranges
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return jsonify({
                'success': False,
                'message': 'Coordinates out of valid range'
            }), 400
        
        # Store location data
        complaint.location = {
            'latitude': latitude,
            'longitude': longitude,
            'address': data.get('address', ''),
            'city': data.get('city', ''),
            'state': data.get('state', ''),
            'country': data.get('country', ''),
            'postal_code': data.get('postal_code', ''),
            'location_name': data.get('location_name', 'Complaint Location'),
            'added_at': datetime.utcnow().isoformat(),
            'accuracy': data.get('accuracy')  # GPS accuracy in meters
        }
        
        db.session.add(complaint)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Location added successfully',
            'data': complaint.location
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error adding location',
            'error': str(e)
        }), 500

@location_bp.route('/get/<int:complaint_id>', methods=['GET'])
@token_required
def get_location(complaint_id):
    """
    Get location data for a complaint
    """
    try:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({
                'success': False,
                'message': 'Complaint not found'
            }), 404
        
        if not complaint.location:
            return jsonify({
                'success': False,
                'message': 'No location data for this complaint'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'complaint_id': complaint_id,
                'location': complaint.location
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error fetching location',
            'error': str(e)
        }), 500

@location_bp.route('/nearby', methods=['GET'])
@token_required
def get_nearby_complaints():
    """
    Find complaints near a given location
    Radius in kilometers
    """
    try:
        latitude = request.args.get('latitude', type=float)
        longitude = request.args.get('longitude', type=float)
        radius = request.args.get('radius', default=5, type=float)
        
        if latitude is None or longitude is None:
            return jsonify({
                'success': False,
                'message': 'Latitude and longitude are required'
            }), 400
        
        all_complaints = Complaint.query.all()
        nearby = []
        
        for complaint in all_complaints:
            if not complaint.location:
                continue
            
            distance = haversine_distance(
                latitude,
                longitude,
                complaint.location['latitude'],
                complaint.location['longitude']
            )
            
            if distance and distance <= radius:
                nearby.append({
                    'complaint_id': complaint.id,
                    'ticket_id': complaint.ticket_id,
                    'title': complaint.title,
                    'status': complaint.status,
                    'priority': complaint.priority,
                    'category': complaint.category,
                    'location': complaint.location,
                    'distance_km': round(distance, 2)
                })
        
        # Sort by distance
        nearby.sort(key=lambda x: x['distance_km'])
        
        return jsonify({
            'success': True,
            'data': {
                'center': {
                    'latitude': latitude,
                    'longitude': longitude
                },
                'radius_km': radius,
                'complaints': nearby,
                'total_count': len(nearby)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error finding nearby complaints',
            'error': str(e)
        }), 500

@location_bp.route('/by-city', methods=['GET'])
@token_required
def get_complaints_by_city():
    """
    Get all complaints for a specific city
    """
    try:
        city = request.args.get('city', '').lower()
        
        if not city:
            return jsonify({
                'success': False,
                'message': 'City parameter is required'
            }), 400
        
        all_complaints = Complaint.query.all()
        city_complaints = []
        
        for complaint in all_complaints:
            if complaint.location and complaint.location.get('city', '').lower() == city:
                city_complaints.append({
                    'complaint_id': complaint.id,
                    'ticket_id': complaint.ticket_id,
                    'title': complaint.title,
                    'status': complaint.status,
                    'category': complaint.category,
                    'location': complaint.location,
                    'created_at': complaint.created_at.isoformat() if complaint.created_at else None
                })
        
        return jsonify({
            'success': True,
            'data': {
                'city': city.title(),
                'complaints': city_complaints,
                'total_count': len(city_complaints)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error fetching city complaints',
            'error': str(e)
        }), 500

@location_bp.route('/heatmap-data', methods=['GET'])
@token_required
def get_heatmap_data():
    """
    Get complaint density data for heatmap visualization
    Returns coordinates and density information
    """
    try:
        category = request.args.get('category', '')
        status = request.args.get('status', '')
        
        all_complaints = Complaint.query.all()
        heatmap_points = []
        
        for complaint in all_complaints:
            # Filter by category if specified
            if category and complaint.category != category:
                continue
            
            # Filter by status if specified
            if status and complaint.status != status:
                continue
            
            if complaint.location:
                # Weight based on priority
                weight = {'high': 3, 'medium': 2, 'low': 1}.get(complaint.priority, 1)
                
                heatmap_points.append({
                    'latitude': complaint.location['latitude'],
                    'longitude': complaint.location['longitude'],
                    'weight': weight,
                    'complaint_id': complaint.id,
                    'title': complaint.title,
                    'status': complaint.status
                })
        
        return jsonify({
            'success': True,
            'data': {
                'points': heatmap_points,
                'total_points': len(heatmap_points),
                'filters': {
                    'category': category or 'all',
                    'status': status or 'all'
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error generating heatmap data',
            'error': str(e)
        }), 500

@location_bp.route('/bounds', methods=['GET'])
@token_required
def get_complaints_in_bounds():
    """
    Get complaints within map bounds
    Useful for map zoom/pan operations
    """
    try:
        north = request.args.get('north', type=float)
        south = request.args.get('south', type=float)
        east = request.args.get('east', type=float)
        west = request.args.get('west', type=float)
        
        if any(x is None for x in [north, south, east, west]):
            return jsonify({
                'success': False,
                'message': 'Bounds parameters (north, south, east, west) are required'
            }), 400
        
        all_complaints = Complaint.query.all()
        complaints_in_bounds = []
        
        for complaint in all_complaints:
            if not complaint.location:
                continue
            
            lat = complaint.location['latitude']
            lon = complaint.location['longitude']
            
            # Check if within bounds
            if south <= lat <= north and west <= lon <= east:
                complaints_in_bounds.append({
                    'complaint_id': complaint.id,
                    'ticket_id': complaint.ticket_id,
                    'title': complaint.title,
                    'status': complaint.status,
                    'priority': complaint.priority,
                    'latitude': lat,
                    'longitude': lon,
                    'address': complaint.location.get('address', '')
                })
        
        return jsonify({
            'success': True,
            'data': {
                'bounds': {
                    'north': north,
                    'south': south,
                    'east': east,
                    'west': west
                },
                'complaints': complaints_in_bounds,
                'total_count': len(complaints_in_bounds)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error fetching complaints in bounds',
            'error': str(e)
        }), 500

@location_bp.route('/statistics', methods=['GET'])
@token_required
def location_statistics():
    """
    Get statistics about complaint locations
    """
    try:
        all_complaints = Complaint.query.all()
        
        # Collect statistics
        cities = {}
        states = {}
        countries = {}
        total_with_location = 0
        
        for complaint in all_complaints:
            if complaint.location:
                total_with_location += 1
                
                city = complaint.location.get('city', 'Unknown')
                state = complaint.location.get('state', 'Unknown')
                country = complaint.location.get('country', 'Unknown')
                
                cities[city] = cities.get(city, 0) + 1
                states[state] = states.get(state, 0) + 1
                countries[country] = countries.get(country, 0) + 1
        
        return jsonify({
            'success': True,
            'data': {
                'total_complaints': len(all_complaints),
                'complaints_with_location': total_with_location,
                'top_cities': sorted(cities.items(), key=lambda x: x[1], reverse=True)[:10],
                'top_states': sorted(states.items(), key=lambda x: x[1], reverse=True)[:10],
                'top_countries': sorted(countries.items(), key=lambda x: x[1], reverse=True)[:5]
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error fetching location statistics',
            'error': str(e)
        }), 500
