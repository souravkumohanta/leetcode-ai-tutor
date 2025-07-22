# Personal Tracker App - Calendar Integration

A scalable Python application that integrates with Outlook and Google calendars to manage study sessions around work hours.

## Features

- OAuth authentication with both Outlook and Google calendars
- Retrieval of busy intervals (meetings/events) from both calendar providers
- Computation of free slots outside work hours
- Proposal of study sessions in available time slots
- Creation and management of "Study Session" events
- Automatic conflict resolution and rescheduling
- Historical tracking of study sessions

## Architecture

The application follows a modular, layered architecture:

- **Web Interface**: Flask-based web application
- **Core Services**: Calendar integration, scheduling, and authentication
- **Providers**: Implementations for Outlook and Google calendar APIs
- **Storage**: Secure JSON-based storage for tokens and application data

## Setup and Installation

### Prerequisites

- Python 3.9 or higher
- Google Cloud project with Calendar API enabled
- Microsoft Azure AD app with Calendar.Read permissions

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/personal-tracker.git
   cd personal-tracker
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your OAuth credentials:
   ```
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   MICROSOFT_CLIENT_ID=your_microsoft_client_id
   MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
   SECRET_KEY=your_flask_secret_key
   ```

### Running the Application

```
python -m app.main
```

The application will be available at http://localhost:5000

## Usage

1. Connect your calendar accounts through the web interface
2. Set your work hours and study preferences
3. Generate study session proposals
4. Review and approve proposed sessions
5. Track your study history and progress

## Security

- OAuth tokens are encrypted at rest using Fernet symmetric encryption
- Sensitive configuration is stored in environment variables
- HTTPS is recommended for production deployments

## Integration

This calendar integration module is designed to be integrated into a larger application. It provides a clean API for:

- Calendar authentication and connection
- Free/busy time retrieval
- Study session scheduling
- Historical data access

## License

MIT
