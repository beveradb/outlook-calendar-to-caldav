import pytest
import os
import json
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.config import Config

# Define a temporary config file path for testing
TEST_CONFIG_FILE = "test_config.json"

@pytest.fixture(autouse=True)
def cleanup_test_config_file():
    # Ensure the test config file is removed before and after each test
    if os.path.exists(TEST_CONFIG_FILE):
        os.remove(TEST_CONFIG_FILE)
    yield
    if os.path.exists(TEST_CONFIG_FILE):
        os.remove(TEST_CONFIG_FILE)

def create_test_config(data):
    with open(TEST_CONFIG_FILE, 'w') as f:
        json.dump(data, f)

def test_config_load_from_file_success():
    config_data = {
        "caldav_url": "http://localhost:8000/caldav/",
        "caldav_username": "testuser",
        "caldav_password": "testpass",
        "outlook_calendar_name": "Calendar",
        "sync_state_filepath": "specs/002-synchronise-outlook-work/sync_state.json"
    }
    create_test_config(config_data)
    
    config = Config.load_from_file(TEST_CONFIG_FILE)
    
    assert config.caldav_url == config_data["caldav_url"]
    assert config.caldav_username == config_data["caldav_username"]
    assert config.caldav_password == config_data["caldav_password"]
    assert config.outlook_calendar_name == config_data["outlook_calendar_name"]
    assert config.sync_interval_minutes == 15 # Default value
    assert config.log_level == "INFO" # Default value

def test_config_load_from_file_missing_field():
    config_data = {
        "caldav_url": "http://localhost:8000/caldav/",
        "caldav_username": "testuser",
        "caldav_password": "testpass"
        # Missing "outlook_calendar_name"
    }
    create_test_config(config_data)
    
    with pytest.raises(ValueError, match="Missing required configuration field: outlook_calendar_name"):
        Config.load_from_file(TEST_CONFIG_FILE)

def test_config_load_from_file_not_found():
    with pytest.raises(FileNotFoundError, match=f"Config file not found at {TEST_CONFIG_FILE}"):
        Config.load_from_file(TEST_CONFIG_FILE)

def test_config_load_from_file_invalid_json():
    with open(TEST_CONFIG_FILE, 'w') as f:
        f.write("{\"caldav_url\": \"invalid json") # Malformed JSON
    
    with pytest.raises(ValueError, match="Invalid JSON in config file"):
        Config.load_from_file(TEST_CONFIG_FILE)

def test_config_save_to_file():
    config = Config(
        caldav_url="http://localhost:8000/caldav/",
        caldav_username="testuser",
        caldav_password="testpass",
        outlook_calendar_name="Calendar",
        sync_interval_minutes=30,
        log_level="DEBUG",
        sync_state_filepath="specs/002-synchronise-outlook-work/sync_state.json"
    )
    config.save_to_file(TEST_CONFIG_FILE)
    
    with open(TEST_CONFIG_FILE, 'r') as f:
        saved_data = json.load(f)
        
    assert saved_data["caldav_url"] == config.caldav_url
    assert saved_data["caldav_username"] == config.caldav_username
    assert saved_data["caldav_password"] == config.caldav_password
    assert saved_data["outlook_calendar_name"] == config.outlook_calendar_name
    assert saved_data["sync_interval_minutes"] == config.sync_interval_minutes
    assert saved_data["log_level"] == config.log_level
    assert saved_data["sync_state_filepath"] == config.sync_state_filepath
