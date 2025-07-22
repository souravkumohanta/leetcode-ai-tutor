"""
Authentication service for the Personal Tracker App
"""
import os
import json
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode
from google_auth_oauthlib.flow import Flow as GoogleFlow
from google.oauth2.credentials import Credentials as GoogleCredentials
from google.auth.transport.requests import Request as GoogleRequest
from app.config import get_config

class AuthenticationService:
    """
    Authentication service for handling OAuth flows and token management
    
    This class provides methods to authenticate with calendar providers,
    manage OAuth tokens, and handle token refresh.
    """
    
    def __init__(self, token_storage):
        """
        Initialize the authentication service
        
        Args:
            token_storage (SecureJsonTokenStorage): Token storage instance
        """
        self.token_storage = token_storage
        self.config = get_config()
        
    def get_auth_url(self, provider_type, redirect_uri):
        """
        Get the authorization URL for a provider
        
        Args:
            provider_type (str): Calendar provider type (google, outlook)
            redirect_uri (str): Redirect URI for OAuth callback
            
        Returns:
            tuple: (auth_url, state) where state is provider-specific state data
        """
        if provider_type == "google":
            return self._get_google_auth_url(redirect_uri)
        elif provider_type == "outlook":
            return self._get_outlook_auth_url(redirect_uri)
        else:
            raise ValueError(f"Unsupported provider: {provider_type}")
    
    def handle_callback(self, provider_type, redirect_uri, code, state=None):
        """
        Handle OAuth callback and get tokens
        
        Args:
            provider_type (str): Calendar provider type (google, outlook)
            redirect_uri (str): Redirect URI for OAuth callback
            code (str): Authorization code from callback
            state (str, optional): State from callback
            
        Returns:
            dict: Token data
        """
        if provider_type == "google":
            return self._handle_google_callback(redirect_uri, code, state)
        elif provider_type == "outlook":
            return self._handle_outlook_callback(redirect_uri, code)
        else:
            raise ValueError(f"Unsupported provider: {provider_type}")
    
    def store_tokens(self, provider_type, user_id, token_data):
        """
        Store tokens for a provider
        
        Args:
            provider_type (str): Calendar provider type (google, outlook)
            user_id (str): User identifier
            token_data (dict): Token data to store
            
        Returns:
            bool: True if successful
        """
        return self.token_storage.store_token(provider_type, user_id, token_data)
    
    def get_valid_token(self, provider_type, user_id):
        """
        Get a valid token, refreshing if necessary
        
        Args:
            provider_type (str): Calendar provider type (google, outlook)
            user_id (str): User identifier
            
        Returns:
            dict: Valid token data or None if not available
            
        Raises:
            Exception: If token refresh fails
        """
        token_data = self.token_storage.retrieve_token(provider_type, user_id)
        
        if not token_data:
            return None
            
        # Check if token is expired
        if self._is_token_expired(provider_type, token_data):
            token_data = self._refresh_token(provider_type, user_id, token_data)
            
        return token_data
    
    def revoke_token(self, provider_type, user_id):
        """
        Revoke a token and remove it from storage
        
        Args:
            provider_type (str): Calendar provider type (google, outlook)
            user_id (str): User identifier
            
        Returns:
            bool: True if successful
        """
        token_data = self.token_storage.retrieve_token(provider_type, user_id)
        
        if not token_data:
            return True  # Already gone
            
        # Attempt to revoke with provider
        if provider_type == "google":
            self._revoke_google_token(token_data)
        elif provider_type == "outlook":
            self._revoke_outlook_token(token_data)
            
        # Delete from storage regardless of revoke success
        return self.token_storage.delete_token(provider_type, user_id)
    
    def list_connected_providers(self, user_id):
        """
        List all providers a user has connected
        
        Args:
            user_id (str): User identifier
            
        Returns:
            list: List of connected provider types
        """
        return self.token_storage.list_providers(user_id)
    
    def _get_google_auth_url(self, redirect_uri):
        """
        Get Google OAuth authorization URL
        
        Args:
            redirect_uri (str): Redirect URI for OAuth callback
            
        Returns:
            tuple: (auth_url, flow) where flow is the Google OAuth flow
        """
        client_config = {
            "web": {
                "client_id": self.config.GOOGLE_CLIENT_ID,
                "client_secret": self.config.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        }
        
        flow = GoogleFlow.from_client_config(
            client_config,
            scopes=['https://www.googleapis.com/auth/calendar'],
            redirect_uri=redirect_uri
        )
        
        # Generate authorization URL
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force to get refresh token
        )
        
        return auth_url, flow
    
    def _get_outlook_auth_url(self, redirect_uri):
        """
        Get Microsoft OAuth authorization URL
        
        Args:
            redirect_uri (str): Redirect URI for OAuth callback
            
        Returns:
            tuple: (auth_url, None)
        """
        params = {
            'client_id': self.config.MICROSOFT_CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': 'offline_access Calendars.ReadWrite',
            'response_mode': 'query'
        }
        
        auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{urlencode(params)}"
        return auth_url, None
    
    def _handle_google_callback(self, redirect_uri, code, state):
        """
        Handle Google OAuth callback
        
        Args:
            redirect_uri (str): Redirect URI for OAuth callback
            code (str): Authorization code from callback
            state (str): State from callback
            
        Returns:
            dict: Token data
        """
        client_config = {
            "web": {
                "client_id": self.config.GOOGLE_CLIENT_ID,
                "client_secret": self.config.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        }
        
        flow = GoogleFlow.from_client_config(
            client_config,
            scopes=['https://www.googleapis.com/auth/calendar'],
            redirect_uri=redirect_uri,
            state=state
        )
        
        # Exchange authorization code for tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Extract token data to store
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
        
        return token_data
    
    def _handle_outlook_callback(self, redirect_uri, code):
        """
        Handle Microsoft OAuth callback
        
        Args:
            redirect_uri (str): Redirect URI for OAuth callback
            code (str): Authorization code from callback
            
        Returns:
            dict: Token data
        """
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        
        # Exchange authorization code for tokens
        data = {
            'client_id': self.config.MICROSOFT_CLIENT_ID,
            'client_secret': self.config.MICROSOFT_CLIENT_SECRET,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        
        tokens = response.json()
        
        # Add expiry timestamp
        if 'expires_in' in tokens:
            expires_in = tokens['expires_in']
            tokens['expires_at'] = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
            
        return tokens
    
    def _is_token_expired(self, provider_type, token_data):
        """
        Check if a token is expired
        
        Args:
            provider_type (str): Calendar provider type (google, outlook)
            token_data (dict): Token data
            
        Returns:
            bool: True if token is expired
        """
        if provider_type == "google":
            # Google tokens include an expiry timestamp
            if 'expiry' in token_data:
                expiry = datetime.fromisoformat(token_data['expiry'])
                # Add a buffer to refresh before actual expiry
                buffer = timedelta(minutes=5)
                return datetime.utcnow() >= (expiry - buffer)
            return True
        else:
            # Microsoft tokens include expires_in seconds
            if 'expires_at' in token_data:
                expiry = datetime.fromisoformat(token_data['expires_at'])
                # Add a buffer to refresh before actual expiry
                buffer = timedelta(minutes=5)
                return datetime.utcnow() >= (expiry - buffer)
            return True
    
    def _refresh_token(self, provider_type, user_id, token_data):
        """
        Refresh an expired token
        
        Args:
            provider_type (str): Calendar provider type (google, outlook)
            user_id (str): User identifier
            token_data (dict): Current token data
            
        Returns:
            dict: Refreshed token data
            
        Raises:
            Exception: If token refresh fails
        """
        if provider_type == "google":
            new_token_data = self._refresh_google_token(token_data)
        else:
            new_token_data = self._refresh_outlook_token(token_data)
            
        # Store the refreshed token
        self.token_storage.store_token(provider_type, user_id, new_token_data)
        return new_token_data
    
    def _refresh_google_token(self, token_data):
        """
        Refresh Google OAuth token
        
        Args:
            token_data (dict): Current token data
            
        Returns:
            dict: Refreshed token data
            
        Raises:
            Exception: If token refresh fails
        """
        credentials = GoogleCredentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=token_data.get('client_id', self.config.GOOGLE_CLIENT_ID),
            client_secret=token_data.get('client_secret', self.config.GOOGLE_CLIENT_SECRET),
            scopes=token_data.get('scopes', ['https://www.googleapis.com/auth/calendar'])
        )
        
        # Refresh the credentials
        request = GoogleRequest()
        credentials.refresh(request)
        
        # Update token data
        token_data['token'] = credentials.token
        token_data['expiry'] = credentials.expiry.isoformat() if credentials.expiry else None
        
        # Only update refresh_token if we got a new one
        if credentials.refresh_token:
            token_data['refresh_token'] = credentials.refresh_token
            
        return token_data
    
    def _refresh_outlook_token(self, token_data):
        """
        Refresh Microsoft OAuth token
        
        Args:
            token_data (dict): Current token data
            
        Returns:
            dict: Refreshed token data
            
        Raises:
            Exception: If token refresh fails
        """
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        
        refresh_data = {
            'client_id': self.config.MICROSOFT_CLIENT_ID,
            'client_secret': self.config.MICROSOFT_CLIENT_SECRET,
            'refresh_token': token_data.get('refresh_token'),
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(token_url, data=refresh_data)
        response.raise_for_status()
        
        new_tokens = response.json()
        
        # Update token data
        token_data['access_token'] = new_tokens['access_token']
        
        # Only update refresh_token if we got a new one
        if 'refresh_token' in new_tokens:
            token_data['refresh_token'] = new_tokens['refresh_token']
            
        # Calculate expiration time
        if 'expires_in' in new_tokens:
            expires_in = new_tokens['expires_in']
            token_data['expires_at'] = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
            
        return token_data
    
    def _revoke_google_token(self, token_data):
        """
        Revoke Google OAuth token
        
        Args:
            token_data (dict): Token data
            
        Returns:
            bool: True if successful
        """
        revoke_url = "https://oauth2.googleapis.com/revoke"
        
        # Try to revoke access token
        if 'token' in token_data:
            params = {'token': token_data['token']}
            try:
                requests.post(revoke_url, params=params)
            except Exception:
                pass
                
        # Try to revoke refresh token
        if 'refresh_token' in token_data:
            params = {'token': token_data['refresh_token']}
            try:
                requests.post(revoke_url, params=params)
            except Exception:
                pass
                
        return True
    
    def _revoke_outlook_token(self, token_data):
        """
        Revoke Microsoft OAuth token
        
        Args:
            token_data (dict): Token data
            
        Returns:
            bool: True if successful
        """
        # Microsoft doesn't have a standard revoke endpoint
        # The tokens will eventually expire
        return True
