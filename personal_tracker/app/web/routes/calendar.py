"""
Calendar routes for the Personal Tracker App
"""
from datetime import datetime, timedelta
from flask import (
    Blueprint, request, session, current_app, jsonify
)
from app.web.routes.auth import login_required

bp = Blueprint('calendar', __name__, url_prefix='/calendar')

@bp.route('/providers')
@login_required
def list_providers():
    """List connected calendar providers."""
    user_id = session.get('user_id')
    auth_service = current_app.config['AUTH_SERVICE']
    
    providers = auth_service.list_connected_providers(user_id)
    
    return jsonify({
        "providers": providers
    })

@bp.route('/busy', methods=['GET'])
@login_required
def get_busy_intervals():
    """Get busy intervals for a date range."""
    user_id = session.get('user_id')
    calendar_service = current_app.config['CALENDAR_SERVICE']
    
    # Get date range from query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    provider_types = request.args.getlist('provider')
    
    # Parse dates
    try:
        start_date = datetime.fromisoformat(start_date_str) if start_date_str else datetime.now()
        end_date = datetime.fromisoformat(end_date_str) if end_date_str else (start_date + timedelta(days=7))
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400
        
    # Get busy intervals
    try:
        busy_intervals, errors = calendar_service.get_busy_intervals(
            user_id, start_date, end_date, provider_types
        )
        
        return jsonify({
            "busy_intervals": busy_intervals,
            "errors": errors
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/events', methods=['GET'])
@login_required
def list_events():
    """List calendar events for a date range."""
    user_id = session.get('user_id')
    calendar_service = current_app.config['CALENDAR_SERVICE']
    
    # Get date range from query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    provider_types = request.args.getlist('provider')
    
    # Parse dates
    try:
        start_date = datetime.fromisoformat(start_date_str) if start_date_str else datetime.now()
        end_date = datetime.fromisoformat(end_date_str) if end_date_str else (start_date + timedelta(days=7))
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400
        
    # Get events
    try:
        events, errors = calendar_service.list_events(
            user_id, start_date, end_date, provider_types
        )
        
        return jsonify({
            "events": events,
            "errors": errors
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/events/<provider>/<event_id>', methods=['GET'])
@login_required
def get_event(provider, event_id):
    """Get a specific calendar event."""
    user_id = session.get('user_id')
    calendar_service = current_app.config['CALENDAR_SERVICE']
    
    try:
        event = calendar_service.get_event(user_id, event_id, provider)
        
        return jsonify(event)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/events', methods=['POST'])
@login_required
def create_event():
    """Create a new calendar event."""
    user_id = session.get('user_id')
    calendar_service = current_app.config['CALENDAR_SERVICE']
    
    # Get event data from request
    data = request.json
    
    # Parse dates
    try:
        start_time = datetime.fromisoformat(data.get('start_time'))
        end_time = datetime.fromisoformat(data.get('end_time'))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid date format"}), 400
        
    # Create event
    try:
        event_id, provider = calendar_service.create_event(
            user_id=user_id,
            title=data.get('title'),
            start_time=start_time,
            end_time=end_time,
            description=data.get('description'),
            provider_type=data.get('provider')
        )
        
        return jsonify({
            "event_id": event_id,
            "provider": provider
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/events/<provider>/<event_id>', methods=['PUT'])
@login_required
def update_event(provider, event_id):
    """Update a calendar event."""
    user_id = session.get('user_id')
    calendar_service = current_app.config['CALENDAR_SERVICE']
    
    # Get event data from request
    data = request.json
    
    # Parse dates
    start_time = None
    if data.get('start_time'):
        try:
            start_time = datetime.fromisoformat(data.get('start_time'))
        except ValueError:
            return jsonify({"error": "Invalid start date format"}), 400
            
    end_time = None
    if data.get('end_time'):
        try:
            end_time = datetime.fromisoformat(data.get('end_time'))
        except ValueError:
            return jsonify({"error": "Invalid end date format"}), 400
            
    # Update event
    try:
        updated_event_id = calendar_service.update_event(
            user_id=user_id,
            event_id=event_id,
            provider_type=provider,
            start_time=start_time,
            end_time=end_time,
            title=data.get('title'),
            description=data.get('description')
        )
        
        return jsonify({
            "event_id": updated_event_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/events/<provider>/<event_id>', methods=['DELETE'])
@login_required
def delete_event(provider, event_id):
    """Delete a calendar event."""
    user_id = session.get('user_id')
    calendar_service = current_app.config['CALENDAR_SERVICE']
    
    try:
        success = calendar_service.delete_event(
            user_id=user_id,
            event_id=event_id,
            provider_type=provider
        )
        
        return jsonify({
            "success": success
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/study-sessions', methods=['GET'])
@login_required
def list_study_sessions():
    """List study sessions for a date range."""
    user_id = session.get('user_id')
    calendar_service = current_app.config['CALENDAR_SERVICE']
    
    # Get date range from query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    provider_types = request.args.getlist('provider')
    
    # Parse dates
    try:
        start_date = datetime.fromisoformat(start_date_str) if start_date_str else datetime.now()
        end_date = datetime.fromisoformat(end_date_str) if end_date_str else (start_date + timedelta(days=7))
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400
        
    # Get study sessions
    try:
        study_sessions, errors = calendar_service.list_study_sessions(
            user_id, start_date, end_date, provider_types
        )
        
        return jsonify({
            "study_sessions": study_sessions,
            "errors": errors
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
