from dataclasses import dataclass
from datetime import datetime, timedelta
import re
from PIL import Image
import pytesseract


@dataclass
class ParsedEvent:
    """
    Represents a calendar event parsed from OCR output.
    """
    original_source_id: str
    start_datetime: str
    end_datetime: str
    title: str
    location: str | None = None
    description: str | None = None
    confidence_score: float = 0.0


def _is_location_line(line: str) -> bool:
    """
    Heuristic to determine if a line is likely a location (e.g., room, office).
    Args:
        line: Text line from OCR output
    Returns:
        True if line is likely a location, False otherwise
    """
    if not line or len(line.split()) > 6:
        return False
    keywords = ["room", "office", "building", "floor", "suite"]
    if any(keyword in line.lower() for keyword in keywords):
        return True
    if re.match(r'^[A-Z]?[0-9]{3,4}$', line):
        return True
    # If it's short and not a typical description phrase, maybe location
    if len(line.split()) <= 4 and not any(word in line.lower() for word in ["check-in", "discussion", "blocker", "project", "sync", "standup"]):
        return True
    return False


def parse_outlook_event_from_ocr(ocr_text: str, current_date: str) -> ParsedEvent | None:
    """
    Parse OCR text output into a ParsedEvent object.
    Args:
        ocr_text: Raw text output from OCR
        current_date: Date string (YYYY-MM-DD) for the event
    Returns:
        ParsedEvent if parsing is successful, None otherwise
    Raises:
        ValueError if time parsing fails
    """
    if not ocr_text.strip():
        return None

    lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
    if not lines:
        return None

    # Placeholder for actual parsing logic
    # This will be refined in later implementation tasks
    
    # For now, let's try to extract a basic event from the first few lines
    title = ""
    start_time_str = ""
    end_time_str = ""
    location = None
    description_lines = []

    # Regex to find time ranges like "10:00 AM - 11:00 AM"
    time_range_pattern = re.compile(r'(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)')
    all_day_pattern = re.compile(r'All Day\s*(.*)')

    event_found = False
    for i, line in enumerate(lines):
        if time_range_pattern.search(line):
            match = time_range_pattern.search(line)
            if not match:
                raise ValueError(f"Could not parse time from line: {line}")
            start_time_str = match.group(1)
            end_time_str = match.group(2)
            title = line[match.end():].strip()
            event_found = True
            # Remaining lines might be location/description
            if i + 1 < len(lines):
                next_line = lines[i+1]
                if not time_range_pattern.search(next_line) and not all_day_pattern.search(next_line) and next_line:
                    if _is_location_line(next_line):
                        location = next_line
                        description_lines = lines[i+2:]
                    else:
                        description_lines = lines[i+1:]
                else:
                    description_lines = lines[i+1:]
            break
        elif all_day_pattern.search(line):
            match = all_day_pattern.search(line)
            if not match:
                continue
            title = match.group(1).strip()
            start_time_str = "12:00 AM"
            end_time_str = "11:59 PM"
            event_found = True
            description_lines = lines[i+1:]
            break
        # If line looks like a time range but doesn't match expected format, raise ValueError
        elif re.search(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', line):
            raise ValueError(f"Could not parse time from line: {line}")

    if not event_found:
        return None # No event line found

    # Convert times to ISO format
    try:
        start_datetime_obj = datetime.strptime(f"{current_date} {start_time_str}", "%Y-%m-%d %I:%M %p")
        end_datetime_obj = datetime.strptime(f"{current_date} {end_time_str}", "%Y-%m-%d %I:%M %p")
    except ValueError as e:
        raise ValueError(f"Could not parse time from: {start_time_str} - {end_time_str}. Original error: {e}")

    # Handle all-day event end time to be end of day
    if "All Day" in ocr_text and end_time_str == "11:59 PM":
        end_datetime_obj = end_datetime_obj.replace(hour=23, minute=59, second=59)

    description = "\n".join(description_lines).strip() if description_lines else None
    if description == "": description = None

    # Generate a simple original_source_id for now
    original_source_id = f"{current_date}-{start_time_str}-{title}"

    return ParsedEvent(
        original_source_id=original_source_id,
        start_datetime=start_datetime_obj.isoformat(timespec='seconds'),
        end_datetime=end_datetime_obj.isoformat(timespec='seconds'),
        title=title,
        location=location,
        description=description,
        confidence_score=0.8 # Placeholder
    )


def process_image_with_ocr(image_path: str) -> str:
    """
    Run OCR on an image file and return the extracted text.
    Args:
        image_path: Path to the image file
    Returns:
        Extracted text as a string
    Raises:
        FileNotFoundError if the image file does not exist
        RuntimeError for other OCR errors
    """
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except FileNotFoundError:
        raise FileNotFoundError(f"Image file not found at {image_path}")
    except Exception as e:
        raise RuntimeError(f"Error during OCR processing: {e}")
