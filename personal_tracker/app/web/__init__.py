"""
Web interface for the Personal Tracker App
"""
import os
from flask import Flask, session
from app.config import get_config
from app.storage.json_storage import JsonStorage
from app.services.history_service import HistoryService
from app.models.user import UserPreferences
from app.core.scheduler import SchedulerService

def create_app(auth_service, calendar_service):
    """
    Create and configure the Flask application
    
    Args:
        auth_service (AuthenticationService): Authentication service instance
        calendar_service (CalendarService): Calendar service instance
        
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    
    # Load configuration
    config = get_config()
    app.config.from_object(config)
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
        
    # Initialize services
    json_storage = JsonStorage(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
    history_service = HistoryService(json_storage)
    scheduler_service = SchedulerService(calendar_service, json_storage)
    
    # Register services with app
    app.config['AUTH_SERVICE'] = auth_service
    app.config['CALENDAR_SERVICE'] = calendar_service
    app.config['HISTORY_SERVICE'] = history_service
    app.config['SCHEDULER_SERVICE'] = scheduler_service
    app.config['JSON_STORAGE'] = json_storage
    
    # Register blueprints
    from app.web.routes import auth, calendar, scheduler, history
    app.register_blueprint(auth.bp)
    app.register_blueprint(calendar.bp)
    app.register_blueprint(scheduler.bp)
    app.register_blueprint(history.bp)
    
    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return {"error": "Not found"}, 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        return {"error": "Internal server error"}, 500
        
    # Register before request handler
    @app.before_request
    def load_user_preferences():
        """Load user preferences before each request"""
        if 'user_id' in session:
            user_id = session['user_id']
            prefs_data = json_storage.load("preferences", user_id)
            
            if prefs_data:
                session['user_preferences'] = UserPreferences.from_dict(prefs_data)
                
    # Register index route
    @app.route('/')
    def index():
        return {
            "app": "Personal Tracker",
            "version": "1.0.0",
            "status": "running"
        }
        
    return app
