
from dataclasses import dataclass
import requests

# Assuming ParsedEvent is defined in ocr_processor.py
from src.ocr_processor import ParsedEvent


class CalDAVClient:
    """
    Simple CalDAV client for event PUT and fetch operations.
    """
    def __init__(self, base_url: str, username: str, password: str, verify_ssl: bool = True):
        """
        Args:
            base_url: CalDAV server base URL (ending with /)
            username: CalDAV username
            password: CalDAV password
            verify_ssl: Whether to verify SSL certificates (default: True)
        """
        self.base_url = base_url
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl

    def put_event(self, uid: str, ical_data: str) -> requests.Response:
        """
        Upload or update an event to CalDAV server.
        Args:
            uid: Unique identifier for the event (used as filename)
            ical_data: iCalendar string
        Returns:
            requests.Response from the PUT request
        """
        url = f"{self.base_url}{uid}.ics"
        headers = {"Content-Type": "text/calendar; charset=utf-8"}
        response = requests.put(
            url,
            data=ical_data.encode('utf-8'),
            auth=(self.username, self.password),
            verify=self.verify_ssl
        )
        return response

    def get_events(self) -> dict[str, str]:
        """
        Fetch all events from the CalDAV server.
        Returns:
            Dictionary mapping event UIDs to iCalendar strings.
        Note: This is a stub; a real implementation would parse the CalDAV multistatus XML response.
        """
        # This is a simplified implementation. A real CalDAV client would parse the multistatus XML response.
        # For now, it returns a dummy dictionary.
        return {"caldav_event_1": "BEGIN:VCALENDAR...END:VCALENDAR"}

def map_parsed_event_to_ical(event: ParsedEvent) -> str:
    """
    Convert a ParsedEvent object to an iCalendar (VCALENDAR) string.
    Args:
        event: ParsedEvent instance
    Returns:
        iCalendar string
    """
    # Format datetimes to iCalendar format (YYYYMMDDTHHMMSSZ)
    dtstamp = event.start_datetime.replace("-", "").replace(":", "") + "Z"
    dtstart = event.start_datetime.replace("-", "").replace(":", "") + "Z"
    dtend = event.end_datetime.replace("-", "").replace(":", "") + "Z"

    ical_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Example Corp//Calendar Sync//EN",
        "BEGIN:VEVENT",
        f"UID:{event.original_source_id}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        f"SUMMARY:{event.title}"
    ]

    if event.location:
        ical_lines.append(f"LOCATION:{event.location}")
    if event.description:
        ical_lines.append(f"DESCRIPTION:{event.description}")

    ical_lines.extend([
        "END:VEVENT",
        "END:VCALENDAR"
    ])
    return "\n".join(ical_lines)
