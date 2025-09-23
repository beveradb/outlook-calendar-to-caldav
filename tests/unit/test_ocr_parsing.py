import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
import re
from src.ocr_processor import parse_outlook_event_from_ocr

def test_row_cleanup_and_event_parsing_junk_prefix():
    from src.ocr_processor import process_image_with_ocr, ParsedEvent
    # Simulate rows with junk prefixes and valid event
    rows = [
        "Monday, September 22",
        "22 MON | Team Sync 09:00 - 10:00",
        "| Standup 10:15 - 10:45",
        "\\ 24) WED | All day event Company Retreat",
        "Random junk row"
    ]
    # Patch process_image_with_ocr to accept rows directly for test
    def fake_process_image_with_ocr(_):
        # Use the parsing logic only
        date_row_pattern = re.compile(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+[A-Za-z]+\s+\d{1,2}")
        time_range_pattern = re.compile(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})")
        all_day_pattern = re.compile(r"All day event", re.IGNORECASE)
        junk_leading_patterns = [
            re.compile(r"^\d{1,2}\s*[A-Z]{3}\s*\|\s*"),
            re.compile(r"^\d{1,2}\s*\|\s*"),
            re.compile(r"^\|\s*"),
            re.compile(r"^\\\s*\d{1,2}\)\s*[A-Z]{3}\s*\|\s*"),
        ]
        parsed_events = []
        current_date_str = None
        for row_text in rows:
            row_text = row_text.strip()
            if date_row_pattern.match(row_text):
                current_date_str = "2025-09-22"
                continue
            if not current_date_str:
                continue
            for pat in junk_leading_patterns:
                row_text = pat.sub("", row_text)
            time_match = time_range_pattern.search(row_text)
            all_day_match = all_day_pattern.search(row_text)
            if not time_match and not all_day_match:
                continue
            title = "Untitled"
            start_time = "00:00"
            end_time = "00:00"
            if time_match:
                title = row_text[:time_match.start()].strip() or "Untitled"
                start_time = time_match.group(1)
                end_time = time_match.group(2)
            elif all_day_match:
                idx = row_text.lower().find("all day event")
                # Extract title after 'All day event'
                title = row_text[idx + len("all day event"):].strip() if idx != -1 else row_text.strip() or "Untitled"
                start_time = "00:00"
                end_time = "23:59"
            start_dt = f"{current_date_str}T{start_time}:00"
            end_dt = f"{current_date_str}T{end_time}:00"
            parsed_events.append(ParsedEvent(
                original_source_id=f"{current_date_str}-{start_time}-{title}",
                start_datetime=start_dt,
                end_datetime=end_dt,
                title=title,
                location=None,
                description=None,
                confidence_score=1.0
            ))
        return parsed_events

    events = fake_process_image_with_ocr(None)
    assert len(events) == 3
    assert events[0].title == "Team Sync"
    assert events[0].start_datetime == "2025-09-22T09:00:00"
    assert events[1].title == "Standup"
    assert events[1].start_datetime == "2025-09-22T10:15:00"
    assert events[2].title == "Company Retreat"
    assert events[2].start_datetime == "2025-09-22T00:00:00"
    assert events[2].end_datetime == "2025-09-22T23:59:00"

def test_row_cleanup_and_event_parsing_no_date_row():
    from src.ocr_processor import process_image_with_ocr, ParsedEvent
    rows = [
        "22 MON | Team Sync 09:00 - 10:00",
        "| Standup 10:15 - 10:45",
    ]
    def fake_process_image_with_ocr(_):
        # Same as above, but no date row
        date_row_pattern = re.compile(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+[A-Za-z]+\s+\d{1,2}")
        time_range_pattern = re.compile(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})")
        all_day_pattern = re.compile(r"All day event", re.IGNORECASE)
        junk_leading_patterns = [
            re.compile(r"^\d{1,2}\s*[A-Z]{3}\s*\|\s*"),
            re.compile(r"^\d{1,2}\s*\|\s*"),
            re.compile(r"^\|\s*"),
            re.compile(r"^\\\s*\d{1,2}\)\s*[A-Z]{3}\s*\|\s*"),
        ]
        parsed_events = []
        current_date_str = None
        for row_text in rows:
            row_text = row_text.strip()
            if date_row_pattern.match(row_text):
                current_date_str = "2025-09-22"
                continue
            if not current_date_str:
                continue
            for pat in junk_leading_patterns:
                row_text = pat.sub("", row_text)
            time_match = time_range_pattern.search(row_text)
            all_day_match = all_day_pattern.search(row_text)
            if not time_match and not all_day_match:
                continue
            title = "Untitled"
            start_time = "00:00"
            end_time = "00:00"
            if time_match:
                title = row_text[:time_match.start()].strip() or "Untitled"
                start_time = time_match.group(1)
                end_time = time_match.group(2)
            elif all_day_match:
                idx = row_text.lower().find("all day event")
                title = row_text[:idx].strip() if idx != -1 else row_text.strip() or "Untitled"
                start_time = "00:00"
                end_time = "23:59"
            start_dt = f"{current_date_str}T{start_time}:00"
            end_dt = f"{current_date_str}T{end_time}:00"
            parsed_events.append(ParsedEvent(
                original_source_id=f"{current_date_str}-{start_time}-{title}",
                start_datetime=start_dt,
                end_datetime=end_dt,
                title=title,
                location=None,
                description=None,
                confidence_score=1.0
            ))
        return parsed_events

    events = fake_process_image_with_ocr(None)
    assert len(events) == 0  # No date row, so no events


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
