"""
History routes for the Personal Tracker App
"""
from datetime import datetime, date
from flask import (
    Blueprint, request, session, current_app, jsonify, Response
)
from app.web.routes.auth import login_required

bp = Blueprint('history', __name__, url_prefix='/history')

@bp.route('/sessions', methods=['GET'])
@login_required
def get_user_history():
    """Get historical study sessions for a user."""
    user_id = session.get('user_id')
    history_service = current_app.config['HISTORY_SERVICE']
    
    # Get filter parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    status = request.args.get('status')
    
    # Parse dates
    start_date = None
    if start_date_str:
        try:
            start_date = date.fromisoformat(start_date_str)
        except ValueError:
            return jsonify({"error": "Invalid start date format"}), 400
            
    end_date = None
    if end_date_str:
        try:
            end_date = date.fromisoformat(end_date_str)
        except ValueError:
            return jsonify({"error": "Invalid end date format"}), 400
            
    # Get history
    try:
        sessions = history_service.get_user_history(
            user_id, start_date, end_date, status
        )
        
        return jsonify({
            "sessions": sessions
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/sessions/<session_id>', methods=['GET'])
@login_required
def get_session(session_id):
    """Get a specific study session."""
    user_id = session.get('user_id')
    history_service = current_app.config['HISTORY_SERVICE']
    
    # Get all sessions
    sessions = history_service.get_user_history(user_id)
    
    # Find the requested session
    session_data = None
    for s in sessions:
        if s.get('id') == session_id:
            session_data = s
            break
            
    if not session_data:
        return jsonify({"error": "Session not found"}), 404
        
    return jsonify(session_data)

@bp.route('/sessions', methods=['POST'])
@login_required
def record_session():
    """Record a completed study session."""
    user_id = session.get('user_id')
    history_service = current_app.config['HISTORY_SERVICE']
    
    # Get session data from request
    session_data = request.json
    
    # Ensure user_id is set
    session_data['user_id'] = user_id
    
    # Record session
    try:
        success = history_service.record_study_session(user_id, session_data)
        
        return jsonify({
            "success": success
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/sessions/<session_id>', methods=['PUT'])
@login_required
def update_session(session_id):
    """Update a study session."""
    user_id = session.get('user_id')
    history_service = current_app.config['HISTORY_SERVICE']
    
    # Get session data from request
    session_data = request.json
    
    # Ensure id and user_id are set
    session_data['id'] = session_id
    session_data['user_id'] = user_id
    
    # Update session
    try:
        success = history_service.record_study_session(user_id, session_data)
        
        return jsonify({
            "success": success
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    """Get statistics for study sessions."""
    user_id = session.get('user_id')
    history_service = current_app.config['HISTORY_SERVICE']
    
    # Get period from query parameters
    period = request.args.get('period', 'month')
    
    # Validate period
    if period not in ['week', 'month', 'year', 'all']:
        return jsonify({"error": "Invalid period"}), 400
        
    # Get statistics
    try:
        stats = history_service.get_statistics(user_id, period)
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/export', methods=['GET'])
@login_required
def export_history():
    """Export study session history."""
    user_id = session.get('user_id')
    history_service = current_app.config['HISTORY_SERVICE']
    
    # Get format from query parameters
    format = request.args.get('format', 'csv')
    
    # Validate format
    if format not in ['csv', 'json']:
        return jsonify({"error": "Invalid format"}), 400
        
    # Export history
    try:
        exported_data = history_service.export_history(user_id, format)
        
        if format == 'csv':
            return Response(
                exported_data,
                mimetype='text/csv',
                headers={
                    'Content-Disposition': 'attachment;filename=study_history.csv'
                }
            )
        else:  # json
            return Response(
                exported_data,
                mimetype='application/json',
                headers={
                    'Content-Disposition': 'attachment;filename=study_history.json'
                }
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/summary', methods=['GET'])
@login_required
def get_summary():
    """Get a summary of study history."""
    user_id = session.get('user_id')
    history_service = current_app.config['HISTORY_SERVICE']
    
    # Get statistics for different periods
    try:
        week_stats = history_service.get_statistics(user_id, 'week')
        month_stats = history_service.get_statistics(user_id, 'month')
        year_stats = history_service.get_statistics(user_id, 'year')
        all_stats = history_service.get_statistics(user_id, 'all')
        
        # Create summary
        summary = {
            "current_week": week_stats['period_stats'],
            "current_month": month_stats['period_stats'],
            "current_year": year_stats['period_stats'],
            "all_time": all_stats['overall_stats']
        }
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
