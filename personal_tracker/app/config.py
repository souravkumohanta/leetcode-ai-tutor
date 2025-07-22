"""
Configuration management for the Personal Tracker App
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration"""
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    
    # Application configuration
    APP_NAME = 'Personal Tracker'
    
    # OAuth configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    MICROSOFT_CLIENT_ID = os.environ.get('MICROSOFT_CLIENT_ID')
    MICROSOFT_CLIENT_SECRET = os.environ.get('MICROSOFT_CLIENT_SECRET')
    
    # User preferences defaults
    DEFAULT_WORK_START_TIME = '10:30'
    DEFAULT_WORK_END_TIME = '18:30'
    DEFAULT_EARLIEST_STUDY_TIME = '07:00'
    DEFAULT_LATEST_STUDY_TIME = '22:00'
    DEFAULT_MIN_STUDY_DURATION = 90  # minutes
    DEFAULT_MORNING_PRIORITY = True

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = False
    TESTING = True
    # Use a separate data directory for testing
    TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'test_data')

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    # In production, ensure SECRET_KEY is set in environment
    SECRET_KEY = os.environ.get('SECRET_KEY')

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get the current configuration"""
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env)
