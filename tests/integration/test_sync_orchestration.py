import pytest
import os
import json
import requests_mock
import sys
from datetime import datetime
import builtins # Import builtins

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.sync_tool import sync_outlook_to_caldav
from src.config import Config
from src.ocr_processor import ParsedEvent
from src.caldav_client import CalDAVClient

# Define temporary file paths for testing
TEST_CONFIG_FILE = "test_sync_config.json"
TEST_SCREENSHOT_FILE = "test_outlook_calendar_screenshot.png"

MOCK_CALDAV_URL = "http://localhost:8000/calendars/user/calendar/"

@pytest.fixture(autouse=True)
def cleanup_test_files():
    # Ensure test files are removed before and after each test
    for f in [TEST_CONFIG_FILE, TEST_SCREENSHOT_FILE]:
        if os.path.exists(f):
            os.remove(f)
    yield
    for f in [TEST_CONFIG_FILE, TEST_SCREENSHOT_FILE]:
        if os.path.exists(f):
            os.remove(f)

def create_test_config(caldav_url, username, password, calendar_name):
    config_data = {
        "caldav_url": caldav_url,
        "caldav_username": username,
        "caldav_password": password,
        "outlook_calendar_name": calendar_name
    }
    with open(TEST_CONFIG_FILE, 'w') as f:
        json.dump(config_data, f)

def create_dummy_screenshot(filepath: str, text_content: str):
    # Create a dummy image file that OCR can process
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', (400, 100), color = (255, 255, 255))
    d = ImageDraw.Draw(img)
    try:
        fnt = ImageFont.truetype("Arial.ttf", 20)
    except IOError:
        fnt = ImageFont.load_default()
    d.text((10,10), text_content, fill=(0,0,0), font=fnt)
    img.save(filepath)

def test_sync_outlook_to_caldav_integration_success(mocker):
    # Mock external dependencies
    mocker.patch('src.sync_tool.launch_outlook', return_value=True)
    mocker.patch('src.sync_tool.navigate_to_calendar', return_value=True)
    mocker.patch('src.sync_tool.capture_screenshot', return_value=True)
    mocker.patch('src.sync_tool.process_image_with_ocr', return_value=[ParsedEvent(
        start_datetime="2025-09-23T10:00:00",
        end_datetime="2025-09-23T11:00:00",
        title="Test Event",
        location="Location A",
        description="Description B",
        confidence_score=0.9
    )])
    mocker.patch('src.sync_tool.parse_outlook_event_from_ocr', return_value=ParsedEvent(
        start_datetime="2025-09-23T10:00:00",
        end_datetime="2025-09-23T11:00:00",
        title="Test Event",
        location="Location A",
        description="Description B",
        confidence_score=0.9
    ))


    # Mock CalDAV client interactions
    with requests_mock.Mocker() as m:
        m.put(f"{MOCK_CALDAV_URL}outlook_event_1.ics", status_code=201)
        m.get(MOCK_CALDAV_URL, text='''
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Example Corp//Calendar Sync//EN
END:VCALENDAR
''', status_code=200)
    # Mock REPORT method for CalDAV event search with valid XML multistatus response
    m.register_uri('REPORT', requests_mock.ANY, text='''
<?xml version="1.0" encoding="utf-8"?>
<D:multistatus xmlns:D="DAV:">
</D:multistatus>
''', status_code=207)

    create_test_config(MOCK_CALDAV_URL, "testuser", "testpass", "Calendar")
    # Patch CalDAVClient.get_events to avoid real HTTP requests
    mocker.patch('src.caldav_client.CalDAVClient.get_events', return_value={})
    # Patch CalDAVClient.put_event to return a mock response with status_code=201
    mock_response = mocker.Mock()
    mock_response.status_code = 201
    mocker.patch('src.caldav_client.CalDAVClient.put_event', return_value=mock_response)
    result = sync_outlook_to_caldav(TEST_CONFIG_FILE, "2025-09-23")
    assert result is True

def test_sync_outlook_to_caldav_integration_no_event(mocker):
    mocker.patch('src.sync_tool.launch_outlook', return_value=True)
    mocker.patch('src.sync_tool.navigate_to_calendar', return_value=True)
    mocker.patch('src.sync_tool.capture_screenshot', return_value=True)
    mocker.patch('src.sync_tool.process_image_with_ocr', return_value="")
    mocker.patch('src.sync_tool.parse_outlook_event_from_ocr', return_value=None)

    with requests_mock.Mocker() as m:
        m.get(MOCK_CALDAV_URL, text='''
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Example Corp//Calendar Sync//EN
END:VCALENDAR
''', status_code=200)
    # Mock REPORT method for CalDAV event search with valid XML multistatus response
    m.register_uri('REPORT', requests_mock.ANY, text='''
<?xml version="1.0" encoding="utf-8"?>
<D:multistatus xmlns:D="DAV:">
</D:multistatus>
''', status_code=207)

    create_test_config(MOCK_CALDAV_URL, "testuser", "testpass", "Calendar")
    create_dummy_screenshot(TEST_SCREENSHOT_FILE, "")
    # Patch CalDAVClient.get_events to avoid real HTTP requests
    mocker.patch('src.caldav_client.CalDAVClient.get_events', return_value={})
    result = sync_outlook_to_caldav(TEST_CONFIG_FILE, "2025-09-23")
    assert result is True

def test_sync_outlook_to_caldav_integration_outlook_launch_failure(mocker):
    mocker.patch('src.sync_tool.launch_outlook', return_value=False)

    create_test_config(MOCK_CALDAV_URL, "testuser", "testpass", "Calendar")
    result = sync_outlook_to_caldav(TEST_CONFIG_FILE, "2025-09-23")
    assert result is False

def test_sync_outlook_to_caldav_integration_caldav_put_failure(mocker):
    mocker.patch('src.sync_tool.launch_outlook', return_value=True)
    mocker.patch('src.sync_tool.navigate_to_calendar', return_value=True)
    mocker.patch('src.sync_tool.capture_screenshot', return_value=True)
    mocker.patch('src.sync_tool.process_image_with_ocr', return_value="10:00 AM - 11:00 AM Test Event")
    mocker.patch('src.sync_tool.parse_outlook_event_from_ocr', return_value=ParsedEvent(
        start_datetime="2025-09-23T10:00:00",
        end_datetime="2025-09-23T11:00:00",
        title="Test Event",
        location=None,
        description=None,
        confidence_score=0.9
    ))

    with requests_mock.Mocker() as m:
        m.put(f"{MOCK_CALDAV_URL}outlook_event_1.ics", status_code=500) # Simulate failure
        m.get(MOCK_CALDAV_URL, text='''
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Example Corp//Calendar Sync//EN
END:VCALENDAR
''', status_code=200)

        create_test_config(MOCK_CALDAV_URL, "testuser", "testpass", "Calendar")
        create_dummy_screenshot(TEST_SCREENSHOT_FILE, "Dummy text for OCR")

        result = sync_outlook_to_caldav(TEST_CONFIG_FILE, "2025-09-23")

        assert result is False
