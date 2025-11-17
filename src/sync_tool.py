from src.config import Config
from src.outlook_automation import launch_outlook, navigate_to_calendar, capture_screenshot
from src.ocr_processor import process_image_with_ocr, parse_outlook_event_from_ocr
from src.gemini_extractor import extract_events_with_gemini, extract_events_with_gemini_fallback
from src.caldav_client import CalDAVClient, map_parsed_event_to_ical
from src.models.calendar_data import ParsedEvent
from src.utils.logger import setup_logging, log_pushbullet_attempt
from src.lib.pushbullet_notify import send_pushbullet_notification
import time
from typing import Callable, TypeVar
import logging
import urllib3
import uuid
import os

logger = setup_logging()
urllib3.disable_warnings()

R = TypeVar("R")


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
                raise  # Re-raise the exception on the last attempt
    raise RuntimeError("Function did not return a value after retries.")  # Should not be reached


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


def sync_outlook_to_caldav(
    config_filepath: str,
    current_date: str,
    notification_func=send_pushbullet_notification,
    dry_run: bool = False,
) -> bool:
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
            getattr(config, "verify_ssl", True),
        )
        logger.info("CalDAV client initialized.")

        # 4. Launch Outlook and navigate to calendar
        logger.info("Launching Outlook...")
        if not _retry(launch_outlook, retries=3, delay=5):
            logger.error("Failed to launch Outlook after multiple retries.")
            send_notification_once(
                getattr(config, "pushbullet_api_key", None),
                "Outlook to CalDAV sync failed: Could not launch Outlook",
                "Calendar Sync",
            )
            return False
        # TEMPORARILY DISABLED: Navigation to calendar (requires accessibility permissions)
        # User should manually ensure Outlook is in calendar view (Work Week + List view) before running
        # if not _retry(navigate_to_calendar, retries=3, delay=5):
        #     logger.error("Failed to navigate to Outlook calendar after multiple retries.")
        #     send_notification_once(
        #         getattr(config, "pushbullet_api_key", None),
        #         "Outlook to CalDAV sync failed: Could not navigate to calendar",
        #         "Calendar Sync",
        #     )
        #     return False
        logger.info("Outlook launched. Please ensure Outlook is in Calendar view (Work Week + List view).")
        time.sleep(3)  # Give user a moment to manually switch to calendar view if needed

        # 5. Capture screenshot
        screenshot_path = "outlook_calendar_screenshot.png"
        cropped_path = "outlook_calendar_screenshot_cropped.png"
        logger.info(f"Capturing screenshot to {screenshot_path}...")
        if not _retry(lambda: capture_screenshot(screenshot_path), retries=3, delay=5):
            logger.error("Failed to capture screenshot after multiple retries.")
            send_notification_once(
                getattr(config, "pushbullet_api_key", None),
                "Outlook to CalDAV sync failed: Could not capture screenshot",
                "Calendar Sync",
            )
            return False
        logger.info(f"Screenshot captured. Raw: {screenshot_path}, Cropped: {cropped_path}")

        # 6. Process cropped screenshot with OCR or Gemini to get parsed events
        use_gemini = getattr(config, "use_gemini_vision", False)
        gemini_api_key = getattr(config, "gemini_api_key", None)
        
        if use_gemini and gemini_api_key:
            logger.info("Processing cropped screenshot with Gemini Vision API...")
            try:
                parsed_events = extract_events_with_gemini(cropped_path, gemini_api_key)
            except Exception as e:
                logger.warning(f"Gemini extraction failed, falling back to OCR: {e}")
                logger.info("Processing cropped screenshot with OCR...")
                parsed_events = process_image_with_ocr(cropped_path)
        else:
            logger.info("Processing cropped screenshot with OCR...")
            parsed_events = process_image_with_ocr(cropped_path)
            
        # Log each event for manual validation
        logger.debug("Parsed events from OCR:")
        for idx, event in enumerate(parsed_events, 1):
            logger.debug(f"Event {idx}: {event}")

        if not parsed_events:
            logger.info("No valid calendar events found in OCR output.")
            send_notification_once(
                getattr(config, "pushbullet_api_key", None),
                "Outlook to CalDAV synced successfully, 0 events created",
                "Calendar Sync",
            )
            return True  # No event to sync, consider it a success
        logger.info(f"Parsed {len(parsed_events)} event(s) from OCR output.")

        # 3. Fetch and delete only future existing CalDAV events
        logger.info("Fetching existing CalDAV events...")
        existing_caldav_events = _retry(caldav_client.get_events, retries=3, delay=5)
        assert existing_caldav_events is not None  # Explicit assertion for linter
        logger.info(f"Fetched {len(existing_caldav_events)} existing CalDAV events.")

        # Delete only future events before syncing new ones, unless dry_run
        deleted_ics_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "ics_deleted"
        )
        os.makedirs(deleted_ics_dir, exist_ok=True)
        
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        for uid, event_obj in existing_caldav_events.items():
            # Extract event end time to determine if it's a future event
            try:
                # Get the VEVENT component from the event
                if hasattr(event_obj, 'icalendar_component'):
                    vevent = event_obj.icalendar_component
                elif hasattr(event_obj, 'instance') and hasattr(event_obj.instance, 'vevent'):
                    vevent = event_obj.instance.vevent
                else:
                    # Parse the ICS data to get the event end time
                    from icalendar import Calendar
                    if hasattr(event_obj, "data"):
                        ics_data = event_obj.data
                    elif hasattr(event_obj, "icalendar"):
                        ics_data = event_obj.icalendar()
                    else:
                        ics_data = str(event_obj)
                    cal = Calendar.from_ical(ics_data)
                    vevent = None
                    for component in cal.walk():
                        if component.name == "VEVENT":
                            vevent = component
                            break
                
                if vevent is None:
                    logger.warning(f"Could not parse VEVENT for {uid}, skipping deletion check.")
                    continue
                
                # Get DTEND or calculate from DTSTART + DURATION
                dtend = vevent.get('dtend')
                if dtend:
                    event_end = dtend.dt
                else:
                    dtstart = vevent.get('dtstart')
                    duration = vevent.get('duration')
                    if dtstart and duration:
                        event_end = dtstart.dt + duration.dt
                    elif dtstart:
                        # All-day event or event with no end time
                        event_end = dtstart.dt
                    else:
                        logger.warning(f"Could not determine end time for {uid}, skipping deletion check.")
                        continue
                
                # Ensure event_end is timezone-aware for comparison
                if hasattr(event_end, 'tzinfo'):
                    if event_end.tzinfo is None:
                        # Assume local timezone if naive
                        from datetime import datetime as dt
                        event_end = event_end.replace(tzinfo=timezone.utc)
                    # Convert to UTC for comparison
                    event_end_utc = event_end.astimezone(timezone.utc) if hasattr(event_end, 'astimezone') else event_end
                else:
                    # It's a date object, consider it as end of day UTC
                    from datetime import datetime as dt
                    event_end_utc = dt.combine(event_end, dt.max.time()).replace(tzinfo=timezone.utc)
                
                # Skip deletion if event has already ended
                if event_end_utc < now:
                    logger.info(f"Skipping past event {uid} (ended: {event_end_utc})")
                    continue
                    
            except Exception as e:
                logger.warning(f"Error checking event end time for {uid}: {e}. Will delete to be safe.")
            
            # Ensure uid is a string for filename extraction
            uid_str = str(uid)
            if "/" in uid_str:
                event_filename = uid_str.rstrip("/").split("/")[-1]
            else:
                event_filename = uid_str
            ics_filename = f"deleted_{event_filename}"
            ics_path = os.path.join(deleted_ics_dir, ics_filename)
            # Extract ICS string from caldav.Event object
            if hasattr(event_obj, "data"):
                ics_data = event_obj.data
            elif hasattr(event_obj, "icalendar"):
                ics_data = event_obj.icalendar()
            else:
                ics_data = str(event_obj)
            try:
                with open(ics_path, "w", encoding="utf-8") as f:
                    f.write(ics_data)
                logger.info(f"Backed up deleted event to ICS: {ics_path}")
            except Exception as e:
                logger.error(f"Failed to back up ICS file {ics_path}: {e}")

            if dry_run:
                logger.info(f"[DRY RUN] Would delete CalDAV event: {uid}")
            else:
                logger.info(f"Deleting CalDAV event: {uid}")
                del_success = _retry(lambda: caldav_client.delete_event(uid), retries=3, delay=5)
                if del_success:
                    logger.info(f"Event {uid} deleted successfully.")
                else:
                    logger.error(f"Failed to delete event {uid}.")
                    logger.critical("Aborting sync due to failed event deletion.")
                    send_notification_once(
                        getattr(config, "pushbullet_api_key", None),
                        f"Outlook to CalDAV sync failed: Could not delete event {uid}",
                        "Calendar Sync",
                    )
                    return False

        # 7. Sync all parsed events
        ics_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ics_create")
        os.makedirs(ics_dir, exist_ok=True)
        all_success = True
        for parsed_event in parsed_events:
            # Generate ICS data and UID inside map_parsed_event_to_ical
            ical_data, event_uid = map_parsed_event_to_ical(parsed_event)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    f"iCalendar payload to be sent for {parsed_event.title} (UID: {event_uid}):\n{ical_data}"
                )

            # Write ICS file to disk before creating event
            ics_filename = f"{event_uid}.ics"
            ics_path = os.path.join(ics_dir, ics_filename)
            try:
                with open(ics_path, "w", encoding="utf-8") as f:
                    f.write(ical_data)
                logger.debug(f"ICS file written: {ics_path}")
            except Exception as e:
                logger.error(f"Failed to write ICS file {ics_path}: {e}")

            if dry_run:
                logger.info(
                    f"[DRY RUN] Would create CalDAV event for Outlook event: {parsed_event.title} (UID: {event_uid})"
                )
            else:
                logger.info(
                    f"Creating CalDAV event for Outlook event: {parsed_event.title} (UID: {event_uid})"
                )
                put_success = _retry(
                    lambda: caldav_client.put_event(event_uid, ical_data), retries=3, delay=5
                )
                if not put_success:
                    logger.error(f"Failed to PUT event '{parsed_event.title}'.")
                    all_success = False
        # Send notification after sync attempt
        if dry_run:
            logger.info(
                f"[DRY RUN] Completed dry run. No events were deleted or created. {len(parsed_events)} events would have been created. ICS files written to {ics_dir}."
            )
            return True
        if all_success:
            send_notification_once(
                getattr(config, "pushbullet_api_key", None),
                f"Outlook to CalDAV synced successfully, {len(parsed_events)} events created",
                "Calendar Sync",
            )
        else:
            send_notification_once(
                getattr(config, "pushbullet_api_key", None),
                "Outlook to CalDAV sync failed: One or more events could not be created.",
                "Calendar Sync",
            )
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
