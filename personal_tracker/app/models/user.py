"""
User models for the Personal Tracker App
"""
from datetime import time, datetime, timedelta

class UserPreferences:
    """
    User preferences model
    
    This class represents user preferences for study sessions and work hours.
    """
    
    def __init__(self, user_id, work_start_time=None, work_end_time=None,
                earliest_study_time=None, latest_study_time=None,
                min_study_duration=None, morning_priority=None):
        """
        Initialize user preferences
        
        Args:
            user_id (str): User identifier
            work_start_time (str or time, optional): Work start time (default: 10:30)
            work_end_time (str or time, optional): Work end time (default: 18:30)
            earliest_study_time (str or time, optional): Earliest study time (default: 07:00)
            latest_study_time (str or time, optional): Latest study time (default: 22:00)
            min_study_duration (int, optional): Minimum study duration in minutes (default: 90)
            morning_priority (bool, optional): Prioritize morning slots (default: True)
        """
        self.user_id = user_id
        
        # Set default values
        self.work_start_time = self._parse_time(work_start_time, time(10, 30))
        self.work_end_time = self._parse_time(work_end_time, time(18, 30))
        self.earliest_study_time = self._parse_time(earliest_study_time, time(7, 0))
        self.latest_study_time = self._parse_time(latest_study_time, time(22, 0))
        self.min_study_duration = min_study_duration or 90
        self.morning_priority = morning_priority if morning_priority is not None else True
        
    def to_dict(self):
        """
        Convert preferences to dictionary
        
        Returns:
            dict: Dictionary representation of preferences
        """
        return {
            'user_id': self.user_id,
            'work_hours': {
                'start': self._format_time(self.work_start_time),
                'end': self._format_time(self.work_end_time)
            },
            'study_preferences': {
                'earliest_time': self._format_time(self.earliest_study_time),
                'latest_time': self._format_time(self.latest_study_time),
                'min_duration': self.min_study_duration
            },
            'priorities': {
                'morning_first': self.morning_priority
            }
        }
        
    @classmethod
    def from_dict(cls, data):
        """
        Create preferences from dictionary
        
        Args:
            data (dict): Dictionary representation of preferences
            
        Returns:
            UserPreferences: User preferences instance
        """
        return cls(
            user_id=data.get('user_id'),
            work_start_time=data.get('work_hours', {}).get('start'),
            work_end_time=data.get('work_hours', {}).get('end'),
            earliest_study_time=data.get('study_preferences', {}).get('earliest_time'),
            latest_study_time=data.get('study_preferences', {}).get('latest_time'),
            min_study_duration=data.get('study_preferences', {}).get('min_duration'),
            morning_priority=data.get('priorities', {}).get('morning_first')
        )
        
    def _parse_time(self, time_value, default):
        """
        Parse time value from string or time object
        
        Args:
            time_value (str or time): Time value
            default (time): Default time value
            
        Returns:
            time: Time object
        """
        if time_value is None:
            return default
            
        if isinstance(time_value, time):
            return time_value
            
        if isinstance(time_value, str):
            # Parse time string (format: HH:MM)
            try:
                hours, minutes = map(int, time_value.split(':'))
                return time(hours, minutes)
            except (ValueError, TypeError):
                return default
                
        return default
        
    def _format_time(self, time_obj):
        """
        Format time object as string
        
        Args:
            time_obj (time): Time object
            
        Returns:
            str: Formatted time string (HH:MM)
        """
        return time_obj.strftime('%H:%M')
        
    def is_work_hours(self, dt):
        """
        Check if a datetime is within work hours
        
        Args:
            dt (datetime): Datetime to check
            
        Returns:
            bool: True if within work hours
        """
        # Only check time component
        t = dt.time()
        
        # Check if time is between work start and end times
        return self.work_start_time <= t <= self.work_end_time
        
    def is_valid_study_time(self, dt):
        """
        Check if a datetime is within valid study hours
        
        Args:
            dt (datetime): Datetime to check
            
        Returns:
            bool: True if within valid study hours
        """
        # Only check time component
        t = dt.time()
        
        # Check if time is outside work hours and within study hours
        return (self.earliest_study_time <= t < self.work_start_time or
                self.work_end_time < t <= self.latest_study_time)
                
    def get_study_window_for_date(self, date):
        """
        Get study time windows for a specific date
        
        Args:
            date (date): Date to get study windows for
            
        Returns:
            list: List of (start, end) tuples representing study windows
        """
        # Create datetime objects for the start and end of each window
        morning_start = datetime.combine(date, self.earliest_study_time)
        morning_end = datetime.combine(date, self.work_start_time)
        
        evening_start = datetime.combine(date, self.work_end_time)
        evening_end = datetime.combine(date, self.latest_study_time)
        
        # Return windows in priority order
        if self.morning_priority:
            return [(morning_start, morning_end), (evening_start, evening_end)]
        else:
            return [(evening_start, evening_end), (morning_start, morning_end)]
