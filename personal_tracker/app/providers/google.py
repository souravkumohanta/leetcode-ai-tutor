"""
Google Calendar provider implementation for the Personal Tracker App
"""
import functools
import time
import random
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from app.providers.base import CalendarProvider

def api_request_with_retry(func):
    """Decorator for API requests with exponential backoff retry"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 3
        retry_count = 0
        base_delay = 1  # seconds
        
        while retry_count < max_retries:
            try:
                return func(*args, **kwargs)
            except HttpError as e:
                status_code = e.resp.status
                
                # Don't retry on client errors except 429 (rate limit)
                if status_code < 500 and status_code != 429:
                    raise
                    
                retry_count += 1
                
                if retry_count >= max_retries:
                    raise
                    
                # Calculate delay with exponential backoff
                delay = base_delay * (2 ** (retry_count - 1))
                
                # Add jitter
                delay = delay * (0.5 + random.random())
                
                # If rate limited and Retry-After header exists, use that
                if status_code == 429 and 'Retry-After' in e.resp.headers:
                    delay = int(e.resp.headers['Retry-After'])
                    
                time.sleep(delay)
                
    return wrapper

class GoogleCalendarProvider(CalendarProvider):
    """
    Google Calendar provider implementation
    
    This class implements the CalendarProvider interface for Google Calendar.
    """
    
    # OAuth 2.0 scopes for Google Calendar
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, auth_service):
        """
        Initialize the Google Calendar provider
        
        Args:
            auth_service (AuthenticationService): Authentication service instance
        """
        self.auth_service = auth_service
        
    def _get_service(self, user_id):
        """
        Get an authenticated Google Calendar service
        
        Args:
            user_id (str): User identifier
            
        Returns:
            googleapiclient.discovery.Resource: Google Calendar service
            
        Raises:
            Exception: If authentication fails
        """
        token_data = self.auth_service.get_valid_token('google', user_id)
        
        if not token_data:
            raise Exception("No valid Google Calendar token found")
            
        credentials = Credentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=token_data.get('client_id'),
            client_secret=token_data.get('client_secret'),
            scopes=token_data.get('scopes', self.SCOPES)
        )
        
        return build('calendar', 'v3', credentials=credentials)
    
    @api_request_with_retry
    def get_busy_intervals(self, user_id, start_date, end_date):
        """
        Get busy intervals from Google Calendar
        
        Args:
            user_id (str): User identifier
            start_date (datetime): Start date for the query
            end_date (datetime): End date for the query
            
        Returns:
            list: List of busy intervals, each with 'start' and 'end' keys
        """
        service = self._get_service(user_id)
        
        # Format dates for Google API
        start_datetime = start_date.isoformat() + 'Z'  # 'Z' indicates UTC time
        end_datetime = end_date.isoformat() + 'Z'
        
        # Call the freebusy API
        body = {
            "timeMin": start_datetime,
            "timeMax": end_datetime,
            "items": [{"id": "primary"}]  # Use primary calendar
        }
        
        freebusy_response = service.freebusy().query(body=body).execute()
        
        # Process and normalize the response
        busy_intervals = []
        for calendar_id, calendar_data in freebusy_response.get('calendars', {}).items():
            for busy in calendar_data.get('busy', []):
                busy_intervals.append({
                    'start': busy['start'],
                    'end': busy['end']
                })
                
        return busy_intervals
    
    @api_request_with_retry
    def create_event(self, user_id, title, start_time, end_time, description=None):
        """
        Create a new event in Google Calendar
        
        Args:
            user_id (str): User identifier
            title (str): Event title
            start_time (datetime): Event start time
            end_time (datetime): Event end time
            description (str, optional): Event description
            
        Returns:
            str: Event ID
        """
        service = self._get_service(user_id)
        
        event = {
            'summary': title,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            }
        }
        
        if description:
            event['description'] = description
            
        # Add metadata to identify this as a study session
        event['extendedProperties'] = {
            'private': {
                'isStudySession': 'true',
                'createdBy': 'PersonalTrackerApp'
            }
        }
        
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return created_event['id']
    
    @api_request_with_retry
    def update_event(self, user_id, event_id, start_time=None, end_time=None, title=None, description=None):
        """
        Update an existing event in Google Calendar
        
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
        service = self._get_service(user_id)
        
        # First get the existing event
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        
        # Update the fields that were provided
        if title:
            event['summary'] = title
            
        if description:
            event['description'] = description
            
        if start_time:
            event['start']['dateTime'] = start_time.isoformat()
            
        if end_time:
            event['end']['dateTime'] = end_time.isoformat()
            
        updated_event = service.events().update(
            calendarId='primary', 
            eventId=event_id, 
            body=event
        ).execute()
        
        return updated_event['id']
    
    @api_request_with_retry
    def delete_event(self, user_id, event_id):
        """
        Delete an event from Google Calendar
        
        Args:
            user_id (str): User identifier
            event_id (str): Event ID
            
        Returns:
            bool: True if successful
        """
        service = self._get_service(user_id)
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return True
    
    @api_request_with_retry
    def get_event(self, user_id, event_id):
        """
        Get a calendar event
        
        Args:
            user_id (str): User identifier
            event_id (str): Event ID
            
        Returns:
            dict: Event data
        """
        service = self._get_service(user_id)
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        
        # Normalize the event data
        return {
            'id': event['id'],
            'title': event.get('summary', ''),
            'description': event.get('description', ''),
            'start': event['start']['dateTime'],
            'end': event['end']['dateTime'],
            'is_study_session': event.get('extendedProperties', {}).get('private', {}).get('isStudySession') == 'true'
        }
    
    @api_request_with_retry
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
        service = self._get_service(user_id)
        
        # Format dates for Google API
        start_datetime = start_date.isoformat() + 'Z'  # 'Z' indicates UTC time
        end_datetime = end_date.isoformat() + 'Z'
        
        # Call the events.list API
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_datetime,
            timeMax=end_datetime,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Normalize the event data
        normalized_events = []
        for event in events:
            # Skip events without start/end times (all-day events)
            if 'dateTime' not in event.get('start', {}) or 'dateTime' not in event.get('end', {}):
                continue
                
            normalized_events.append({
                'id': event['id'],
                'title': event.get('summary', ''),
                'description': event.get('description', ''),
                'start': event['start']['dateTime'],
                'end': event['end']['dateTime'],
                'is_study_session': event.get('extendedProperties', {}).get('private', {}).get('isStudySession') == 'true'
            })
            
        return normalized_events
