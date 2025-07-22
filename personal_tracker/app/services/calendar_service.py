"""
Calendar service for the Personal Tracker App
"""
from datetime import datetime

class CalendarService:
    """
    Calendar service for unified access to calendar providers
    
    This class provides methods to interact with multiple calendar providers
    through a unified interface.
    """
    
    def __init__(self):
        """Initialize the calendar service"""
        self.providers = {}
        
    def register_provider(self, provider_type, provider):
        """
        Register a calendar provider
        
        Args:
            provider_type (str): Provider type (google, outlook)
            provider (CalendarProvider): Provider instance
        """
        self.providers[provider_type] = provider
        
    def get_busy_intervals(self, user_id, start_date, end_date, provider_types=None):
        """
        Get busy intervals from all or specified providers
        
        Args:
            user_id (str): User identifier
            start_date (datetime): Start date for the query
            end_date (datetime): End date for the query
            provider_types (list, optional): List of provider types to query
            
        Returns:
            list: List of busy intervals, each with 'start' and 'end' keys
        """
        if not provider_types:
            provider_types = list(self.providers.keys())
            
        all_intervals = []
        errors = []
        
        for provider_type in provider_types:
            if provider_type in self.providers:
                try:
                    provider_intervals = self.providers[provider_type].get_busy_intervals(
                        user_id, start_date, end_date
                    )
                    all_intervals.extend(provider_intervals)
                except Exception as e:
                    # Log error but continue with other providers
                    errors.append(f"Error getting busy intervals from {provider_type}: {str(e)}")
                    
        # Merge overlapping intervals
        return self._merge_intervals(all_intervals), errors
        
    def create_event(self, user_id, title, start_time, end_time, 
                    description=None, provider_type=None):
        """
        Create an event in the specified or default provider
        
        Args:
            user_id (str): User identifier
            title (str): Event title
            start_time (datetime): Event start time
            end_time (datetime): Event end time
            description (str, optional): Event description
            provider_type (str, optional): Provider type to use
            
        Returns:
            tuple: (event_id, provider_type)
        """
        if not provider_type:
            # Use first available provider
            if not self.providers:
                raise ValueError("No calendar providers registered")
                
            provider_type = next(iter(self.providers))
            
        if provider_type not in self.providers:
            raise ValueError(f"Provider {provider_type} not registered")
            
        event_id = self.providers[provider_type].create_event(
            user_id, title, start_time, end_time, description
        )
        
        return event_id, provider_type
        
    def update_event(self, user_id, event_id, provider_type, 
                    start_time=None, end_time=None, title=None, description=None):
        """
        Update an existing event
        
        Args:
            user_id (str): User identifier
            event_id (str): Event ID
            provider_type (str): Provider type
            start_time (datetime, optional): New start time
            end_time (datetime, optional): New end time
            title (str, optional): New title
            description (str, optional): New description
            
        Returns:
            str: Event ID
        """
        if provider_type not in self.providers:
            raise ValueError(f"Provider {provider_type} not registered")
            
        return self.providers[provider_type].update_event(
            user_id, event_id, start_time, end_time, title, description
        )
        
    def delete_event(self, user_id, event_id, provider_type):
        """
        Delete an event
        
        Args:
            user_id (str): User identifier
            event_id (str): Event ID
            provider_type (str): Provider type
            
        Returns:
            bool: True if successful
        """
        if provider_type not in self.providers:
            raise ValueError(f"Provider {provider_type} not registered")
            
        return self.providers[provider_type].delete_event(user_id, event_id)
        
    def get_event(self, user_id, event_id, provider_type):
        """
        Get an event
        
        Args:
            user_id (str): User identifier
            event_id (str): Event ID
            provider_type (str): Provider type
            
        Returns:
            dict: Event data
        """
        if provider_type not in self.providers:
            raise ValueError(f"Provider {provider_type} not registered")
            
        return self.providers[provider_type].get_event(user_id, event_id)
        
    def list_events(self, user_id, start_date, end_date, provider_types=None):
        """
        List events from all or specified providers
        
        Args:
            user_id (str): User identifier
            start_date (datetime): Start date for the query
            end_date (datetime): End date for the query
            provider_types (list, optional): List of provider types to query
            
        Returns:
            list: List of events with provider information
        """
        if not provider_types:
            provider_types = list(self.providers.keys())
            
        all_events = []
        errors = []
        
        for provider_type in provider_types:
            if provider_type in self.providers:
                try:
                    provider_events = self.providers[provider_type].list_events(
                        user_id, start_date, end_date
                    )
                    
                    # Add provider information to each event
                    for event in provider_events:
                        event['provider'] = provider_type
                        
                    all_events.extend(provider_events)
                except Exception as e:
                    # Log error but continue with other providers
                    errors.append(f"Error listing events from {provider_type}: {str(e)}")
                    
        # Sort events by start time
        all_events.sort(key=lambda x: x['start'])
        
        return all_events, errors
        
    def list_study_sessions(self, user_id, start_date, end_date, provider_types=None):
        """
        List study sessions from all or specified providers
        
        Args:
            user_id (str): User identifier
            start_date (datetime): Start date for the query
            end_date (datetime): End date for the query
            provider_types (list, optional): List of provider types to query
            
        Returns:
            list: List of study session events
        """
        events, errors = self.list_events(user_id, start_date, end_date, provider_types)
        
        # Filter for study sessions
        study_sessions = [event for event in events if event.get('is_study_session')]
        
        return study_sessions, errors
        
    def _merge_intervals(self, intervals):
        """
        Merge overlapping time intervals
        
        Args:
            intervals (list): List of intervals, each with 'start' and 'end' keys
            
        Returns:
            list: List of merged intervals
        """
        if not intervals:
            return []
            
        # Sort intervals by start time
        sorted_intervals = sorted(intervals, key=lambda x: x['start'])
        
        merged = [sorted_intervals[0]]
        
        for interval in sorted_intervals[1:]:
            # Get last merged interval
            last = merged[-1]
            
            # Convert string times to datetime if needed
            current_start = self._ensure_datetime(interval['start'])
            current_end = self._ensure_datetime(interval['end'])
            last_start = self._ensure_datetime(last['start'])
            last_end = self._ensure_datetime(last['end'])
            
            # Check for overlap
            if current_start <= last_end:
                # Merge overlapping intervals
                last['end'] = max(current_end, last_end).isoformat() if isinstance(max(current_end, last_end), datetime) else max(current_end, last_end)
            else:
                # Add non-overlapping interval
                merged.append(interval)
                
        return merged
        
    def _ensure_datetime(self, time_value):
        """
        Convert string time to datetime if needed
        
        Args:
            time_value (str or datetime): Time value
            
        Returns:
            datetime: Datetime object
        """
        if isinstance(time_value, str):
            # Handle various ISO formats
            if 'Z' in time_value:
                time_value = time_value.replace('Z', '+00:00')
            return datetime.fromisoformat(time_value)
        return time_value
