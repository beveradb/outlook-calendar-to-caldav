from src.ocr_processor import ParsedEvent

def resolve_conflict(outlook_event: ParsedEvent, caldav_event_ical: str) -> ParsedEvent:
    """Resolves conflicts by always prioritizing the Outlook event."""
    # As per requirements, Outlook always wins in conflict resolution.
    return outlook_event
