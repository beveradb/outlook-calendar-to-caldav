from dataclasses import dataclass, field
import json
import os

@dataclass
class ParsedEvent:
    original_source_id: str
    start_datetime: str
    end_datetime: str
    title: str
    location: str | None = None
    description: str | None = None
    confidence_score: float = 0.0

@dataclass
class SyncState:
    filepath: str
    _synced_events: dict = field(default_factory=dict)

    def __post_init__(self):
        self.load_state()

    def load_state(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                self._synced_events = json.load(f)

    def save_state(self):
        with open(self.filepath, 'w') as f:
            json.dump(self._synced_events, f, indent=4)

    def record_sync(self, outlook_id: str, caldav_id: str):
        self._synced_events[outlook_id] = caldav_id
        self.save_state()

    def get_caldav_id(self, outlook_id: str) -> str | None:
        return self._synced_events.get(outlook_id)
