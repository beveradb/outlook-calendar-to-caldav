
from dataclasses import dataclass, field
from datetime import date
import json
import os

@dataclass
class ParsedEvent:
    """
    Represents a calendar event parsed from Outlook (via OCR).
    Attributes:
        start_datetime: ISO 8601 string for event start.
        end_datetime: ISO 8601 string for event end.
        title: Event title/summary.
        location: Optional location string.
        description: Optional event description.
        confidence_score: Heuristic confidence in the OCR parse (0.0-1.0).
        _ical_timezone: Timezone for iCalendar output (default: "America/New_York").
    """
    start_datetime: str
    end_datetime: str
    title: str
    location: str | None = None
    description: str | None = None
    confidence_score: float = 0.0
    _ical_timezone: str = "America/New_York"


@dataclass
class WeekExtraction:
    """
    Events read from one Outlook week capture, plus the date range the capture shows.
    range_start/range_end are None when the visible date range could not be read; such a
    capture must never be used to delete events.
    """
    range_start: "date | None"
    range_end: "date | None"
    events: list = field(default_factory=list)
