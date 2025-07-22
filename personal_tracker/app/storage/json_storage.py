"""
JSON-based storage implementation for the Personal Tracker App
"""
import os
import json
import time
import fcntl
from datetime import datetime

class JsonStorage:
    """
    JSON file-based storage implementation
    
    This class provides methods to save and load data from JSON files,
    with proper file locking to handle concurrent access.
    """
    
    def __init__(self, base_path="./data"):
        """
        Initialize the JSON storage
        
        Args:
            base_path (str): Base directory for storing JSON files
        """
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Create necessary subdirectories"""
        for dir_name in ["tokens", "history", "preferences", "events"]:
            os.makedirs(os.path.join(self.base_path, dir_name), exist_ok=True)
    
    def _get_file_path(self, storage_type, user_id, provider=None):
        """
        Generate file path based on storage type and identifiers
        
        Args:
            storage_type (str): Type of storage (tokens, history, etc.)
            user_id (str): User identifier
            provider (str, optional): Provider name for token storage
            
        Returns:
            str: Path to the JSON file
        """
        if provider:
            return os.path.join(self.base_path, storage_type, f"{user_id}_{provider}.json")
        return os.path.join(self.base_path, storage_type, f"{user_id}_{storage_type}.json")
    
    def save(self, storage_type, user_id, data, provider=None):
        """
        Save data to JSON file with file locking
        
        Args:
            storage_type (str): Type of storage (tokens, history, etc.)
            user_id (str): User identifier
            data (dict): Data to save
            provider (str, optional): Provider name for token storage
            
        Returns:
            bool: True if successful
        """
        file_path = self._get_file_path(storage_type, user_id, provider)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Add timestamp for tracking
        if isinstance(data, dict):
            data['_last_updated'] = datetime.utcnow().isoformat()
        
        # Use file locking to handle concurrent access
        with open(file_path, 'w') as f:
            # Get an exclusive lock
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                json.dump(data, f, indent=2)
            finally:
                # Release the lock
                fcntl.flock(f, fcntl.LOCK_UN)
        
        return True
    
    def load(self, storage_type, user_id, provider=None):
        """
        Load data from JSON file with file locking
        
        Args:
            storage_type (str): Type of storage (tokens, history, etc.)
            user_id (str): User identifier
            provider (str, optional): Provider name for token storage
            
        Returns:
            dict: Loaded data or None if file doesn't exist
        """
        file_path = self._get_file_path(storage_type, user_id, provider)
        
        try:
            with open(file_path, 'r') as f:
                # Get a shared lock (allows other readers but not writers)
                fcntl.flock(f, fcntl.LOCK_SH)
                try:
                    return json.load(f)
                finally:
                    # Release the lock
                    fcntl.flock(f, fcntl.LOCK_UN)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            # Handle corrupted JSON files
            # Backup the corrupted file and return None
            backup_path = f"{file_path}.corrupted.{int(time.time())}"
            os.rename(file_path, backup_path)
            return None
    
    def delete(self, storage_type, user_id, provider=None):
        """
        Delete a JSON file
        
        Args:
            storage_type (str): Type of storage (tokens, history, etc.)
            user_id (str): User identifier
            provider (str, optional): Provider name for token storage
            
        Returns:
            bool: True if successful, False if file doesn't exist
        """
        file_path = self._get_file_path(storage_type, user_id, provider)
        
        try:
            os.remove(file_path)
            return True
        except FileNotFoundError:
            return False
    
    def list_users(self, storage_type):
        """
        List all users that have data of the specified type
        
        Args:
            storage_type (str): Type of storage (tokens, history, etc.)
            
        Returns:
            list: List of user IDs
        """
        dir_path = os.path.join(self.base_path, storage_type)
        if not os.path.exists(dir_path):
            return []
            
        users = set()
        for filename in os.listdir(dir_path):
            if filename.endswith('.json'):
                # Extract user_id from filename (user_id_type.json or user_id_provider.json)
                parts = filename.split('_')
                if len(parts) >= 2:
                    users.add(parts[0])
                    
        return list(users)
