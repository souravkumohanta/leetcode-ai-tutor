"""
Scheduler routes for the Personal Tracker App
"""
from datetime import datetime, timedelta, date
from flask import (
    Blueprint, request, session, current_app, jsonify
)
from app.web.routes.auth import login_required
from app.models.user import UserPreferences
from app.models.event import StudySession

bp = Blueprint('scheduler', __name__, url_prefix='/scheduler')

@bp.route('/free-slots', methods=['GET'])
@login_required
def get_free_slots():
    """Get free time slots for a specific date."""
    user_id = session.get('user_id')
    scheduler_service = current_app.config['SCHEDULER_SERVICE']
    json_storage = current_app.config['JSON_STORAGE']
    
    # Get date from query parameters
    target_date_str = request.args.get('date')
    min_duration = request.args.get('min_duration')
    
    # Parse date
    try:
        if target_date_str:
            target_date = date.fromisoformat(target_date_str)
        else:
            target_date = date.today()
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400
        
    # Parse min_duration
    if min_duration:
        try:
            min_duration = int(min_duration)
        except ValueError:
            return jsonify({"error": "Invalid min_duration format"}), 400
    else:
        min_duration = None
        
    # Get user preferences
    prefs_data = json_storage.load("preferences", user_id)
    if not prefs_data:
        return jsonify({"error": "User preferences not found"}), 404
        
    user_preferences = UserPreferences.from_dict(prefs_data)
    
    # Get free slots
    try:
        free_slots = scheduler_service.compute_free_slots(
            user_id, user_preferences, target_date, min_duration
        )
        
        # Convert to serializable format
        serializable_slots = []
        for start, end in free_slots:
            serializable_slots.append({
                "start": start.isoformat(),
                "end": end.isoformat(),
                "duration": int((end - start).total_seconds() / 60)
            })
            
        return jsonify({
            "date": target_date.isoformat(),
            "free_slots": serializable_slots
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/propose', methods=['GET'])
@login_required
def propose_study_sessions():
    """Generate study session proposals for a date range."""
    user_id = session.get('user_id')
    scheduler_service = current_app.config['SCHEDULER_SERVICE']
    json_storage = current_app.config['JSON_STORAGE']
    
    # Get date range from query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    daily_target = request.args.get('daily_target')
    
    # Parse dates
    try:
        if start_date_str:
            start_date = date.fromisoformat(start_date_str)
        else:
            start_date = date.today()
            
        if end_date_str:
            end_date = date.fromisoformat(end_date_str)
        else:
            end_date = start_date + timedelta(days=7)
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400
        
    # Parse daily_target
    if daily_target:
        try:
            daily_target = int(daily_target)
        except ValueError:
            return jsonify({"error": "Invalid daily_target format"}), 400
    else:
        daily_target = None
        
    # Get user preferences
    prefs_data = json_storage.load("preferences", user_id)
    if not prefs_data:
        return jsonify({"error": "User preferences not found"}), 404
        
    user_preferences = UserPreferences.from_dict(prefs_data)
    
    # Generate proposals
    try:
        proposals = scheduler_service.propose_study_sessions(
            user_id, user_preferences, start_date, end_date, daily_target
        )
        
        # Convert to serializable format
        serializable_proposals = {}
        for date_key, sessions in proposals.items():
            serializable_sessions = []
            for session in sessions:
                serializable_sessions.append(session.to_dict())
                
            serializable_proposals[date_key.isoformat()] = serializable_sessions
            
        return jsonify({
            "proposals": serializable_proposals
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/schedule', methods=['POST'])
@login_required
def schedule_sessions():
    """Schedule approved study sessions."""
    user_id = session.get('user_id')
    scheduler_service = current_app.config['SCHEDULER_SERVICE']
    
    # Get sessions from request
    data = request.json
    sessions_data = data.get('sessions', [])
    provider_type = data.get('provider')
    
    # Convert to StudySession objects
    approved_sessions = []
    for session_data in sessions_data:
        session = StudySession.from_dict(session_data)
        approved_sessions.append(session)
        
    # Schedule sessions
    try:
        created_sessions = scheduler_service.schedule_approved_sessions(
            user_id, approved_sessions, provider_type
        )
        
        # Convert to serializable format
        serializable_sessions = []
        for session in created_sessions:
            serializable_sessions.append(session.to_dict())
            
        return jsonify({
            "scheduled_sessions": serializable_sessions
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/conflicts', methods=['POST'])
@login_required
def handle_conflicts():
    """Detect and resolve conflicts with existing study sessions."""
    user_id = session.get('user_id')
    scheduler_service = current_app.config['SCHEDULER_SERVICE']
    json_storage = current_app.config['JSON_STORAGE']
    
    # Get user preferences
    prefs_data = json_storage.load("preferences", user_id)
    if not prefs_data:
        return jsonify({"error": "User preferences not found"}), 404
        
    user_preferences = UserPreferences.from_dict(prefs_data)
    
    # Handle conflicts
    try:
        rescheduled_sessions, cancelled_sessions = scheduler_service.handle_conflicts(
            user_id, user_preferences
        )
        
        # Convert to serializable format
        serializable_rescheduled = []
        for session in rescheduled_sessions:
            serializable_rescheduled.append(session.to_dict())
            
        serializable_cancelled = []
        for session in cancelled_sessions:
            serializable_cancelled.append(session.to_dict())
            
        return jsonify({
            "rescheduled_sessions": serializable_rescheduled,
            "cancelled_sessions": serializable_cancelled
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/tracked-events', methods=['GET'])
@login_required
def get_tracked_events():
    """Get tracked study events for a user."""
    user_id = session.get('user_id')
    scheduler_service = current_app.config['SCHEDULER_SERVICE']
    
    try:
        events = scheduler_service.get_tracked_events(user_id)
        
        return jsonify({
            "events": events
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/track-event', methods=['POST'])
@login_required
def track_event():
    """Track a study event."""
    user_id = session.get('user_id')
    scheduler_service = current_app.config['SCHEDULER_SERVICE']
    
    # Get event data from request
    event_data = request.json
    
    try:
        scheduler_service.track_event(user_id, event_data)
        
        return jsonify({
            "success": True
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
