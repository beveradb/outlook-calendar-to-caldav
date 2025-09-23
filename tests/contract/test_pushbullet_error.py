import pytest
from src.lib.pushbullet_notify import send_pushbullet_notification

class DummyResponse:
    def __init__(self, status_code=401, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {}
    def raise_for_status(self):
        raise Exception("Unauthorized: Invalid API key")
    def json(self):
        return self._json_data

# Patch requests.post to simulate Pushbullet API error
@pytest.fixture(autouse=True)
def patch_requests_post_error(monkeypatch):
    def dummy_post(*args, **kwargs):
        return DummyResponse()
    monkeypatch.setattr("requests.post", dummy_post)


def test_pushbullet_error_notification():
    api_key = "bad_key"
    message = "Sync failed with error: test error"
    result = send_pushbullet_notification(api_key, message)
    assert "Unauthorized" in result
