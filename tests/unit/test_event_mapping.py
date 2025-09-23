import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.ocr_processor import ParsedEvent
from src.caldav_client import map_parsed_event_to_ical # This function will be implemented later

def test_map_parsed_event_to_ical_basic_event():
    # This test will initially fail as map_parsed_event_to_ical is not yet implemented
    # and the import is commented out.

    parsed_event = ParsedEvent(
        original_source_id="2025-09-23-10:00 AM-Meeting with John",
        start_datetime="2025-09-23T10:00:00",
        end_datetime="2025-09-23T11:00:00",
        title="Meeting with John",
        location="Conference Room 3",
        description="Project discussion",
        confidence_score=0.9,
        _ical_timezone="UTC"
    )

    # Expected iCalendar output (simplified for contract test)
    expected_ical = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Example Corp//Calendar Sync//EN
BEGIN:VEVENT
UID:2025-09-23-10:00 AM-Meeting with John
DTSTAMP:20250923T100000Z
DTSTART:20250923T100000Z
DTEND:20250923T110000Z
SUMMARY:Meeting with John
LOCATION:Conference Room 3
DESCRIPTION:Project discussion
END:VEVENT
END:VCALENDAR
"""

    ical_output = map_parsed_event_to_ical(parsed_event)
    assert ical_output.strip() == expected_ical.strip()
