#!/usr/bin/env python3
"""
Personal Tracker App - Calendar Integration
Main application entry point
"""
import os
from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from app.web import create_app
from app.services.auth_service import AuthenticationService
from app.services.calendar_service import CalendarService
from app.core.scheduler import SchedulerService
from app.storage.token_store import SecureJsonTokenStorage
from app.storage.json_storage import JsonStorage
from app.providers.outlook import OutlookCalendarProvider
from app.providers.google import GoogleCalendarProvider

def main():
    """Main application entry point"""
    # Initialize storage
    json_storage = JsonStorage(os.path.join(os.path.dirname(__file__), '..', 'data'))
    token_storage = SecureJsonTokenStorage(json_storage)
    
    # Initialize services
    auth_service = AuthenticationService(token_storage)
    calendar_service = CalendarService()
    
    # Register calendar providers
    outlook_provider = OutlookCalendarProvider(auth_service)
    google_provider = GoogleCalendarProvider(auth_service)
    calendar_service.register_provider('outlook', outlook_provider)
    calendar_service.register_provider('google', google_provider)
    
    # Create and configure Flask app
    app = create_app(auth_service, calendar_service)
    
    # Run the app
    app.run(debug=True)

if __name__ == "__main__":
    main()
