
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

@dataclass
class SyncState:
    """
    Tracks mapping of Outlook event IDs to CalDAV event IDs for idempotent syncs.
    Persists state to a JSON file.
    """
    filepath: str
    _synced_events: dict = field(default_factory=dict)

    def __post_init__(self):
        """Load state from file on initialization."""
        self.load_state()

    def load_state(self):
        """Load the sync state from the JSON file, or initialize empty if missing/corrupt."""
        if os.path.exists(self.filepath) and os.path.getsize(self.filepath) > 0:
            try:
                with open(self.filepath, 'r') as f:
                    self._synced_events = json.load(f)
            except json.JSONDecodeError:
                # Handle empty or invalid JSON by starting with an empty state
                self._synced_events = {}
        else:
            self._synced_events = {} # Initialize as empty if file doesn't exist or is empty

    def save_state(self):
        """Persist the current sync state to the JSON file."""
        with open(self.filepath, 'w') as f:
            json.dump(self._synced_events, f, indent=4)

    def record_sync(self, outlook_id: str, caldav_id: str):
        """Record a mapping from Outlook event ID to CalDAV event ID and persist state."""
        self._synced_events[outlook_id] = caldav_id
        self.save_state()

    def get_caldav_id(self, outlook_id: str) -> str | None:
        """Get the CalDAV event ID for a given Outlook event ID, or None if not synced yet."""
        return self._synced_events.get(outlook_id)
