"""
Base calendar provider interface for the Personal Tracker App
"""
from abc import ABC, abstractmethod
from datetime import datetime

class CalendarProvider(ABC):
    """
    Abstract base class for calendar providers
    
    This class defines the interface that all calendar providers must implement.
    """
    
    @abstractmethod
    def get_busy_intervals(self, user_id, start_date, end_date):
        """
        Get busy intervals from the calendar
        
        Args:
            user_id (str): User identifier
            start_date (datetime): Start date for the query
            end_date (datetime): End date for the query
            
        Returns:
            list: List of busy intervals, each with 'start' and 'end' keys
        """
        pass
    
    @abstractmethod
    def create_event(self, user_id, title, start_time, end_time, description=None):
        """
        Create a new calendar event
        
        Args:
            user_id (str): User identifier
            title (str): Event title
            start_time (datetime): Event start time
            end_time (datetime): Event end time
            description (str, optional): Event description
            
        Returns:
            str: Event ID
        """
        pass
    
    @abstractmethod
    def update_event(self, user_id, event_id, start_time=None, end_time=None, title=None, description=None):
        """
        Update an existing calendar event
        
        Args:
            user_id (str): User identifier
            event_id (str): Event ID
            start_time (datetime, optional): New start time
            end_time (datetime, optional): New end time
            title (str, optional): New title
            description (str, optional): New description
            
        Returns:
            str: Event ID
        """
        pass
    
    @abstractmethod
    def delete_event(self, user_id, event_id):
        """
        Delete a calendar event
        
        Args:
            user_id (str): User identifier
            event_id (str): Event ID
            
        Returns:
            bool: True if successful
        """
        pass
    
    @abstractmethod
    def get_event(self, user_id, event_id):
        """
        Get a calendar event
        
        Args:
            user_id (str): User identifier
            event_id (str): Event ID
            
        Returns:
            dict: Event data
        """
        pass
    
    @abstractmethod
    def list_events(self, user_id, start_date, end_date):
        """
        List calendar events in a date range
        
        Args:
            user_id (str): User identifier
            start_date (datetime): Start date for the query
            end_date (datetime): End date for the query
            
        Returns:
            list: List of events
        """
        pass
