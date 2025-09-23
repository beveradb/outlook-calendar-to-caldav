import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
import requests_mock
from src.caldav_client import CalDAVClient

# Mock CalDAV server URL for testing
MOCK_CALDAV_URL = "http://localhost:8000/calendars/user/calendar/"

@pytest.fixture
def caldav_client():
    return CalDAVClient(MOCK_CALDAV_URL, "testuser", "testpass")

def test_put_caldav_event_contract(caldav_client):
    with requests_mock.Mocker() as m:
        # Mock a successful PUT response
        m.put(f"{MOCK_CALDAV_URL}test_uid.ics", headers={'Content-Type': 'text/calendar; charset=utf-8'}, status_code=201)

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

        response = caldav_client.put_event("test_uid", ical_data)

        assert response.status_code == 201
        assert m.called_once
        assert m.last_request.text == ical_data
