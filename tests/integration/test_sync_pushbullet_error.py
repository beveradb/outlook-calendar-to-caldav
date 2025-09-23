import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.sync_tool import sync_outlook_to_caldav
from src.config import Config

class DummyPushbullet:
    def __init__(self):
        self.sent = False
        self.message = None
    def send(self, api_key, message, title="Calendar Sync"):
        self.sent = True
        self.message = message
        return "dummy_id"

@pytest.fixture(autouse=True)
def patch_pushbullet_notify(monkeypatch):
    dummy = DummyPushbullet()
    monkeypatch.setattr("src.lib.pushbullet_notify.send_pushbullet_notification", dummy.send)
    return dummy


def test_sync_triggers_pushbullet_error(patch_pushbullet_notify):
    # Prepare config with API key
    config = Config(
        caldav_url="http://localhost:8000/caldav/",
        caldav_username="testuser",
        caldav_password="testpass",
        outlook_calendar_name="Calendar",
        pushbullet_api_key="test_key"
    )
    # Simulate sync error (replace with actual sync logic as needed)
    # For this test, we call sync_outlook_to_caldav with a dummy config file path and date
    # Patch CalDAVClient.delete_event to always fail, triggering error notification
    import src.caldav_client
    def always_fail_delete_event(self, event_url):
        return False
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(src.caldav_client.CalDAVClient, "delete_event", always_fail_delete_event)
    try:
        sync_outlook_to_caldav(config_filepath="config.json", current_date="2025-09-23", notification_func=patch_pushbullet_notify.send)
    except Exception:
        pass
    monkeypatch.undo()
    assert patch_pushbullet_notify.sent
    assert "failed" in patch_pushbullet_notify.message or "error" in patch_pushbullet_notify.message
