

from src.ocr_processor import ParsedEvent
from src.interfaces.calendar_repository import ICalendarRepository
import caldav
from caldav import DAVClient


class CalDAVClient(ICalendarRepository):

    def __init__(self, calendar_url: str, username: str, password: str, verify_ssl: bool = True):
        self.calendar_url = calendar_url
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.client = DAVClient(
            url=calendar_url,
            username=username,
            password=password,
            ssl_verify_cert=verify_ssl
        )
        # Use the calendar at the specified URL
        self.calendar = caldav.Calendar(
            client=self.client,
            url=calendar_url
        )

    def get_events(self) -> dict[str, caldav.Event]:
        """
        Fetch all events from the configured calendar using the caldav library.
        Returns:
            Dictionary mapping event hrefs to caldav.Event objects.
        """
        events = {}
        for event in self.calendar.events():
            href = event.url
            events[href] = event
        return events

    def delete_event(self, event_url: str) -> bool:
        """
        Delete an event from the configured calendar by its full URL.
        Args:
            event_url: Full URL to the event resource
        Returns:
            True if deletion succeeded, False otherwise
        """
        try:
            for event in self.calendar.events():
                if event.url == event_url:
                    event.delete()
                    return True
            return False
        except Exception:
            return False

    def put_event(self, uid: str, ical_data: str) -> bool:
        """
        Upload or update an event to the configured calendar using the caldav library.
        Args:
            uid: Unique identifier for the event (used as filename)
            ical_data: iCalendar string
        Returns:
            True if upload succeeded, False otherwise
        """
        try:
            event = self.calendar.add_event(ical_data)
            return True
        except Exception as e:
            return False

def map_parsed_event_to_ical(event: ParsedEvent) -> tuple[str, str]:
    """
    Convert a ParsedEvent object to an iCalendar (VCALENDAR) string and generate a UID.
    Args:
        event: ParsedEvent instance
        timezone: 'America/New_York' (default) or 'UTC' for test compatibility
    Returns:
        Tuple of (iCalendar string, UID)
    """
    from datetime import datetime
    from datetime import timezone as dt_timezone
    import pytz
    import uuid

    def to_dt(dt_str, tz):
        dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
        if tz == "UTC":
            dt_utc = pytz.utc.localize(dt)
            return dt_utc.strftime("%Y%m%dT%H%M%SZ")
        else:
            eastern = pytz.timezone("America/New_York")
            dt_eastern = eastern.localize(dt)
            return dt_eastern.strftime("%Y%m%dT%H%M%S")

    # Default to America/New_York unless overridden
    event_timezone = getattr(event, "_ical_timezone", "America/New_York")
    dtstamp = to_dt(event.start_datetime, event_timezone)
    dtstart = to_dt(event.start_datetime, event_timezone)
    dtend = to_dt(event.end_datetime, event_timezone)

    event_uid = uuid.uuid4().hex[:12]
    now_utc = datetime.now(dt_timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ical_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "PRODID:-//calendar-sync//EN",
        f"X-WR-TIMEZONE:{event_timezone}",
    ]
    # Add concise VTIMEZONE for America/New_York
    if event_timezone == "America/New_York":
        ical_lines.extend([
            "BEGIN:VTIMEZONE",
            "TZID:America/New_York",
            "BEGIN:STANDARD",
            "DTSTART:19701101T020000",
            "RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU",
            "TZNAME:EST",
            "TZOFFSETFROM:-0400",
            "TZOFFSETTO:-0500",
            "END:STANDARD",
            "BEGIN:DAYLIGHT",
            "DTSTART:19700308T020000",
            "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU",
            "TZNAME:EDT",
            "TZOFFSETFROM:-0500",
            "TZOFFSETTO:-0400",
            "END:DAYLIGHT",
            "X-LIC-LOCATION:America/New_York",
            "END:VTIMEZONE"
        ])
    ical_lines.extend([
        "BEGIN:VEVENT",
        f"UID:{event_uid}",
        f"DTSTAMP:{now_utc}",
        f"CREATED:{now_utc}",
        f"LAST-MODIFIED:{now_utc}",
        "SEQUENCE:0",
        "STATUS:CONFIRMED",
        "TRANSP:OPAQUE",
    ])
    if event_timezone == "UTC":
        ical_lines.append(f"DTSTART:{dtstart}")
        ical_lines.append(f"DTEND:{dtend}")
    else:
        ical_lines.append(f"DTSTART;TZID=America/New_York:{dtstart}")
        ical_lines.append(f"DTEND;TZID=America/New_York:{dtend}")
    ical_lines.append(f"SUMMARY:{event.title}")

    if event.location:
        ical_lines.append(f"LOCATION:{event.location}")
    if event.description:
        ical_lines.append(f"DESCRIPTION:{event.description}")

    ical_lines.extend([
        "END:VEVENT",
        "END:VCALENDAR"
    ])
    return "\n".join(ical_lines), event_uid
