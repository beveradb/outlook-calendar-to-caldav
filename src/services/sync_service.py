"""
Calendar sync service layer.
Implements Single Responsibility Principle by separating concerns.
"""
from typing import List, Optional
from datetime import datetime, timezone
import logging
import os

from src.models.calendar_data import ParsedEvent
from src.interfaces.calendar_repository import ICalendarRepository
from src.interfaces.notification_service import INotificationService
from src.interfaces.event_extractor import IEventExtractor
from src.caldav_client import map_parsed_event_to_ical

logger = logging.getLogger(__name__)


class EventDeletionService:
    """Responsible for deleting events from calendar"""
    
    def __init__(self, calendar_repo: ICalendarRepository, backup_dir: Optional[str] = None):
        """
        Initialize event deletion service.
        
        Args:
            calendar_repo: Calendar repository implementation
            backup_dir: Directory to backup deleted events (optional)
        """
        self.calendar_repo = calendar_repo
        self.backup_dir = backup_dir
        if backup_dir:
            os.makedirs(backup_dir, exist_ok=True)
    
    def delete_future_events(self, dry_run: bool = False) -> int:
        """
        Delete all future events (events that haven't ended yet).
        
        Args:
            dry_run: If True, don't actually delete, just log what would be deleted
            
        Returns:
            Number of events deleted
        """
        existing_events = self.calendar_repo.get_events()
        now = datetime.now(timezone.utc)
        deleted_count = 0
        
        for uid, event_obj in existing_events.items():
            try:
                # Check if event has ended
                event_end = self._get_event_end_time(event_obj)
                if event_end and event_end < now:
                    logger.info(f"Skipping past event {uid} (ended: {event_end})")
                    continue
            except Exception as e:
                logger.warning(f"Error checking event end time for {uid}: {e}. Will delete to be safe.")
            
            # Backup event if backup directory is configured
            if self.backup_dir:
                self._backup_event(uid, event_obj)
            
            # Delete event
            if dry_run:
                logger.info(f"[DRY RUN] Would delete CalDAV event: {uid}")
            else:
                logger.info(f"Deleting CalDAV event: {uid}")
                if self.calendar_repo.delete_event(uid):
                    deleted_count += 1
                    logger.info(f"Event {uid} deleted successfully.")
                else:
                    logger.error(f"Failed to delete event {uid}.")
                    raise RuntimeError(f"Failed to delete event {uid}")
        
        return deleted_count
    
    def _get_event_end_time(self, event_obj) -> Optional[datetime]:
        """Extract event end time from caldav event object"""
        from icalendar import Calendar
        
        # Get ICS data
        if hasattr(event_obj, "data"):
            ics_data = event_obj.data
        elif hasattr(event_obj, "icalendar"):
            ics_data = event_obj.icalendar()
        else:
            ics_data = str(event_obj)
        
        # Parse ICS to get end time
        cal = Calendar.from_ical(ics_data)
        for component in cal.walk():
            if component.name == "VEVENT":
                # Get DTEND or calculate from DTSTART + DURATION
                dtend = component.get('dtend')
                if dtend:
                    event_end = dtend.dt
                else:
                    dtstart = component.get('dtstart')
                    duration = component.get('duration')
                    if dtstart and duration:
                        event_end = dtstart.dt + duration.dt
                    elif dtstart:
                        event_end = dtstart.dt
                    else:
                        return None
                
                # Ensure timezone-aware for comparison
                if hasattr(event_end, 'tzinfo'):
                    if event_end.tzinfo is None:
                        event_end = event_end.replace(tzinfo=timezone.utc)
                    event_end_utc = event_end.astimezone(timezone.utc) if hasattr(event_end, 'astimezone') else event_end
                else:
                    # It's a date object, consider it as end of day UTC
                    from datetime import datetime as dt
                    event_end_utc = dt.combine(event_end, dt.max.time()).replace(tzinfo=timezone.utc)
                
                return event_end_utc
        
        return None
    
    def _backup_event(self, uid: str, event_obj):
        """Backup event to ICS file"""
        if not self.backup_dir:
            return
        
        # Extract filename from uid
        uid_str = str(uid)
        if "/" in uid_str:
            event_filename = uid_str.rstrip("/").split("/")[-1]
        else:
            event_filename = uid_str
        
        ics_filename = f"deleted_{event_filename}"
        ics_path = os.path.join(self.backup_dir, ics_filename)
        
        # Extract ICS string
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


class EventCreationService:
    """Responsible for creating events in calendar"""
    
    def __init__(
        self,
        calendar_repo: ICalendarRepository,
        backup_dir: Optional[str] = None
    ):
        """
        Initialize event creation service.
        
        Args:
            calendar_repo: Calendar repository implementation
            backup_dir: Directory to save created event ICS files (optional)
        """
        self.calendar_repo = calendar_repo
        self.backup_dir = backup_dir
        if backup_dir:
            os.makedirs(backup_dir, exist_ok=True)
    
    def create_events(self, events: List[ParsedEvent], dry_run: bool = False) -> tuple[int, int]:
        """
        Create multiple events in the calendar.
        
        Args:
            events: List of parsed events to create
            dry_run: If True, don't actually create, just log what would be created
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        success_count = 0
        fail_count = 0
        
        for event in events:
            ical_data, event_uid = map_parsed_event_to_ical(event)
            
            logger.debug(f"iCalendar payload for {event.title} (UID: {event_uid}):\n{ical_data}")
            
            # Backup to ICS file if configured
            if self.backup_dir:
                self._save_ics_file(event_uid, ical_data)
            
            if dry_run:
                logger.info(f"[DRY RUN] Would create CalDAV event for: {event.title} (UID: {event_uid})")
                success_count += 1
            else:
                logger.info(f"Creating CalDAV event for: {event.title} (UID: {event_uid})")
                if self.calendar_repo.put_event(event_uid, ical_data):
                    success_count += 1
                else:
                    logger.error(f"Failed to PUT event '{event.title}'.")
                    fail_count += 1
        
        return success_count, fail_count
    
    def _save_ics_file(self, uid: str, ical_data: str):
        """Save ICS data to file"""
        if not self.backup_dir:
            return
        
        ics_filename = f"{uid}.ics"
        ics_path = os.path.join(self.backup_dir, ics_filename)
        
        try:
            with open(ics_path, "w", encoding="utf-8") as f:
                f.write(ical_data)
            logger.debug(f"ICS file written: {ics_path}")
        except Exception as e:
            logger.error(f"Failed to write ICS file {ics_path}: {e}")


class CalendarSyncOrchestrator:
    """
    Orchestrates the calendar synchronization process.
    Coordinates event extraction, deletion, and creation.
    """
    
    def __init__(
        self,
        event_extractor: IEventExtractor,
        deletion_service: EventDeletionService,
        creation_service: EventCreationService,
        notification_service: INotificationService
    ):
        """
        Initialize the sync orchestrator.
        
        Args:
            event_extractor: Service for extracting events from images
            deletion_service: Service for deleting events
            creation_service: Service for creating events
            notification_service: Service for sending notifications
        """
        self.event_extractor = event_extractor
        self.deletion_service = deletion_service
        self.creation_service = creation_service
        self.notification_service = notification_service
    
    def sync(self, screenshot_path: str, dry_run: bool = False) -> bool:
        """
        Execute the sync process.
        
        Args:
            screenshot_path: Path to the Outlook calendar screenshot
            dry_run: If True, don't actually make changes
            
        Returns:
            True if sync succeeded, False otherwise
        """
        try:
            # Extract events from screenshot
            logger.info(f"Extracting events from screenshot: {screenshot_path}")
            parsed_events = self.event_extractor.extract_events(screenshot_path)
            
            if not parsed_events:
                logger.info("No valid calendar events found.")
                self.notification_service.send_notification(
                    "Outlook to CalDAV synced successfully, 0 events created",
                    "Calendar Sync"
                )
                return True
            
            logger.info(f"Parsed {len(parsed_events)} event(s) from screenshot.")
            
            # Delete future events
            logger.info("Deleting future events from calendar...")
            self.deletion_service.delete_future_events(dry_run=dry_run)
            
            # Create new events
            logger.info("Creating new events in calendar...")
            success_count, fail_count = self.creation_service.create_events(
                parsed_events,
                dry_run=dry_run
            )
            
            # Send notification
            if dry_run:
                logger.info(
                    f"[DRY RUN] Completed. {success_count} events would have been created."
                )
                return True
            
            if fail_count == 0:
                self.notification_service.send_notification(
                    f"Outlook to CalDAV synced successfully, {success_count} events created",
                    "Calendar Sync"
                )
                return True
            else:
                self.notification_service.send_notification(
                    f"Outlook to CalDAV sync partially failed: {success_count} created, {fail_count} failed",
                    "Calendar Sync"
                )
                return False
        
        except Exception as e:
            logger.error(f"Sync failed with error: {e}", exc_info=True)
            self.notification_service.send_notification(
                f"Outlook to CalDAV sync failed: {e}",
                "Calendar Sync"
            )
            return False
