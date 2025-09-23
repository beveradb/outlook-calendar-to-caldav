from dataclasses import dataclass
from datetime import datetime, timedelta
import re
import os
from PIL import Image
import pytesseract
from src.utils.logger import logger


from src.models.calendar_data import ParsedEvent


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


def process_image_with_ocr(image_path: str):
    from src.utils.logger import logger
    try:
        img = Image.open(image_path)
    except Exception as e:
        logger.error(f"Could not open image {image_path}: {e}")
        raise FileNotFoundError(f"Image file not found at {image_path}")

    # --- Color replacement for #f6640c and #954a27 and similar colors ---
    # Convert to RGB if not already
    if img.mode != 'RGB':
        img = img.convert('RGB')
    pixels = img.load()
    width, height = img.size
    import colorsys
    def rgb_to_hls(r, g, b):
        return colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)

    # Replace any pixel with saturation above threshold
    saturation_thresh = 0.2
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            h, l, s = rgb_to_hls(r, g, b)
            if s > saturation_thresh:
                pixels[x, y] = (0, 0, 0)

    # Save the color-replaced image for manual review
    color_replaced_path = image_path.replace('.png', '_color_replaced.png')
    try:
        img.save(color_replaced_path)
        logger.debug(f"Color-replaced image saved to {color_replaced_path}")
    except Exception as e:
        logger.error(f"Could not save color-replaced image: {e}")

    # Convert to grayscale and enhance contrast
    img = img.convert('L')  # Grayscale
    threshold = 80
    img = img.point([255 if i > threshold else 0 for i in range(256)])

    # Save the processed image for manual review
    processed_path = image_path.replace('.png', '_bw.png')
    try:
        img.save(processed_path)
        logger.debug(f"High-contrast image saved to {processed_path}")
    except Exception as e:
        logger.error(f"Could not save high-contrast image: {e}")

    ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    n_boxes = len(ocr_data['level'])
    words = []
    # Collect words first, discarding those in x=775..880
    for i in range(n_boxes):
        word = ocr_data['text'][i].strip()
        if not word:
            continue
        x = ocr_data['left'][i]
        if 775 <= x <= 880:
            logger.debug(f"Discarding word at x={x}: '{word}'")
            continue
        word_data = {
            'text': word,
            'x': x,
            'y': ocr_data['top'][i],
            'width': ocr_data['width'][i],
            'height': ocr_data['height'][i]
        }
        words.append(word_data)

    # Sort words by y before logging
    words_for_log = sorted(words, key=lambda w: w['y'])
    logger.debug("Raw OCR word data:")
    for w in words_for_log:
        y_min = w['y']
        y_max = w['y'] + w['height']
        logger.debug(f"Word: {{'text': '{w['text']}', 'x': {w['x']}, 'y_min': {y_min}, 'y_max': {y_max}, 'width': {w['width']}, 'height': {w['height']}}}")

    # --- New strict rule-based row identification ---
    # 1. No row > 70px tall
    # 2. At least 20px between rows
    # 3. No row with only a single character

    # Sort words by top y
    words_sorted = sorted(words, key=lambda w: w['y'])
    rows = []  # List of lists of word objects
    ocr_crop_dir = os.path.join(os.path.dirname(image_path), "ocr_crops")
    os.makedirs(ocr_crop_dir, exist_ok=True)


    # --- Sweep-line/overlap row grouping ---
    unused = [dict(w) for w in words_sorted]
    last_y_max = None
    row_idx = 1
    while unused:
        # Start new row with lowest y_min
        unused.sort(key=lambda w: w['y'])
        seed = unused.pop(0)
        row_y_min = int(seed['y'])
        window_max = row_y_min + 62
        row_words = [seed]
        to_remove = []
        for w in unused:
            w_y_min = int(w['y'])
            if row_y_min <= w_y_min <= window_max:
                row_words.append(w)
                to_remove.append(w)
        for w in to_remove:
            unused.remove(w)
        if row_words:
            max_y_max = max(int(w['y']) + int(w['height']) for w in row_words)
            row_y_max = min(window_max, max_y_max)
            row_height = row_y_max - row_y_min
            row_words_sorted = sorted(row_words, key=lambda w: w['x'])
            row_text = ' '.join([w['text'] for w in row_words_sorted])
            if row_height > 62:
                logger.error(f"Row too tall: y_min={row_y_min}, y_max={row_y_max}, height={row_height}, words={[w['text'] for w in row_words_sorted]}")
                raise ValueError(f"Row too tall: {row_height}px. Words: {[w['text'] for w in row_words_sorted]}")
            if len(row_text) == 1:
                logger.error(f"Row contains only a single character: y_min={row_y_min}, y_max={row_y_max}, words={[w['text'] for w in row_words_sorted]}")
                raise ValueError(f"Row contains only a single character. Words: {[w['text'] for w in row_words_sorted]}")
            if last_y_max is not None and row_y_min - last_y_max < 5:
                logger.error(f"Gap between rows too small: prev_y_max={last_y_max}, curr_y_min={row_y_min}, gap={row_y_min - last_y_max}")
                raise ValueError(f"Gap between rows too small: {row_y_min - last_y_max}px")
            crop_path = os.path.join(ocr_crop_dir, f"row_{row_idx:02d}.png")
            crop_img = img.crop((0, float(row_y_min), float(img.width), float(row_y_max)))
            crop_img.save(crop_path)
            logger.debug(f"Row {row_idx}: y_min={row_y_min}, y_max={row_y_max}, text={row_text}")
            logger.debug(f"Row {row_idx}: cropped image saved to {crop_path}")
            rows.append(row_words_sorted)  # Save word objects per row
            last_y_max = row_y_max
            row_idx += 1
            row_idx += 1

    # --- Event parsing and cleanup ---
    # Rules:
    # - Date rows: "Monday, September 22" etc. (not events)
    # - Event rows: must have time range "HH:MM - HH:MM" or "All day event"
    # - Remove leading junk: e.g. "22 MON | ", "22 | ", " | ", "\\ 24) WED | "
    # - Event title: text before time or "All day event"
    # - Discard trailing text after time

    date_row_pattern = re.compile(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+[A-Za-z]+\s+\d{1,2}")
    time_range_pattern = re.compile(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})")
    all_day_pattern = re.compile(r"All day event", re.IGNORECASE)
    
    parsed_events = []
    current_date_str = None
    for idx, row_words in enumerate(rows):
        # Reconstruct row text for date row check
        row_text_full = ' '.join([w['text'] for w in row_words]).strip()
        # Check for date row
        if date_row_pattern.match(row_text_full):
            logger.info(f"Date row detected: {row_text_full}")
            # Parse date, always specify year to avoid ambiguity
            try:
                # Assume current year if not present
                current_year = datetime.now().year
                current_date_str = datetime.strptime(f"{row_text_full} {current_year}", "%A, %B %d %Y").strftime("%Y-%m-%d")
            except Exception:
                # Fallback: ignore date row if can't parse
                continue
            continue

        # Only parse event rows if we have a current date
        if not current_date_str:
            continue

        # For event rows, discard words with x < 120
        event_row_words = [w for w in row_words if w['x'] >= 120]
        row_text = ' '.join([w['text'] for w in event_row_words]).strip()

        # Check for time range or all day event
        time_match = time_range_pattern.search(row_text)
        all_day_match = all_day_pattern.search(row_text)
        if not time_match and not all_day_match:
            logger.error(f"Unable to parse event row: {row_text}")
            raise ValueError(f"Unable to parse event row: {row_text}")

        # Extract event title and times
        title = None
        start_time = None
        end_time = None
        if time_match:
            title = row_text[:time_match.start()].strip()
            start_time = time_match.group(1)
            end_time = time_match.group(2)
        elif all_day_match:
            idx = row_text.lower().find("all day event")
            # Extract title after 'All day event'
            title = row_text[idx + len("all day event"):].strip() if idx != -1 else row_text.strip()
            start_time = "00:00"
            end_time = "23:59"
        else:
            # Should not reach here due to earlier check, but guard for safety
            logger.error(f"Unable to parse event row: {row_text}")
            continue

        # Sanitize title and UID to remove problematic characters (e.g., forward slash)
        def sanitize(s: str) -> str:
            # Replace / and \ with - and remove control characters
            return re.sub(r'[\\/]', '-', s).strip()

        safe_title = sanitize(title)
        safe_uid = sanitize(f"{current_date_str}-{start_time}-{safe_title}")
        start_dt = f"{current_date_str}T{start_time}:00"
        end_dt = f"{current_date_str}T{end_time}:00"
        event_obj = ParsedEvent(
            original_source_id=safe_uid,
            start_datetime=start_dt,
            end_datetime=end_dt,
            title=safe_title,
            location=None,
            description=None,
            confidence_score=1.0
        )
        parsed_events.append(event_obj)
        logger.info(f"Calendar event detected: {event_obj.start_datetime} - {event_obj.end_datetime} | {event_obj.title}")

    return parsed_events
