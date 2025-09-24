
from src.config import Config
from src.outlook_automation import launch_outlook, navigate_to_calendar, capture_screenshot
from src.ocr_processor import process_image_with_ocr, parse_outlook_event_from_ocr
from src.caldav_client import CalDAVClient, map_parsed_event_to_ical
from src.models.calendar_data import ParsedEvent
from src.utils.logger import setup_logging, log_pushbullet_attempt
from src.lib.pushbullet_notify import send_pushbullet_notification
import time
from typing import Callable, TypeVar
import logging
import urllib3
import uuid

logger = setup_logging()
urllib3.disable_warnings()

R = TypeVar('R')


def _retry(func: Callable[[], R], retries=3, delay=5) -> R:
    """
    Retry a function up to 'retries' times with a delay between attempts.
    Args:
        func: Callable to execute
        retries: Number of attempts
        delay: Seconds to wait between attempts
    Returns:
        Result of func()
    Raises:
        Exception from func() if all retries fail
    """
    for i in range(retries):
        try:
            return func()
        except Exception as e:
            logger.warning(f"Attempt {i+1}/{retries} failed: {e}")
            if i < retries - 1:
                time.sleep(delay)
            else:
                raise # Re-raise the exception on the last attempt
    raise RuntimeError("Function did not return a value after retries.") # Should not be reached


def resolve_conflict(outlook_event: ParsedEvent, caldav_event_ical: str) -> ParsedEvent:
    """
    Resolve a conflict between Outlook and CalDAV events.
    Args:
        outlook_event: ParsedEvent from Outlook
        caldav_event_ical: iCalendar string from CalDAV
    Returns:
        ParsedEvent to use (Outlook always wins per requirements)
    """
    # As per requirements, Outlook always wins in conflict resolution.
    return outlook_event

def sync_outlook_to_caldav(config_filepath: str, current_date: str, notification_func=send_pushbullet_notification) -> bool:
    """
    Orchestrate the synchronization of Outlook calendar events to CalDAV.
    Args:
        config_filepath: Path to config JSON file
        current_date: Date string (YYYY-MM-DD) for which to sync events
    Returns:
        True if sync is successful, False otherwise
    """
    notification_sent = False
    def send_notification_once(api_key, message, title):
        nonlocal notification_sent
        if api_key and not notification_sent:
            result = notification_func(api_key, message, title)
            log_pushbullet_attempt(message, str(result))
            notification_sent = True
        return notification_sent

    try:
        # 1. Load configuration
        config = Config.load_from_file(config_filepath)
        logger.setLevel(config.log_level.upper())
        logger.info("Configuration loaded successfully.")

        # 2. Initialize CalDAV client
        logger.info("Initializing CalDAV client...")
        caldav_client = CalDAVClient(
            config.caldav_url,
            config.caldav_username,
            config.caldav_password,
            getattr(config, "verify_ssl", True)
        )
        logger.info("CalDAV client initialized.")

        # 3. Fetch and delete all existing CalDAV events
        logger.info("Fetching existing CalDAV events...")
        existing_caldav_events = _retry(caldav_client.get_events, retries=3, delay=5)
        assert existing_caldav_events is not None # Explicit assertion for linter
        logger.info(f"Fetched {len(existing_caldav_events)} existing CalDAV events.")

        # Delete all events before syncing new ones
        for uid in existing_caldav_events.keys():
            logger.info(f"Deleting CalDAV event: {uid}")
            del_success = _retry(lambda: caldav_client.delete_event(uid), retries=3, delay=5)
            if del_success:
                logger.info(f"Event {uid} deleted successfully.")
            else:
                logger.error(f"Failed to delete event {uid}.")
                logger.critical("Aborting sync due to failed event deletion.")
                send_notification_once(getattr(config, "pushbullet_api_key", None),
                                      f"Outlook to CalDAV sync failed: Could not delete event {uid}",
                                      "Calendar Sync")
                return False

        # 4. Launch Outlook and navigate to calendar
        logger.info("Launching Outlook and navigating to calendar...")
        if not _retry(launch_outlook, retries=3, delay=5):
            logger.error("Failed to launch Outlook after multiple retries.")
            send_notification_once(getattr(config, "pushbullet_api_key", None),
                                  "Outlook to CalDAV sync failed: Could not launch Outlook",
                                  "Calendar Sync")
            return False
        if not _retry(navigate_to_calendar, retries=3, delay=5):
            logger.error("Failed to navigate to Outlook calendar after multiple retries.")
            send_notification_once(getattr(config, "pushbullet_api_key", None),
                                  "Outlook to CalDAV sync failed: Could not navigate to calendar",
                                  "Calendar Sync")
            return False
        logger.info("Outlook launched and navigated to calendar.")

        # 5. Capture screenshot
        screenshot_path = "outlook_calendar_screenshot.png"
        cropped_path = "outlook_calendar_screenshot_cropped.png"
        logger.info(f"Capturing screenshot to {screenshot_path}...")
        if not _retry(lambda: capture_screenshot(screenshot_path), retries=3, delay=5):
            logger.error("Failed to capture screenshot after multiple retries.")
            send_notification_once(getattr(config, "pushbullet_api_key", None),
                                  "Outlook to CalDAV sync failed: Could not capture screenshot",
                                  "Calendar Sync")
            return False
        logger.info(f"Screenshot captured. Raw: {screenshot_path}, Cropped: {cropped_path}")

        # 6. Process cropped screenshot with OCR to get parsed events
        logger.info("Processing cropped screenshot with OCR...")
        parsed_events = process_image_with_ocr(cropped_path)
        # Log each event for manual validation
        logger.debug("Parsed events from OCR:")
        for idx, event in enumerate(parsed_events, 1):
            logger.debug(f"Event {idx}: {event}")

        if not parsed_events:
            logger.info("No valid calendar events found in OCR output.")
            send_notification_once(getattr(config, "pushbullet_api_key", None),
                                  "Outlook to CalDAV synced successfully, 0 events created",
                                  "Calendar Sync")
            return True # No event to sync, consider it a success
        logger.info(f"Parsed {len(parsed_events)} event(s) from OCR output.")

        # 7. Sync all parsed events
        all_success = True
        for parsed_event in parsed_events:
            ical_data = map_parsed_event_to_ical(parsed_event)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"iCalendar payload to be sent for {parsed_event.title}:\n{ical_data}")

            # Always generate a new UUID for CalDAV UID
            uid_to_use = uuid.uuid4().hex[:12]
            logger.info(f"Creating CalDAV event for Outlook event: {parsed_event.title} (UID: {uid_to_use})")
            put_success = _retry(lambda: caldav_client.put_event(uid_to_use, ical_data), retries=3, delay=5)

            if not put_success:
                logger.error(f"Failed to PUT event '{parsed_event.title}'.")
                all_success = False
        # Send notification after sync attempt
        if all_success:
            send_notification_once(getattr(config, "pushbullet_api_key", None),
                                  f"Outlook to CalDAV synced successfully, {len(parsed_events)} events created",
                                  "Calendar Sync")
        else:
            send_notification_once(getattr(config, "pushbullet_api_key", None),
                                  "Outlook to CalDAV sync completed with errors.",
                                  "Calendar Sync")
        return all_success

    except FileNotFoundError as e:
        logger.error(f"Configuration or image file error: {e}")
        try:
            config = Config.load_from_file(config_filepath)
            api_key = getattr(config, "pushbullet_api_key", None)
        except Exception:
            api_key = None
        notification_func(api_key, f"Outlook to CalDAV sync failed: {e}", "Calendar Sync")
        return False
    except ValueError as e:
        logger.error(f"Configuration or parsing error: {e}")
        try:
            config = Config.load_from_file(config_filepath)
            api_key = getattr(config, "pushbullet_api_key", None)
        except Exception:
            api_key = None
        notification_func(api_key, f"Outlook to CalDAV sync failed: {e}", "Calendar Sync")
        return False
    except RuntimeError as e:
        logger.error(f"Runtime error during sync: {e}")
        try:
            config = Config.load_from_file(config_filepath)
            api_key = getattr(config, "pushbullet_api_key", None)
        except Exception:
            api_key = None
        notification_func(api_key, f"Outlook to CalDAV sync failed: {e}", "Calendar Sync")
        return False
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        try:
            config = Config.load_from_file(config_filepath)
            api_key = getattr(config, "pushbullet_api_key", None)
        except Exception:
            api_key = None
        notification_func(api_key, f"Outlook to CalDAV sync failed: {e}", "Calendar Sync")
        return False
