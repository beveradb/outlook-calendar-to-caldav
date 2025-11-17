"""
Gemini Vision API-based calendar event extractor.

This module uses Google's Gemini vision model to extract calendar events
from Outlook calendar screenshots with much higher reliability than traditional OCR.
"""

import os
import json
from datetime import datetime
from typing import List
import google.generativeai as genai
from PIL import Image

from src.models.calendar_data import ParsedEvent
from src.utils.logger import logger


def extract_events_with_gemini(image_path: str, api_key: str) -> List[ParsedEvent]:
    """
    Extract calendar events from a screenshot using Gemini Vision API.
    
    Args:
        image_path: Path to the cropped calendar screenshot
        api_key: Google Gemini API key
        
    Returns:
        List of ParsedEvent objects extracted from the image
        
    Raises:
        Exception if Gemini API call fails
    """
    # Configure Gemini
    genai.configure(api_key=api_key)
    
    # Use Gemini 2.0 Flash with vision capabilities
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Load image
    try:
        img = Image.open(image_path)
        logger.debug(f"Loaded image from {image_path} for Gemini processing")
    except Exception as e:
        logger.error(f"Failed to load image {image_path}: {e}")
        raise
    
    # Craft a detailed prompt for event extraction
    # Get current year to help Gemini infer the correct year
    current_year = datetime.now().year
    
    prompt = f"""You are analyzing a screenshot of Microsoft Outlook calendar in Work Week view with List layout.

IMPORTANT: Today's date is {datetime.now().strftime('%B %d, %Y')}. The current year is {current_year}.

Please extract ALL calendar events visible in this screenshot and return them as a JSON array.

For each event, extract:
- title: The event title/subject
- start_time: Start time in HH:MM format (24-hour)
- end_time: End time in HH:MM format (24-hour) 
- date: Date in YYYY-MM-DD format (YEAR MUST BE {current_year})
- location: Location if visible (optional)
- description: Any additional details visible (optional)

Important notes:
- The calendar shows events with dates on the left (date numbers like 28, 29, 30, 31)
- Events show time ranges like "11:45 - 12:00" or "16:00 - 16:55"
- Some events may show "Microsoft Teams Meeting" or other meeting types
- Extract the date from the date headers (e.g., "Monday, October 27", "Tuesday, October 28")
- Be very careful to match events with their correct dates
- If you see multiple events on the same day, include all of them
- If a time range is partially visible or unclear, make your best estimate
- CRITICAL: All dates must use the year {current_year}, not any other year

Return ONLY a valid JSON array with no additional text. Format:
[
  {{
    "title": "Event Title",
    "start_time": "HH:MM",
    "end_time": "HH:MM",
    "date": "YYYY-MM-DD",
    "location": "optional location",
    "description": "optional description"
  }}
]

Extract all events you can see."""

    try:
        logger.info("Sending screenshot to Gemini Vision API for event extraction...")
        response = model.generate_content([prompt, img])
        
        # Extract the JSON from response
        response_text = response.text.strip()
        logger.debug(f"Gemini raw response: {response_text}")
        
        # Clean up the response (remove markdown code blocks if present)
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # Remove ```json
        if response_text.startswith("```"):
            response_text = response_text[3:]   # Remove ```
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # Remove trailing ```
        response_text = response_text.strip()
        
        # Parse JSON
        events_data = json.loads(response_text)
        logger.info(f"Gemini extracted {len(events_data)} events")
        
        # Convert to ParsedEvent objects
        parsed_events = []
        for event_data in events_data:
            try:
                # Combine date and time
                date_str = event_data['date']
                start_time_str = event_data['start_time']
                end_time_str = event_data['end_time']
                
                # Create ISO format datetime strings
                start_datetime = f"{date_str}T{start_time_str}:00"
                end_datetime = f"{date_str}T{end_time_str}:00"
                
                # Validate datetime format
                datetime.fromisoformat(start_datetime)
                datetime.fromisoformat(end_datetime)
                
                event = ParsedEvent(
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    title=event_data['title'],
                    location=event_data.get('location'),
                    description=event_data.get('description'),
                    confidence_score=0.95  # Gemini is highly reliable
                )
                parsed_events.append(event)
                logger.info(f"Calendar event detected: {event.start_datetime} - {event.end_datetime} | {event.title}")
                
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse event from Gemini response: {event_data}. Error: {e}")
                continue
        
        return parsed_events
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {e}")
        logger.error(f"Response was: {response_text}")
        raise
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        raise


def extract_events_with_gemini_fallback(image_path: str, api_key: str) -> List[ParsedEvent]:
    """
    Extract events using Gemini with fallback to OCR if it fails.
    
    Args:
        image_path: Path to the cropped calendar screenshot
        api_key: Google Gemini API key
        
    Returns:
        List of ParsedEvent objects
    """
    try:
        return extract_events_with_gemini(image_path, api_key)
    except Exception as e:
        logger.warning(f"Gemini extraction failed, falling back to OCR: {e}")
        from src.ocr_processor import process_image_with_ocr
        return process_image_with_ocr(image_path)
