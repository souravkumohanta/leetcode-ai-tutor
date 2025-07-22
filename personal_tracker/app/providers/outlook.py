"""
Outlook Calendar provider implementation for the Personal Tracker App
"""
import functools
import time
import random
import requests
from datetime import datetime, timedelta
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
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code
                
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
                if status_code == 429 and 'Retry-After' in e.response.headers:
                    delay = int(e.response.headers['Retry-After'])
                    
                time.sleep(delay)
                
    return wrapper

class OutlookCalendarProvider(CalendarProvider):
    """
    Outlook Calendar provider implementation
    
    This class implements the CalendarProvider interface for Microsoft Outlook Calendar.
    """
    
    # Microsoft Graph API base URL
    GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'
    
    def __init__(self, auth_service):
        """
        Initialize the Outlook Calendar provider
        
        Args:
            auth_service (AuthenticationService): Authentication service instance
        """
        self.auth_service = auth_service
        
    def _get_headers(self, user_id):
        """
        Get authentication headers for Microsoft Graph API
        
        Args:
            user_id (str): User identifier
            
        Returns:
            dict: Headers for API requests
            
        Raises:
            Exception: If authentication fails
        """
        token_data = self.auth_service.get_valid_token('outlook', user_id)
        
        if not token_data:
            raise Exception("No valid Outlook Calendar token found")
            
        return {
            'Authorization': f"Bearer {token_data['access_token']}",
            'Content-Type': 'application/json'
        }
    
    @api_request_with_retry
    def get_busy_intervals(self, user_id, start_date, end_date):
        """
        Get busy intervals from Outlook Calendar
        
        Args:
            user_id (str): User identifier
            start_date (datetime): Start date for the query
            end_date (datetime): End date for the query
            
        Returns:
            list: List of busy intervals, each with 'start' and 'end' keys
        """
        headers = self._get_headers(user_id)
        
        # Format dates for Microsoft Graph API
        start_datetime = start_date.isoformat()
        end_datetime = end_date.isoformat()
        
        # Use the calendar view endpoint to get events in the time range
        url = f"{self.GRAPH_API_ENDPOINT}/me/calendarView"
        params = {
            'startDateTime': start_datetime,
            'endDateTime': end_datetime,
            '$select': 'subject,start,end,isAllDay'
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        events = response.json().get('value', [])
        
        # Process and normalize the response
        busy_intervals = []
        for event in events:
            # Skip all-day events as they don't block specific time slots
            if event.get('isAllDay'):
                continue
                
            busy_intervals.append({
                'start': event['start']['dateTime'],
                'end': event['end']['dateTime']
            })
            
        return busy_intervals
    
    @api_request_with_retry
    def create_event(self, user_id, title, start_time, end_time, description=None):
        """
        Create a new event in Outlook Calendar
        
        Args:
            user_id (str): User identifier
            title (str): Event title
            start_time (datetime): Event start time
            end_time (datetime): Event end time
            description (str, optional): Event description
            
        Returns:
            str: Event ID
        """
        headers = self._get_headers(user_id)
        
        # Format the event for Microsoft Graph API
        event = {
            'subject': title,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC'
            },
            # Add metadata as categories
            'categories': ['Study Session', 'PersonalTrackerApp']
        }
        
        if description:
            event['body'] = {
                'contentType': 'text',
                'content': description
            }
            
        url = f"{self.GRAPH_API_ENDPOINT}/me/events"
        response = requests.post(url, headers=headers, json=event)
        response.raise_for_status()
        
        created_event = response.json()
        return created_event['id']
    
    @api_request_with_retry
    def update_event(self, user_id, event_id, start_time=None, end_time=None, title=None, description=None):
        """
        Update an existing event in Outlook Calendar
        
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
        headers = self._get_headers(user_id)
        
        # Create update payload with only the fields to update
        update_payload = {}
        
        if title:
            update_payload['subject'] = title
            
        if description:
            update_payload['body'] = {
                'contentType': 'text',
                'content': description
            }
            
        if start_time:
            update_payload['start'] = {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC'
            }
            
        if end_time:
            update_payload['end'] = {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC'
            }
            
        url = f"{self.GRAPH_API_ENDPOINT}/me/events/{event_id}"
        response = requests.patch(url, headers=headers, json=update_payload)
        response.raise_for_status()
        
        updated_event = response.json()
        return updated_event['id']
    
    @api_request_with_retry
    def delete_event(self, user_id, event_id):
        """
        Delete an event from Outlook Calendar
        
        Args:
            user_id (str): User identifier
            event_id (str): Event ID
            
        Returns:
            bool: True if successful
        """
        headers = self._get_headers(user_id)
        
        url = f"{self.GRAPH_API_ENDPOINT}/me/events/{event_id}"
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        
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
        headers = self._get_headers(user_id)
        
        url = f"{self.GRAPH_API_ENDPOINT}/me/events/{event_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        event = response.json()
        
        # Normalize the event data
        return {
            'id': event['id'],
            'title': event.get('subject', ''),
            'description': event.get('body', {}).get('content', ''),
            'start': event['start']['dateTime'],
            'end': event['end']['dateTime'],
            'is_study_session': 'Study Session' in event.get('categories', [])
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
        headers = self._get_headers(user_id)
        
        # Format dates for Microsoft Graph API
        start_datetime = start_date.isoformat()
        end_datetime = end_date.isoformat()
        
        # Use the calendar view endpoint to get events in the time range
        url = f"{self.GRAPH_API_ENDPOINT}/me/calendarView"
        params = {
            'startDateTime': start_datetime,
            'endDateTime': end_datetime,
            '$select': 'id,subject,body,start,end,isAllDay,categories'
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        events = response.json().get('value', [])
        
        # Normalize the event data
        normalized_events = []
        for event in events:
            # Skip all-day events
            if event.get('isAllDay'):
                continue
                
            normalized_events.append({
                'id': event['id'],
                'title': event.get('subject', ''),
                'description': event.get('body', {}).get('content', ''),
                'start': event['start']['dateTime'],
                'end': event['end']['dateTime'],
                'is_study_session': 'Study Session' in event.get('categories', [])
            })
            
        return normalized_events
