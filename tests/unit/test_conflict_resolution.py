import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.sync_tool import resolve_conflict # This will be implemented later
from src.ocr_processor import ParsedEvent

def test_resolve_conflict_outlook_wins():
    # This test will initially fail as resolve_conflict is not yet implemented

    outlook_event = ParsedEvent(
        original_source_id="outlook_123",
        start_datetime="2025-09-23T10:00:00",
        end_datetime="2025-09-23T11:00:00",
        title="Outlook Meeting",
        location="Outlook Room",
        description="Outlook description",
        confidence_score=0.9
    )

    caldav_event_ical = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Example Corp//Calendar Sync//EN
BEGIN:VEVENT
UID:caldav_456
DTSTAMP:20250923T090000Z
DTSTART:20250923T090000Z
DTEND:20250923T100000Z
SUMMARY:CalDAV Event
LOCATION:CalDAV Room
DESCRIPTION:CalDAV description
END:VEVENT
END:VCALENDAR
"""

    resolved_event = resolve_conflict(outlook_event, caldav_event_ical)
    assert resolved_event.title == outlook_event.title
    assert resolved_event.location == outlook_event.location
    assert resolved_event.description == outlook_event.description
