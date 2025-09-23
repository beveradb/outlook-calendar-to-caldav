import pytest
from src.lib.pushbullet_notify import send_pushbullet_notification

class DummyResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {"iden": "123abc"}
    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception("HTTP error")
    def json(self):
        return self._json_data

# Patch requests.post to simulate Pushbullet API success
@pytest.fixture(autouse=True)
def patch_requests_post_success(monkeypatch):
    def dummy_post(*args, **kwargs):
        return DummyResponse()
    monkeypatch.setattr("requests.post", dummy_post)


def test_pushbullet_success_notification():
    api_key = "test_key"
    message = "Outlook to CalDAV synced successfully, 5 events created"
    result = send_pushbullet_notification(api_key, message)
    assert result == "123abc"
