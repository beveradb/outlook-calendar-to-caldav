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
    try:
        # You may want to mock file loading if needed
        sync_outlook_to_caldav(config_filepath="config.json", current_date="2025-09-23")
    except Exception:
        pass
    assert patch_pushbullet_notify.sent
    assert "error" in patch_pushbullet_notify.message
