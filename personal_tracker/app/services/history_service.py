"""
History service for the Personal Tracker App
"""
from datetime import datetime, timedelta
from collections import defaultdict
from app.models.event import StudySession

class HistoryService:
    """
    History service for tracking and analyzing study sessions
    
    This class provides methods to record, retrieve, and analyze
    historical study session data.
    """
    
    def __init__(self, json_storage):
        """
        Initialize the history service
        
        Args:
            json_storage (JsonStorage): JSON storage instance
        """
        self.json_storage = json_storage
        
    def record_study_session(self, user_id, session):
        """
        Record a completed study session
        
        Args:
            user_id (str): User identifier
            session (StudySession or dict): Study session to record
            
        Returns:
            bool: True if successful
        """
        # Convert session to dict if it's a StudySession object
        if isinstance(session, StudySession):
            session_dict = session.to_dict()
        else:
            session_dict = session
            
        # Get existing history
        history = self.json_storage.load("history", user_id) or {
            "user_id": user_id,
            "sessions": []
        }
        
        # Update existing session or add new one
        found = False
        for i, existing in enumerate(history["sessions"]):
            if existing.get("id") == session_dict["id"]:
                history["sessions"][i] = session_dict
                found = True
                break
                
        if not found:
            history["sessions"].append(session_dict)
            
        # Update statistics
        self._update_statistics(history)
        
        # Save updated history
        return self.json_storage.save("history", user_id, history)
        
    def get_user_history(self, user_id, start_date=None, end_date=None, status=None):
        """
        Get historical study sessions for a user
        
        Args:
            user_id (str): User identifier
            start_date (date, optional): Start date for filtering
            end_date (date, optional): End date for filtering
            status (str, optional): Filter by status (completed, scheduled, cancelled)
            
        Returns:
            list: List of study sessions
        """
        history = self.json_storage.load("history", user_id) or {
            "user_id": user_id,
            "sessions": []
        }
        
        sessions = history.get("sessions", [])
        
        # Apply filters
        filtered_sessions = []
        for session in sessions:
            # Parse start time
            session_start = None
            if session.get("start_time"):
                try:
                    session_start = datetime.fromisoformat(session["start_time"])
                except (ValueError, TypeError):
                    continue
                    
            # Filter by date range
            if start_date and session_start and session_start.date() < start_date:
                continue
                
            if end_date and session_start and session_start.date() > end_date:
                continue
                
            # Filter by status
            if status and session.get("status") != status:
                continue
                
            filtered_sessions.append(session)
            
        return filtered_sessions
        
    def get_statistics(self, user_id, period="month"):
        """
        Calculate statistics for study sessions
        
        Args:
            user_id (str): User identifier
            period (str, optional): Period for statistics (week, month, year, all)
            
        Returns:
            dict: Statistics data
        """
        # Get history with pre-calculated statistics
        history = self.json_storage.load("history", user_id) or {
            "user_id": user_id,
            "sessions": [],
            "statistics": {}
        }
        
        # If statistics are missing, calculate them
        if "statistics" not in history:
            self._update_statistics(history)
            self.json_storage.save("history", user_id, history)
            
        # Get base statistics
        stats = history.get("statistics", {})
        
        # Filter sessions by period
        today = datetime.now().date()
        
        if period == "week":
            start_date = today - timedelta(days=today.weekday())
        elif period == "month":
            start_date = today.replace(day=1)
        elif period == "year":
            start_date = today.replace(month=1, day=1)
        else:  # all
            start_date = None
            
        # Get filtered sessions
        filtered_sessions = self.get_user_history(
            user_id, start_date=start_date, status="completed"
        )
        
        # Calculate period-specific statistics
        period_stats = self._calculate_statistics(filtered_sessions)
        
        # Combine with overall statistics
        combined_stats = {
            "period": period,
            "period_stats": period_stats,
            "overall_stats": stats
        }
        
        return combined_stats
        
    def export_history(self, user_id, format="csv"):
        """
        Export study session history
        
        Args:
            user_id (str): User identifier
            format (str, optional): Export format (csv, json)
            
        Returns:
            str: Exported data
        """
        sessions = self.get_user_history(user_id)
        
        if format == "json":
            import json
            return json.dumps(sessions, indent=2)
        else:  # csv
            import csv
            import io
            
            output = io.StringIO()
            fieldnames = [
                "id", "title", "start_time", "end_time", "duration",
                "status", "provider", "topics", "notes"
            ]
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for session in sessions:
                # Prepare row data
                row = {field: session.get(field, "") for field in fieldnames}
                
                # Format topics list
                if "topics" in row and isinstance(row["topics"], list):
                    row["topics"] = ", ".join(row["topics"])
                    
                writer.writerow(row)
                
            return output.getvalue()
            
    def _update_statistics(self, history):
        """
        Update statistics in the history object
        
        Args:
            history (dict): History data to update
        """
        sessions = history.get("sessions", [])
        
        # Calculate statistics
        stats = self._calculate_statistics(sessions)
        
        # Add to history
        history["statistics"] = stats
        
    def _calculate_statistics(self, sessions):
        """
        Calculate statistics from a list of sessions
        
        Args:
            sessions (list): List of session dictionaries
            
        Returns:
            dict: Statistics data
        """
        # Filter completed sessions
        completed_sessions = [s for s in sessions if s.get("status") == "completed"]
        
        # Basic counts
        total_sessions = len(completed_sessions)
        total_duration = sum(s.get("duration", 0) for s in completed_sessions)
        total_hours = round(total_duration / 60, 1) if total_duration else 0
        
        # Calculate weekly average
        sessions_by_week = defaultdict(list)
        for session in completed_sessions:
            if session.get("start_time"):
                try:
                    start_time = datetime.fromisoformat(session["start_time"])
                    week_key = f"{start_time.year}-{start_time.isocalendar()[1]}"
                    sessions_by_week[week_key].append(session)
                except (ValueError, TypeError):
                    continue
                    
        weekly_counts = [len(sessions) for sessions in sessions_by_week.values()]
        weekly_durations = [
            sum(s.get("duration", 0) for s in sessions) 
            for sessions in sessions_by_week.values()
        ]
        
        weekly_avg_sessions = round(sum(weekly_counts) / len(weekly_counts), 1) if weekly_counts else 0
        weekly_avg_hours = round(sum(weekly_durations) / len(weekly_durations) / 60, 1) if weekly_durations else 0
        
        # Calculate daily distribution
        daily_distribution = [0] * 7  # Monday to Sunday
        for session in completed_sessions:
            if session.get("start_time"):
                try:
                    start_time = datetime.fromisoformat(session["start_time"])
                    weekday = start_time.weekday()
                    daily_distribution[weekday] += 1
                except (ValueError, TypeError):
                    continue
                    
        # Calculate time of day distribution
        morning_count = 0  # 5:00 - 12:00
        afternoon_count = 0  # 12:00 - 17:00
        evening_count = 0  # 17:00 - 22:00
        night_count = 0  # 22:00 - 5:00
        
        for session in completed_sessions:
            if session.get("start_time"):
                try:
                    start_time = datetime.fromisoformat(session["start_time"])
                    hour = start_time.hour
                    
                    if 5 <= hour < 12:
                        morning_count += 1
                    elif 12 <= hour < 17:
                        afternoon_count += 1
                    elif 17 <= hour < 22:
                        evening_count += 1
                    else:
                        night_count += 1
                except (ValueError, TypeError):
                    continue
                    
        # Compile statistics
        return {
            "total_sessions": total_sessions,
            "total_hours": total_hours,
            "weekly_average": {
                "sessions": weekly_avg_sessions,
                "hours": weekly_avg_hours
            },
            "daily_distribution": {
                "monday": daily_distribution[0],
                "tuesday": daily_distribution[1],
                "wednesday": daily_distribution[2],
                "thursday": daily_distribution[3],
                "friday": daily_distribution[4],
                "saturday": daily_distribution[5],
                "sunday": daily_distribution[6]
            },
            "time_distribution": {
                "morning": morning_count,
                "afternoon": afternoon_count,
                "evening": evening_count,
                "night": night_count
            }
        }
