"""
Scheduler service for the Personal Tracker App
"""
from datetime import datetime, timedelta, time
from app.models.event import Event, StudySession

class SchedulerService:
    """
    Scheduler service for study session scheduling
    
    This class provides methods to compute free time slots and propose
    study sessions based on calendar data and user preferences.
    """
    
    def __init__(self, calendar_service, json_storage):
        """
        Initialize the scheduler service
        
        Args:
            calendar_service (CalendarService): Calendar service instance
            json_storage (JsonStorage): JSON storage instance
        """
        self.calendar_service = calendar_service
        self.json_storage = json_storage
        
    def compute_free_slots(self, user_id, user_preferences, target_date, min_duration=None):
        """
        Compute available free slots for the target date
        
        Args:
            user_id (str): User identifier
            user_preferences (UserPreferences): User preferences
            target_date (date): Target date
            min_duration (int, optional): Minimum slot duration in minutes
            
        Returns:
            list: List of (start, end) tuples representing free slots
        """
        if min_duration is None:
            min_duration = user_preferences.min_study_duration
            
        # Get study windows for the date
        study_windows = user_preferences.get_study_window_for_date(target_date)
        
        # Get busy intervals for the entire day
        start_datetime = datetime.combine(target_date, time(0, 0))
        end_datetime = datetime.combine(target_date, time(23, 59, 59))
        
        busy_intervals, errors = self.calendar_service.get_busy_intervals(
            user_id, start_datetime, end_datetime
        )
        
        # Convert busy intervals to datetime objects if they're strings
        normalized_busy = []
        for interval in busy_intervals:
            start = interval['start']
            end = interval['end']
            
            if isinstance(start, str):
                start = datetime.fromisoformat(start.replace('Z', '+00:00'))
            if isinstance(end, str):
                end = datetime.fromisoformat(end.replace('Z', '+00:00'))
                
            normalized_busy.append((start, end))
            
        # Compute free slots within each study window
        free_slots = []
        
        for window_start, window_end in study_windows:
            # Start with the entire window as a free slot
            current_slots = [(window_start, window_end)]
            
            # Remove busy intervals from current slots
            for busy_start, busy_end in normalized_busy:
                # Skip busy intervals outside the window
                if busy_end <= window_start or busy_start >= window_end:
                    continue
                    
                # Update current slots
                new_slots = []
                for slot_start, slot_end in current_slots:
                    # Skip if slot is completely within busy interval
                    if busy_start <= slot_start and slot_end <= busy_end:
                        continue
                        
                    # If busy interval splits the slot, create two new slots
                    if slot_start < busy_start and busy_end < slot_end:
                        new_slots.append((slot_start, busy_start))
                        new_slots.append((busy_end, slot_end))
                    # If busy interval overlaps start of slot
                    elif busy_start <= slot_start and busy_end > slot_start:
                        new_slots.append((busy_end, slot_end))
                    # If busy interval overlaps end of slot
                    elif busy_start < slot_end and busy_end >= slot_end:
                        new_slots.append((slot_start, busy_start))
                    # If busy interval doesn't overlap slot
                    else:
                        new_slots.append((slot_start, slot_end))
                        
                current_slots = new_slots
                
            # Filter slots by minimum duration
            min_duration_delta = timedelta(minutes=min_duration)
            valid_slots = [
                (start, end) for start, end in current_slots
                if end - start >= min_duration_delta
            ]
            
            free_slots.extend(valid_slots)
            
        return free_slots
        
    def propose_study_sessions(self, user_id, user_preferences, start_date, end_date, daily_target=None):
        """
        Generate study session proposals for a date range
        
        Args:
            user_id (str): User identifier
            user_preferences (UserPreferences): User preferences
            start_date (date): Start date
            end_date (date): End date
            daily_target (int, optional): Daily target duration in minutes
            
        Returns:
            dict: Dictionary mapping dates to lists of proposed sessions
        """
        if daily_target is None:
            # Default to 2 hours per day
            daily_target = 120
            
        proposals = {}
        current_date = start_date
        
        while current_date <= end_date:
            # Skip weekends if it's a weekday-only schedule
            if current_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                current_date += timedelta(days=1)
                continue
                
            # Compute free slots for the date
            free_slots = self.compute_free_slots(
                user_id, user_preferences, current_date
            )
            
            # Generate proposals for the date
            date_proposals = self._generate_proposals_for_date(
                user_id, free_slots, daily_target, user_preferences.min_study_duration
            )
            
            proposals[current_date] = date_proposals
            current_date += timedelta(days=1)
            
        return proposals
        
    def _generate_proposals_for_date(self, user_id, free_slots, daily_target, min_duration):
        """
        Generate study session proposals for a specific date
        
        Args:
            user_id (str): User identifier
            free_slots (list): List of (start, end) tuples representing free slots
            daily_target (int): Daily target duration in minutes
            min_duration (int): Minimum session duration in minutes
            
        Returns:
            list: List of StudySession objects
        """
        proposals = []
        remaining_target = daily_target
        
        # Sort slots by duration (longest first)
        sorted_slots = sorted(free_slots, key=lambda x: x[1] - x[0], reverse=True)
        
        for slot_start, slot_end in sorted_slots:
            # Skip if we've met the daily target
            if remaining_target <= 0:
                break
                
            # Calculate session duration
            slot_duration = int((slot_end - slot_start).total_seconds() / 60)
            
            # Limit session duration to remaining target or max 2 hours
            session_duration = min(slot_duration, remaining_target, 120)
            
            # Ensure session meets minimum duration
            if session_duration < min_duration:
                continue
                
            # Create session end time
            session_end = slot_start + timedelta(minutes=session_duration)
            
            # Create study session proposal
            session = StudySession(
                title="Study Session",
                start_time=slot_start,
                end_time=session_end,
                user_id=user_id,
                status="proposed"
            )
            
            proposals.append(session)
            remaining_target -= session_duration
            
        return proposals
        
    def schedule_approved_sessions(self, user_id, approved_sessions, provider_type=None):
        """
        Create calendar events for approved study sessions
        
        Args:
            user_id (str): User identifier
            approved_sessions (list): List of StudySession objects
            provider_type (str, optional): Calendar provider to use
            
        Returns:
            list: List of created StudySession objects with provider information
        """
        created_sessions = []
        
        for session in approved_sessions:
            try:
                # Create calendar event
                event_id, provider = self.calendar_service.create_event(
                    user_id=user_id,
                    title=session.title,
                    start_time=session.start_time,
                    end_time=session.end_time,
                    description=session.description,
                    provider_type=provider_type
                )
                
                # Update session with provider information
                session.provider = provider
                session.provider_event_id = event_id
                session.status = "scheduled"
                
                # Store session in history
                self._store_session(user_id, session)
                
                created_sessions.append(session)
            except Exception as e:
                # Log error but continue with other sessions
                print(f"Error scheduling session: {str(e)}")
                
        return created_sessions
        
    def handle_conflicts(self, user_id, user_preferences):
        """
        Detect and resolve conflicts with existing study sessions
        
        Args:
            user_id (str): User identifier
            user_preferences (UserPreferences): User preferences
            
        Returns:
            tuple: (rescheduled_sessions, cancelled_sessions)
        """
        # Get all scheduled study sessions for the next week
        today = datetime.now().date()
        next_week = today + timedelta(days=7)
        
        study_sessions, _ = self.calendar_service.list_study_sessions(
            user_id, datetime.combine(today, time(0, 0)), 
            datetime.combine(next_week, time(23, 59, 59))
        )
        
        # Get busy intervals for the same period
        busy_intervals, _ = self.calendar_service.get_busy_intervals(
            user_id, 
            datetime.combine(today, time(0, 0)), 
            datetime.combine(next_week, time(23, 59, 59))
        )
        
        # Convert busy intervals to Event objects for easier comparison
        busy_events = []
        for interval in busy_intervals:
            start = interval['start']
            end = interval['end']
            
            if isinstance(start, str):
                start = datetime.fromisoformat(start.replace('Z', '+00:00'))
            if isinstance(end, str):
                end = datetime.fromisoformat(end.replace('Z', '+00:00'))
                
            # Skip intervals that are study sessions (to avoid self-conflicts)
            is_study_session = False
            for session in study_sessions:
                if (isinstance(session, dict) and 
                    session.get('start') == start and 
                    session.get('end') == end):
                    is_study_session = True
                    break
                    
            if not is_study_session:
                busy_events.append(Event(
                    start_time=start,
                    end_time=end
                ))
                
        # Check each study session for conflicts
        rescheduled_sessions = []
        cancelled_sessions = []
        
        for session_data in study_sessions:
            # Convert to StudySession object if it's a dict
            if isinstance(session_data, dict):
                session = StudySession.from_dict(session_data)
            else:
                session = session_data
                
            # Check for conflicts
            has_conflict = False
            for busy_event in busy_events:
                if session.overlaps(busy_event):
                    has_conflict = True
                    break
                    
            if has_conflict:
                # Try to reschedule
                session_date = session.start_time.date()
                free_slots = self.compute_free_slots(
                    user_id, user_preferences, session_date
                )
                
                # Find a new slot with the same duration
                session_duration = session.duration
                rescheduled = False
                
                for slot_start, slot_end in free_slots:
                    slot_duration = int((slot_end - slot_start).total_seconds() / 60)
                    
                    if slot_duration >= session_duration:
                        # Create new session end time
                        new_end = slot_start + timedelta(minutes=session_duration)
                        
                        # Update session times
                        try:
                            self.calendar_service.update_event(
                                user_id=user_id,
                                event_id=session.provider_event_id,
                                provider_type=session.provider,
                                start_time=slot_start,
                                end_time=new_end
                            )
                            
                            # Update session object
                            session.start_time = slot_start
                            session.end_time = new_end
                            session.status = "rescheduled"
                            
                            # Store updated session
                            self._store_session(user_id, session)
                            
                            rescheduled_sessions.append(session)
                            rescheduled = True
                            break
                        except Exception as e:
                            # Log error but continue trying other slots
                            print(f"Error rescheduling session: {str(e)}")
                            
                if not rescheduled:
                    # Cancel the session if it can't be rescheduled
                    try:
                        self.calendar_service.delete_event(
                            user_id=user_id,
                            event_id=session.provider_event_id,
                            provider_type=session.provider
                        )
                        
                        # Update session status
                        session.status = "cancelled"
                        
                        # Store updated session
                        self._store_session(user_id, session)
                        
                        cancelled_sessions.append(session)
                    except Exception as e:
                        # Log error but continue with other sessions
                        print(f"Error cancelling session: {str(e)}")
                        
        return rescheduled_sessions, cancelled_sessions
        
    def _store_session(self, user_id, session):
        """
        Store a study session in history
        
        Args:
            user_id (str): User identifier
            session (StudySession): Study session to store
        """
        # Get existing history
        history = self.json_storage.load("history", user_id) or {
            "user_id": user_id,
            "sessions": []
        }
        
        # Convert session to dict
        session_dict = session.to_dict()
        
        # Update existing session or add new one
        found = False
        for i, existing in enumerate(history["sessions"]):
            if existing.get("id") == session_dict["id"]:
                history["sessions"][i] = session_dict
                found = True
                break
                
        if not found:
            history["sessions"].append(session_dict)
            
        # Save updated history
        self.json_storage.save("history", user_id, history)
        
    def get_tracked_events(self, user_id):
        """
        Get tracked study events for a user
        
        Args:
            user_id (str): User identifier
            
        Returns:
            list: List of tracked events
        """
        events_data = self.json_storage.load("events", user_id) or {
            "user_id": user_id,
            "study_events": []
        }
        
        return events_data.get("study_events", [])
        
    def track_event(self, user_id, event):
        """
        Track a study event
        
        Args:
            user_id (str): User identifier
            event (dict): Event data to track
        """
        events_data = self.json_storage.load("events", user_id) or {
            "user_id": user_id,
            "study_events": []
        }
        
        # Add event to tracked events
        events_data["study_events"].append(event)
        
        # Save updated events
        self.json_storage.save("events", user_id, events_data)
