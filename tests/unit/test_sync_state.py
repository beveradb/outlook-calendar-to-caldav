import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.models.calendar_data import SyncState # This will be implemented later

def test_sync_state_is_idempotent():
    # This test will initially fail as SyncState is not yet implemented

    # Expected behavior (commented out for now)
    sync_state = SyncState("test_path.json")
    # Simulate initial sync
    sync_state.record_sync("outlook_event_1", "caldav_event_1")
    assert sync_state.get_caldav_id("outlook_event_1") == "caldav_event_1"

    # Simulate re-sync with same data (should be idempotent)
    sync_state.record_sync("outlook_event_1", "caldav_event_1")
    assert sync_state.get_caldav_id("outlook_event_1") == "caldav_event_1"

    # Simulate update to an event
    sync_state.record_sync("outlook_event_1", "caldav_event_1_updated")
    assert sync_state.get_caldav_id("outlook_event_1") == "caldav_event_1_updated"

    # Simulate new event
    sync_state.record_sync("outlook_event_2", "caldav_event_2")
    assert sync_state.get_caldav_id("outlook_event_2") == "caldav_event_2"
