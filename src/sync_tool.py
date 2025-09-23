from src.config import Config
from src.outlook_automation import launch_outlook, navigate_to_calendar, capture_screenshot
from src.ocr_processor import process_image_with_ocr, parse_outlook_event_from_ocr
from src.caldav_client import CalDAVClient, map_parsed_event_to_ical
from src.models.calendar_data import SyncState
from src.utils.logger import setup_logging

logger = setup_logging()

def sync_outlook_to_caldav(config_filepath: str, current_date: str) -> bool:
    """Orchestrates the synchronization of Outlook calendar events to CalDAV."""
    try:
        # 1. Load configuration
        config = Config.load_from_file(config_filepath)
        logger.setLevel(config.log_level.upper())
        logger.info("Configuration loaded successfully.")

        # 2. Launch Outlook and navigate to calendar
        logger.info("Launching Outlook and navigating to calendar...")
        if not launch_outlook():
            logger.error("Failed to launch Outlook.")
            return False
        if not navigate_to_calendar():
            logger.error("Failed to navigate to Outlook calendar.")
            return False
        logger.info("Outlook launched and navigated to calendar.")

        # 3. Capture screenshot
        screenshot_path = "outlook_calendar_screenshot.png"
        logger.info(f"Capturing screenshot to {screenshot_path}...")
        if not capture_screenshot(screenshot_path):
            logger.error("Failed to capture screenshot.")
            return False
        logger.info("Screenshot captured.")

        # 4. Process screenshot with OCR to parse events
        logger.info("Processing screenshot with OCR...")
        ocr_text = process_image_with_ocr(screenshot_path)
        parsed_event = parse_outlook_event_from_ocr(ocr_text, current_date)

        if not parsed_event:
            logger.info("No event found in OCR output.")
            return True # No event to sync, consider it a success
        logger.info(f"Parsed event: {parsed_event.title}")

        # 5. Initialize CalDAV client and SyncState
        logger.info("Initializing CalDAV client and SyncState...")
        caldav_client = CalDAVClient(config.caldav_url, config.caldav_username, config.caldav_password)
        sync_state = SyncState(config.sync_state_filepath)
        logger.info("CalDAV client and SyncState initialized.")

        # 6. Fetch existing CalDAV events (simplified for now)
        logger.info("Fetching existing CalDAV events...")
        existing_caldav_events = caldav_client.get_events()
        logger.info(f"Fetched {len(existing_caldav_events)} existing CalDAV events.")

        # 7. Compare and resolve conflicts (Outlook wins)
        ical_data = map_parsed_event_to_ical(parsed_event)

        caldav_uid = sync_state.get_caldav_id(parsed_event.original_source_id)

        if caldav_uid:
            logger.info(f"Updating existing CalDAV event: {caldav_uid}")
            response = caldav_client.put_event(caldav_uid, ical_data)
        else:
            logger.info(f"Creating new CalDAV event for Outlook event: {parsed_event.original_source_id}")
            response = caldav_client.put_event(parsed_event.original_source_id, ical_data)
            caldav_uid = parsed_event.original_source_id # For new events, UID is the outlook_id

        if response.status_code in [200, 201, 204]:
            logger.info(f"Event synced successfully. CalDAV UID: {caldav_uid}")
            # 8. Record sync state
            sync_state.record_sync(parsed_event.original_source_id, caldav_uid)
            logger.info("Sync state recorded.")
            return True
        else:
            logger.error(f"Failed to sync event. Status code: {response.status_code}, Response: {response.text}")
            return False

    except FileNotFoundError as e:
        logger.error(f"Configuration or image file error: {e}")
        return False
    except ValueError as e:
        logger.error(f"Configuration or parsing error: {e}")
        return False
    except RuntimeError as e:
        logger.error(f"Runtime error during sync: {e}")
        return False
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        return False
