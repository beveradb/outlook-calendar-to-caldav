import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from src.ocr_processor import parse_outlook_event_from_ocr

def test_parse_outlook_event_from_ocr_basic():
    # Simulate OCR output for a basic event
    ocr_text = """
    Today
    10:00 AM - 11:00 AM Meeting with John
    Conference Room 3
    Project discussion
    """
    
    event = parse_outlook_event_from_ocr(ocr_text, "2025-09-22")
    
    assert event.start_datetime == "2025-09-22T10:00:00"
    assert event.end_datetime == "2025-09-22T11:00:00"
    assert event.title == "Meeting with John"
    assert event.location == "Conference Room 3"
    assert event.description == "Project discussion"
    assert event.confidence_score > 0  # Assuming some confidence score is set

def test_parse_outlook_event_from_ocr_no_location_description():
    # Simulate OCR output for an event without location or description
    ocr_text = """
    Today
    02:00 PM - 03:00 PM Quick Sync
    """
    
    event = parse_outlook_event_from_ocr(ocr_text, "2025-09-22")
    
    assert event.start_datetime == "2025-09-22T14:00:00"
    assert event.end_datetime == "2025-09-22T15:00:00"
    assert event.title == "Quick Sync"
    assert event.location is None
    assert event.description is None

def test_parse_outlook_event_from_ocr_multi_line_description():
    # Simulate OCR output for an event with a multi-line description
    ocr_text = """
    Today
    04:00 PM - 05:00 PM Team Standup
    Daily check-in
    Discuss blockers
    """
    
    event = parse_outlook_event_from_ocr(ocr_text, "2025-09-22")
    
    assert event.start_datetime == "2025-09-22T16:00:00"
    assert event.end_datetime == "2025-09-22T17:00:00"
    assert event.title == "Team Standup"
    assert event.location is None
    assert event.description == "Daily check-in\nDiscuss blockers"

def test_parse_outlook_event_from_ocr_all_day_event():
    # Simulate OCR output for an all-day event (no time range)
    ocr_text = """
    Today
    All Day Holiday
    """
    
    event = parse_outlook_event_from_ocr(ocr_text, "2025-09-22")
    
    assert event.start_datetime == "2025-09-22T00:00:00"
    assert event.end_datetime == "2025-09-22T23:59:59"
    assert event.title == "Holiday"
    assert event.location is None
    assert event.description is None

def test_parse_outlook_event_from_ocr_different_date_format():
    # Simulate OCR output with a different date format (should still use provided date)
    ocr_text = """
    Tomorrow
    09:00 AM - 10:00 AM Project X Planning
    """
    
    event = parse_outlook_event_from_ocr(ocr_text, "2025-09-23")
    
    assert event.start_datetime == "2025-09-23T09:00:00"
    assert event.end_datetime == "2025-09-23T10:00:00"
    assert event.title == "Project X Planning"

def test_parse_outlook_event_from_ocr_invalid_time_format():
    # Simulate OCR output with an invalid time format
    ocr_text = """
    Today
    10:00 - 11:00 Meeting
    """
    
    with pytest.raises(ValueError, match="Could not parse time"): # Expecting a ValueError for now
        parse_outlook_event_from_ocr(ocr_text, "2025-09-22")

def test_parse_outlook_event_from_ocr_empty_input():
    # Simulate empty OCR input
    ocr_text = """
    """
    
    event = parse_outlook_event_from_ocr(ocr_text, "2025-09-22")
    assert event is None
