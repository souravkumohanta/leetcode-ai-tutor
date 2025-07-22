"""
Secure token storage implementation for the Personal Tracker App
"""
import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from datetime import datetime

class SecureJsonTokenStorage:
    """
    Secure storage for OAuth tokens using JSON files and encryption
    
    This class provides methods to securely store and retrieve OAuth tokens
    using Fernet symmetric encryption.
    """
    
    def __init__(self, json_storage, encryption_key=None):
        """
        Initialize the secure token storage
        
        Args:
            json_storage (JsonStorage): JSON storage instance
            encryption_key (bytes, optional): Encryption key or None to generate one
        """
        self.json_storage = json_storage
        self.encryption_key = encryption_key or self._generate_key()
        self.fernet = Fernet(self.encryption_key)
        
    def store_token(self, provider_type, user_id, token_data):
        """
        Encrypt and store OAuth tokens
        
        Args:
            provider_type (str): Calendar provider type (google, outlook)
            user_id (str): User identifier
            token_data (dict): Token data to encrypt and store
            
        Returns:
            bool: True if successful
        """
        # Convert token data to JSON string
        token_json = json.dumps(token_data)
        
        # Encrypt the token data
        encrypted_data = self.fernet.encrypt(token_json.encode('utf-8'))
        
        # Create storage object
        storage_data = {
            "provider": provider_type,
            "user_id": user_id,
            "encrypted_data": encrypted_data.decode('utf-8'),
            "last_refreshed": datetime.utcnow().isoformat()
        }
        
        # Save to JSON storage
        return self.json_storage.save("tokens", user_id, storage_data, provider_type)
        
    def retrieve_token(self, provider_type, user_id):
        """
        Retrieve and decrypt OAuth tokens
        
        Args:
            provider_type (str): Calendar provider type (google, outlook)
            user_id (str): User identifier
            
        Returns:
            dict: Decrypted token data or None if not found
        """
        # Load from JSON storage
        storage_data = self.json_storage.load("tokens", user_id, provider_type)
        
        if not storage_data or "encrypted_data" not in storage_data:
            return None
            
        try:
            # Decrypt the token data
            encrypted_data = storage_data["encrypted_data"].encode('utf-8')
            decrypted_data = self.fernet.decrypt(encrypted_data)
            
            # Parse JSON
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception as e:
            # Log error but don't expose details
            print(f"Error decrypting token: {type(e).__name__}")
            return None
    
    def delete_token(self, provider_type, user_id):
        """
        Delete a stored token
        
        Args:
            provider_type (str): Calendar provider type (google, outlook)
            user_id (str): User identifier
            
        Returns:
            bool: True if successful, False if token doesn't exist
        """
        return self.json_storage.delete("tokens", user_id, provider_type)
    
    def list_providers(self, user_id):
        """
        List all providers for which a user has tokens
        
        Args:
            user_id (str): User identifier
            
        Returns:
            list: List of provider types
        """
        # This is a simplified implementation
        # In a real app, you would scan the tokens directory for matching files
        providers = []
        for provider in ["google", "outlook"]:
            if self.json_storage.load("tokens", user_id, provider) is not None:
                providers.append(provider)
        return providers
        
    def _generate_key(self):
        """
        Generate a secure encryption key
        
        Returns:
            bytes: Fernet encryption key
        """
        # Use environment variable if available
        env_key = os.environ.get('TOKEN_ENCRYPTION_KEY')
        if env_key:
            try:
                # Try to decode the key from base64
                return base64.urlsafe_b64decode(env_key)
            except Exception:
                # If decoding fails, use it to derive a key
                pass
        
        # Generate a key using PBKDF2
        salt = os.environ.get('TOKEN_ENCRYPTION_SALT', 'personal-tracker-salt').encode()
        password = env_key or os.environ.get('SECRET_KEY', 'default-key-please-change')
        
        if not isinstance(password, bytes):
            password = password.encode('utf-8')
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
