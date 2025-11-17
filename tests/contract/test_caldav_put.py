import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from unittest.mock import Mock, patch
from src.caldav_client import CalDAVClient

# Mock CalDAV server URL for testing
MOCK_CALDAV_URL = "http://localhost:8000/calendars/user/calendar/"

@pytest.fixture
def caldav_client():
    return CalDAVClient(MOCK_CALDAV_URL, "testuser", "testpass")

def test_put_caldav_event_contract(caldav_client):
    """Test that CalDAVClient.put_event sends the correct data to the calendar"""
    
    # Example iCalendar data (minimal for contract test)
    ical_data = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Example Corp//Calendar Sync//EN
BEGIN:VEVENT
UID:test_uid
DTSTAMP:20250922T100000Z
DTSTART:20250922T110000Z
DTEND:20250922T120000Z
SUMMARY:Test Event
END:VEVENT
END:VCALENDAR
"""

    # Mock the calendar.add_event method
    with patch.object(caldav_client.calendar, 'add_event') as mock_add_event:
        # Configure the mock to succeed
        mock_add_event.return_value = Mock()
        
        result = caldav_client.put_event("test_uid", ical_data)
        
        # Verify the result
        assert result is True
        # Verify add_event was called once with the ical data
        mock_add_event.assert_called_once_with(ical_data)
        # Verify the ical data contains expected fields
        args = mock_add_event.call_args[0][0]
        assert "BEGIN:VEVENT" in args
        assert "SUMMARY:Test Event" in args
        assert "UID:test_uid" in args
