"""
Authentication routes for the Personal Tracker App
"""
import functools
import uuid
from flask import (
    Blueprint, flash, g, redirect, render_template, request,
    session, url_for, current_app, jsonify
)

bp = Blueprint('auth', __name__, url_prefix='/auth')

def login_required(view):
    """View decorator that redirects anonymous users to the login page."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return view(**kwargs)
    return wrapped_view

@bp.route('/login', methods=['POST'])
def login():
    """Log in a user."""
    if request.method == 'POST':
        username = request.json.get('username')
        
        error = None
        if not username:
            error = 'Username is required.'
            
        if error is None:
            # Simple user management - just use the username as the user ID
            # In a real app, you would authenticate against a database
            user_id = username
            session.clear()
            session['user_id'] = user_id
            return jsonify({"success": True, "user_id": user_id})
            
        return jsonify({"error": error}), 400
        
    return jsonify({"error": "Method not allowed"}), 405

@bp.route('/logout')
def logout():
    """Log out the current user."""
    session.clear()
    return jsonify({"success": True})

@bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    if request.method == 'POST':
        username = request.json.get('username')
        
        error = None
        if not username:
            error = 'Username is required.'
            
        if error is None:
            # Simple user management - just use the username as the user ID
            # In a real app, you would store the user in a database
            user_id = username
            
            # Create user preferences
            json_storage = current_app.config['JSON_STORAGE']
            
            # Check if user already exists
            if json_storage.load("preferences", user_id):
                error = f"User {username} is already registered."
            else:
                # Create default preferences
                from app.models.user import UserPreferences
                prefs = UserPreferences(user_id=user_id)
                json_storage.save("preferences", user_id, prefs.to_dict())
                
                # Log in the user
                session.clear()
                session['user_id'] = user_id
                return jsonify({"success": True, "user_id": user_id})
                
        return jsonify({"error": error}), 400
        
    return jsonify({"error": "Method not allowed"}), 405

@bp.route('/user')
@login_required
def get_user():
    """Get the current user."""
    user_id = session.get('user_id')
    
    # Get user preferences
    json_storage = current_app.config['JSON_STORAGE']
    prefs_data = json_storage.load("preferences", user_id)
    
    # Get connected providers
    auth_service = current_app.config['AUTH_SERVICE']
    providers = auth_service.list_connected_providers(user_id)
    
    return jsonify({
        "user_id": user_id,
        "preferences": prefs_data,
        "connected_providers": providers
    })

@bp.route('/preferences', methods=['GET', 'PUT'])
@login_required
def preferences():
    """Get or update user preferences."""
    user_id = session.get('user_id')
    json_storage = current_app.config['JSON_STORAGE']
    
    if request.method == 'GET':
        prefs_data = json_storage.load("preferences", user_id)
        return jsonify(prefs_data)
        
    elif request.method == 'PUT':
        # Update preferences
        prefs_data = request.json
        
        # Ensure user_id is set
        prefs_data['user_id'] = user_id
        
        # Save preferences
        json_storage.save("preferences", user_id, prefs_data)
        
        # Update session
        from app.models.user import UserPreferences
        session['user_preferences'] = UserPreferences.from_dict(prefs_data)
        
        return jsonify({"success": True})
        
    return jsonify({"error": "Method not allowed"}), 405

@bp.route('/connect/<provider>')
@login_required
def connect_provider(provider):
    """Connect to a calendar provider."""
    if provider not in ['google', 'outlook']:
        return jsonify({"error": "Invalid provider"}), 400
        
    user_id = session.get('user_id')
    auth_service = current_app.config['AUTH_SERVICE']
    
    # Generate redirect URI
    redirect_uri = url_for('auth.oauth_callback', provider=provider, _external=True)
    
    # Get authorization URL
    try:
        auth_url, state = auth_service.get_auth_url(provider, redirect_uri)
        
        # Store state in session
        session[f'{provider}_oauth_state'] = state
        
        return jsonify({
            "auth_url": auth_url
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/callback/<provider>')
@login_required
def oauth_callback(provider):
    """Handle OAuth callback."""
    if provider not in ['google', 'outlook']:
        return jsonify({"error": "Invalid provider"}), 400
        
    user_id = session.get('user_id')
    auth_service = current_app.config['AUTH_SERVICE']
    
    # Get authorization code from request
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code:
        return jsonify({"error": "No authorization code provided"}), 400
        
    # Check state if available
    if provider == 'google' and state != session.get(f'{provider}_oauth_state'):
        return jsonify({"error": "Invalid state parameter"}), 400
        
    # Generate redirect URI
    redirect_uri = url_for('auth.oauth_callback', provider=provider, _external=True)
    
    try:
        # Handle callback and get tokens
        token_data = auth_service.handle_callback(provider, redirect_uri, code, state)
        
        # Store tokens
        auth_service.store_tokens(provider, user_id, token_data)
        
        return jsonify({"success": True, "provider": provider})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/disconnect/<provider>')
@login_required
def disconnect_provider(provider):
    """Disconnect from a calendar provider."""
    if provider not in ['google', 'outlook']:
        return jsonify({"error": "Invalid provider"}), 400
        
    user_id = session.get('user_id')
    auth_service = current_app.config['AUTH_SERVICE']
    
    try:
        # Revoke token
        auth_service.revoke_token(provider, user_id)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
