"""
Event models for the Personal Tracker App
"""
import uuid
from datetime import datetime, timedelta

class Event:
    """
    Event model
    
    This class represents a calendar event, which could be a study session
    or any other calendar event.
    """
    
    def __init__(self, id=None, title=None, start_time=None, end_time=None,
                description=None, provider=None, provider_event_id=None,
                is_study_session=False, status="scheduled", user_id=None):
        """
        Initialize an event
        
        Args:
            id (str, optional): Event ID (generated if not provided)
            title (str, optional): Event title
            start_time (datetime, optional): Event start time
            end_time (datetime, optional): Event end time
            description (str, optional): Event description
            provider (str, optional): Calendar provider (google, outlook)
            provider_event_id (str, optional): Event ID in the provider's system
            is_study_session (bool, optional): Whether this is a study session
            status (str, optional): Event status (scheduled, completed, cancelled)
            user_id (str, optional): User identifier
        """
        self.id = id or str(uuid.uuid4())
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.description = description
        self.provider = provider
        self.provider_event_id = provider_event_id
        self.is_study_session = is_study_session
        self.status = status
        self.user_id = user_id
        
    @property
    def duration(self):
        """
        Get event duration in minutes
        
        Returns:
            int: Duration in minutes or None if start/end time not set
        """
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return None
        
    def to_dict(self):
        """
        Convert event to dictionary
        
        Returns:
            dict: Dictionary representation of event
        """
        return {
            'id': self.id,
            'title': self.title,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'description': self.description,
            'provider': self.provider,
            'provider_event_id': self.provider_event_id,
            'is_study_session': self.is_study_session,
            'status': self.status,
            'user_id': self.user_id
        }
        
    @classmethod
    def from_dict(cls, data):
        """
        Create event from dictionary
        
        Args:
            data (dict): Dictionary representation of event
            
        Returns:
            Event: Event instance
        """
        # Parse datetime strings
        start_time = None
        if data.get('start_time'):
            try:
                start_time = datetime.fromisoformat(data['start_time'])
            except (ValueError, TypeError):
                pass
                
        end_time = None
        if data.get('end_time'):
            try:
                end_time = datetime.fromisoformat(data['end_time'])
            except (ValueError, TypeError):
                pass
                
        return cls(
            id=data.get('id'),
            title=data.get('title'),
            start_time=start_time,
            end_time=end_time,
            description=data.get('description'),
            provider=data.get('provider'),
            provider_event_id=data.get('provider_event_id'),
            is_study_session=data.get('is_study_session', False),
            status=data.get('status', 'scheduled'),
            user_id=data.get('user_id')
        )
        
    @classmethod
    def from_provider_event(cls, provider_event, provider, user_id):
        """
        Create event from provider event data
        
        Args:
            provider_event (dict): Provider event data
            provider (str): Provider type (google, outlook)
            user_id (str): User identifier
            
        Returns:
            Event: Event instance
        """
        # Parse datetime strings
        start_time = None
        if provider_event.get('start'):
            try:
                start_str = provider_event['start']
                if isinstance(start_str, str):
                    # Handle 'Z' in ISO format
                    if 'Z' in start_str:
                        start_str = start_str.replace('Z', '+00:00')
                    start_time = datetime.fromisoformat(start_str)
            except (ValueError, TypeError):
                pass
                
        end_time = None
        if provider_event.get('end'):
            try:
                end_str = provider_event['end']
                if isinstance(end_str, str):
                    # Handle 'Z' in ISO format
                    if 'Z' in end_str:
                        end_str = end_str.replace('Z', '+00:00')
                    end_time = datetime.fromisoformat(end_str)
            except (ValueError, TypeError):
                pass
                
        return cls(
            title=provider_event.get('title'),
            start_time=start_time,
            end_time=end_time,
            description=provider_event.get('description'),
            provider=provider,
            provider_event_id=provider_event.get('id'),
            is_study_session=provider_event.get('is_study_session', False),
            user_id=user_id
        )
        
    def overlaps(self, other):
        """
        Check if this event overlaps with another event
        
        Args:
            other (Event): Other event to check
            
        Returns:
            bool: True if events overlap
        """
        if not self.start_time or not self.end_time or not other.start_time or not other.end_time:
            return False
            
        # Events overlap if one starts before the other ends
        return self.start_time < other.end_time and other.start_time < self.end_time
        
    def __str__(self):
        """String representation of event"""
        if self.start_time and self.end_time:
            time_str = f"{self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.end_time.strftime('%H:%M')}"
        else:
            time_str = "No time specified"
            
        return f"{self.title} ({time_str})"

class StudySession(Event):
    """
    Study session model
    
    This class represents a study session event.
    """
    
    def __init__(self, id=None, title="Study Session", start_time=None, end_time=None,
                description=None, provider=None, provider_event_id=None,
                status="scheduled", user_id=None, topics=None, notes=None):
        """
        Initialize a study session
        
        Args:
            id (str, optional): Event ID (generated if not provided)
            title (str, optional): Event title (default: "Study Session")
            start_time (datetime, optional): Event start time
            end_time (datetime, optional): Event end time
            description (str, optional): Event description
            provider (str, optional): Calendar provider (google, outlook)
            provider_event_id (str, optional): Event ID in the provider's system
            status (str, optional): Event status (scheduled, completed, cancelled)
            user_id (str, optional): User identifier
            topics (list, optional): List of study topics
            notes (str, optional): Study session notes
        """
        super().__init__(
            id=id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            provider=provider,
            provider_event_id=provider_event_id,
            is_study_session=True,
            status=status,
            user_id=user_id
        )
        self.topics = topics or []
        self.notes = notes
        
    def to_dict(self):
        """
        Convert study session to dictionary
        
        Returns:
            dict: Dictionary representation of study session
        """
        data = super().to_dict()
        data.update({
            'topics': self.topics,
            'notes': self.notes
        })
        return data
        
    @classmethod
    def from_dict(cls, data):
        """
        Create study session from dictionary
        
        Args:
            data (dict): Dictionary representation of study session
            
        Returns:
            StudySession: Study session instance
        """
        # Parse datetime strings
        start_time = None
        if data.get('start_time'):
            try:
                start_time = datetime.fromisoformat(data['start_time'])
            except (ValueError, TypeError):
                pass
                
        end_time = None
        if data.get('end_time'):
            try:
                end_time = datetime.fromisoformat(data['end_time'])
            except (ValueError, TypeError):
                pass
                
        return cls(
            id=data.get('id'),
            title=data.get('title', "Study Session"),
            start_time=start_time,
            end_time=end_time,
            description=data.get('description'),
            provider=data.get('provider'),
            provider_event_id=data.get('provider_event_id'),
            status=data.get('status', 'scheduled'),
            user_id=data.get('user_id'),
            topics=data.get('topics', []),
            notes=data.get('notes')
        )
