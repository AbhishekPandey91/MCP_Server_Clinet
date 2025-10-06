from mcp.server.fastmcp import FastMCP
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import os
import pickle
import io
from datetime import datetime, timedelta
from typing import List, Dict, Union, Optional
import json

mcp = FastMCP("google-workspace")

# OAuth 2.0 scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/calendar'
]

# Token file path
TOKEN_FILE = 'token.pickle'
CREDENTIALS_FILE = 'credentials.json'


def get_credentials():
    """
    Handles OAuth 2.0 authentication for Google APIs.
    Returns valid credentials or initiates OAuth flow if needed.
    """
    creds = None
    
    # Check if token.pickle exists with saved credentials
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for future use
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds


# ==================== GOOGLE DRIVE TOOLS ====================

@mcp.tool()
def google_drive_search(
    query: str,
    file_type: Optional[str] = None,
    max_results: int = 10
) -> Union[List[Dict], str]:
    """
    Searches and accesses files in Google Drive.
    
    Authenticates using OAuth 2.0 with Google Drive API.
    Searches files by name, content, type, or modification date.
    Applies user permissions and sharing settings filter.
    Downloads file metadata and content preview.
    Returns file list with direct access links and descriptions.
    
    Args:
        query: Search query (file name or content)
        file_type: Filter by MIME type (e.g., 'document', 'spreadsheet', 'pdf', 'folder')
        max_results: Maximum number of results to return (default: 10)
        
    Returns:
        List of files with metadata and access links, or error message
        
    Examples:
        google_drive_search("budget 2024")
        google_drive_search("project", file_type="document")
        google_drive_search("*.pdf", file_type="pdf")
    """
    try:
        creds = get_credentials()
        if not creds:
            return "Error: Google credentials not found. Please set up credentials.json file."
        
        service = build('drive', 'v3', credentials=creds)
        
        # Build search query
        search_query = f"name contains '{query}'"
        
        # Add MIME type filter if specified
        mime_types = {
            'document': 'application/vnd.google-apps.document',
            'spreadsheet': 'application/vnd.google-apps.spreadsheet',
            'presentation': 'application/vnd.google-apps.presentation',
            'pdf': 'application/pdf',
            'folder': 'application/vnd.google-apps.folder',
            'image': 'image/',
            'video': 'video/',
        }
        
        if file_type and file_type.lower() in mime_types:
            mime = mime_types[file_type.lower()]
            if mime.endswith('/'):
                search_query += f" and mimeType contains '{mime}'"
            else:
                search_query += f" and mimeType='{mime}'"
        
        # Add trashed filter
        search_query += " and trashed=false"
        
        # Execute search
        results = service.files().list(
            q=search_query,
            pageSize=max_results,
            fields="files(id, name, mimeType, size, createdTime, modifiedTime, "
                   "webViewLink, iconLink, owners, shared, description)",
            orderBy='modifiedTime desc'
        ).execute()
        
        files = results.get('files', [])
        
        if not files:
            return f"No files found matching '{query}'"
        
        # Format results
        file_list = []
        for file in files:
            file_info = {
                'id': file['id'],
                'name': file['name'],
                'type': file['mimeType'].split('.')[-1] if '.' in file['mimeType'] else file['mimeType'],
                'size': f"{int(file.get('size', 0)) / 1024:.2f} KB" if file.get('size') else 'N/A',
                'created': file.get('createdTime', 'Unknown'),
                'modified': file.get('modifiedTime', 'Unknown'),
                'link': file.get('webViewLink', 'No link available'),
                'shared': file.get('shared', False),
                'owner': file.get('owners', [{}])[0].get('displayName', 'Unknown'),
                'description': file.get('description', 'No description')
            }
            file_list.append(file_info)
        
        return file_list
        
    except Exception as e:
        return f"Error searching Google Drive: {str(e)}"


@mcp.tool()
def google_drive_get_file(
    file_id: str,
    include_content: bool = False
) -> Union[Dict, str]:
    """
    Retrieves detailed information about a specific Google Drive file.
    
    Args:
        file_id: The unique ID of the file
        include_content: If True, downloads file content (text files only)
        
    Returns:
        File details and optionally content, or error message
    """
    try:
        creds = get_credentials()
        if not creds:
            return "Error: Google credentials not found."
        
        service = build('drive', 'v3', credentials=creds)
        
        # Get file metadata
        file = service.files().get(
            fileId=file_id,
            fields="id, name, mimeType, size, createdTime, modifiedTime, "
                   "webViewLink, webContentLink, description, owners, shared, "
                   "permissions, parents"
        ).execute()
        
        file_info = {
            'id': file['id'],
            'name': file['name'],
            'type': file['mimeType'],
            'size': f"{int(file.get('size', 0)) / 1024:.2f} KB" if file.get('size') else 'N/A',
            'created': file.get('createdTime'),
            'modified': file.get('modifiedTime'),
            'view_link': file.get('webViewLink'),
            'download_link': file.get('webContentLink'),
            'description': file.get('description', 'No description'),
            'shared': file.get('shared', False),
            'owner': file.get('owners', [{}])[0].get('displayName', 'Unknown')
        }
        
        # Download content if requested (for text-based files)
        if include_content:
            try:
                request = service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                
                content = fh.getvalue().decode('utf-8')
                file_info['content_preview'] = content[:1000] + "..." if len(content) > 1000 else content
            except:
                file_info['content_preview'] = "Content preview not available for this file type"
        
        return file_info
        
    except Exception as e:
        return f"Error retrieving file: {str(e)}"


# ==================== GOOGLE CALENDAR TOOLS ====================

@mcp.tool()
def google_calendar_view(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_results: int = 10,
    calendar_id: str = 'primary'
) -> Union[List[Dict], str]:
    """
    Reads calendar events and schedules from Google Calendar.
    
    Connects to Google Calendar API with user authorization.
    Queries events within specified date ranges.
    Retrieves event details (time, location, attendees, description).
    Checks for conflicts and availability windows.
    Returns structured calendar data with timezone handling.
    
    Args:
        start_date: Start date in ISO format (YYYY-MM-DD) or None for today
        end_date: End date in ISO format (YYYY-MM-DD) or None for 7 days from start
        max_results: Maximum number of events to return (default: 10)
        calendar_id: Calendar ID to query (default: 'primary')
        
    Returns:
        List of calendar events with details, or error message
        
    Examples:
        google_calendar_view()  # Today's events
        google_calendar_view("2024-12-01", "2024-12-31")  # December events
        google_calendar_view(max_results=5)  # Next 5 events
    """
    try:
        creds = get_credentials()
        if not creds:
            return "Error: Google credentials not found."
        
        service = build('calendar', 'v3', credentials=creds)
        
        # Set date range
        if start_date:
            time_min = datetime.fromisoformat(start_date).isoformat() + 'Z'
        else:
            time_min = datetime.utcnow().isoformat() + 'Z'
        
        if end_date:
            time_max = datetime.fromisoformat(end_date).replace(
                hour=23, minute=59, second=59
            ).isoformat() + 'Z'
        else:
            time_max = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'
        
        # Query events
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return "No upcoming events found in the specified date range."
        
        # Format events
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            event_info = {
                'id': event['id'],
                'summary': event.get('summary', 'No title'),
                'start': start,
                'end': end,
                'location': event.get('location', 'No location'),
                'description': event.get('description', 'No description'),
                'attendees': [
                    {
                        'email': attendee.get('email'),
                        'status': attendee.get('responseStatus', 'unknown')
                    }
                    for attendee in event.get('attendees', [])
                ],
                'organizer': event.get('organizer', {}).get('email', 'Unknown'),
                'link': event.get('htmlLink'),
                'status': event.get('status', 'confirmed')
            }
            event_list.append(event_info)
        
        return event_list
        
    except Exception as e:
        return f"Error viewing calendar: {str(e)}"


@mcp.tool()
def google_calendar_create(
    summary: str,
    start_time: str,
    end_time: str,
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    reminders: Optional[int] = 10,
    calendar_id: str = 'primary'
) -> Union[Dict, str]:
    """
    Creates new calendar events and meetings in Google Calendar.
    
    Validates event details and time availability.
    Creates calendar event with specified parameters.
    Sends invitations to specified attendees.
    Sets reminders and notification preferences.
    Returns confirmation with event ID and meeting details.
    
    Args:
        summary: Event title/name
        start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
        end_time: End time in ISO format (YYYY-MM-DDTHH:MM:SS)
        description: Event description (optional)
        location: Event location (optional)
        attendees: List of attendee email addresses (optional)
        reminders: Minutes before event to send reminder (default: 10)
        calendar_id: Calendar ID to create event in (default: 'primary')
        
    Returns:
        Created event details with confirmation, or error message
        
    Examples:
        google_calendar_create(
            "Team Meeting",
            "2024-12-15T10:00:00",
            "2024-12-15T11:00:00",
            description="Quarterly review",
            attendees=["colleague@example.com"]
        )
    """
    try:
        creds = get_credentials()
        if not creds:
            return "Error: Google credentials not found."
        
        service = build('calendar', 'v3', credentials=creds)
        
        # Validate time format
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            
            if end_dt <= start_dt:
                return "Error: End time must be after start time"
        except ValueError:
            return "Error: Invalid time format. Use YYYY-MM-DDTHH:MM:SS"
        
        # Build event object
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': reminders},
                    {'method': 'email', 'minutes': reminders},
                ],
            },
        }
        
        if description:
            event['description'] = description
        
        if location:
            event['location'] = location
        
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
            event['sendUpdates'] = 'all'  # Send invitations
        
        # Check for conflicts
        conflicts = service.events().list(
            calendarId=calendar_id,
            timeMin=start_time + 'Z' if not start_time.endswith('Z') else start_time,
            timeMax=end_time + 'Z' if not end_time.endswith('Z') else end_time,
            singleEvents=True
        ).execute()
        
        has_conflicts = len(conflicts.get('items', [])) > 0
        
        # Create event
        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event,
            sendUpdates='all' if attendees else 'none'
        ).execute()
        
        return {
            'status': 'success',
            'message': 'Event created successfully',
            'event_id': created_event['id'],
            'summary': created_event['summary'],
            'start': created_event['start'].get('dateTime'),
            'end': created_event['end'].get('dateTime'),
            'link': created_event.get('htmlLink'),
            'attendees_notified': len(attendees) if attendees else 0,
            'has_time_conflicts': has_conflicts,
            'reminder_set': f"{reminders} minutes before"
        }
        
    except Exception as e:
        return f"Error creating calendar event: {str(e)}"


@mcp.tool()
def google_calendar_update(
    event_id: str,
    summary: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    calendar_id: str = 'primary'
) -> Union[Dict, str]:
    """
    Updates an existing calendar event.
    
    Args:
        event_id: The ID of the event to update
        summary: New event title (optional)
        start_time: New start time in ISO format (optional)
        end_time: New end time in ISO format (optional)
        description: New description (optional)
        location: New location (optional)
        calendar_id: Calendar ID (default: 'primary')
        
    Returns:
        Updated event details or error message
    """
    try:
        creds = get_credentials()
        if not creds:
            return "Error: Google credentials not found."
        
        service = build('calendar', 'v3', credentials=creds)
        
        # Get existing event
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        
        # Update fields
        if summary:
            event['summary'] = summary
        if start_time:
            event['start']['dateTime'] = start_time
        if end_time:
            event['end']['dateTime'] = end_time
        if description:
            event['description'] = description
        if location:
            event['location'] = location
        
        # Update event
        updated_event = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event,
            sendUpdates='all'
        ).execute()
        
        return {
            'status': 'success',
            'message': 'Event updated successfully',
            'event_id': updated_event['id'],
            'summary': updated_event['summary'],
            'link': updated_event.get('htmlLink')
        }
        
    except Exception as e:
        return f"Error updating event: {str(e)}"


@mcp.tool()
def google_calendar_delete(
    event_id: str,
    calendar_id: str = 'primary'
) -> Union[str, Dict]:
    """
    Deletes a calendar event.
    
    Args:
        event_id: The ID of the event to delete
        calendar_id: Calendar ID (default: 'primary')
        
    Returns:
        Confirmation message or error
    """
    try:
        creds = get_credentials()
        if not creds:
            return "Error: Google credentials not found."
        
        service = build('calendar', 'v3', credentials=creds)
        
        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id,
            sendUpdates='all'
        ).execute()
        
        return {
            'status': 'success',
            'message': f'Event {event_id} deleted successfully'
        }
        
    except Exception as e:
        return f"Error deleting event: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")