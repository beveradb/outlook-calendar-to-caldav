
from dataclasses import dataclass, field
import json
import os

@dataclass
class ParsedEvent:
    """
    Represents a calendar event parsed from Outlook (via OCR).
    Attributes:
        original_source_id: Unique identifier from the source (e.g., Outlook event ID or generated from OCR).
        start_datetime: ISO 8601 string for event start.
        end_datetime: ISO 8601 string for event end.
        title: Event title/summary.
        location: Optional location string.
        description: Optional event description.
        confidence_score: Heuristic confidence in the OCR parse (0.0-1.0).
        _ical_timezone: Timezone for iCalendar output (default: "America/New_York").
    """
    original_source_id: str
    start_datetime: str
    end_datetime: str
    title: str
    location: str | None = None
    description: str | None = None
    confidence_score: float = 0.0
    _ical_timezone: str = "America/New_York"
