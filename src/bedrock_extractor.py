"""
Claude Vision (via AWS Bedrock) calendar event extractor.

Uses Claude Opus on Bedrock to extract calendar events from Outlook
calendar screenshots. Authenticates using the ambient AWS credentials
(SSO session / profile already configured for Claude Code).
"""

import base64
import json
import subprocess
import sys
from datetime import datetime
from typing import List

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, TokenRetrievalError

from src.models.calendar_data import ParsedEvent
from src.utils.logger import logger

DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-4-6"
DEFAULT_REGION = "us-east-1"


def _ensure_aws_session() -> None:
    """
    Verify AWS credentials are valid. If the SSO session is expired,
    trigger `aws sso login` to refresh it.
    """
    try:
        sts = boto3.client("sts")
        sts.get_caller_identity()
        logger.debug("AWS SSO session is active")
    except (NoCredentialsError, TokenRetrievalError, ClientError) as e:
        logger.warning(f"AWS credentials expired or missing ({e}), triggering SSO login...")
        result = subprocess.run(
            ["aws", "sso", "login"],
            check=False,
            capture_output=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                "aws sso login failed. Please run 'aws sso login' manually."
            )
        # Verify credentials work after login
        sts = boto3.client("sts")
        sts.get_caller_identity()
        logger.info("AWS SSO login successful")


def extract_events_with_bedrock(
    image_path: str,
    model_id: str = DEFAULT_MODEL_ID,
    region: str = DEFAULT_REGION,
) -> List[ParsedEvent]:
    """
    Extract calendar events from a screenshot using Claude on Bedrock.

    Uses the ambient AWS credentials (profile/SSO session).
    """
    model_id = model_id or DEFAULT_MODEL_ID
    region = region or DEFAULT_REGION

    _ensure_aws_session()

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    # Determine media type from file extension
    ext = image_path.lower().rsplit(".", 1)[-1]
    media_type_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}
    media_type = media_type_map.get(ext, "image/png")

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

    client = boto3.client("bedrock-runtime", region_name=region)

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ],
    })

    logger.info(f"Sending screenshot to Claude on Bedrock ({model_id})...")
    response = client.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=body,
    )

    response_body = json.loads(response["body"].read())
    response_text = response_body["content"][0]["text"].strip()
    logger.debug(f"Bedrock raw response: {response_text}")

    # Clean up markdown code blocks if present
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()

    events_data = json.loads(response_text)
    logger.info(f"Claude extracted {len(events_data)} events")

    parsed_events = []
    for event_data in events_data:
        try:
            date_str = event_data["date"]
            start_time_str = event_data["start_time"]
            end_time_str = event_data["end_time"]

            start_datetime = f"{date_str}T{start_time_str}:00"
            end_datetime = f"{date_str}T{end_time_str}:00"

            event = ParsedEvent(
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                title=event_data["title"],
                location=event_data.get("location"),
                description=event_data.get("description"),
                confidence_score=0.95,
            )
            parsed_events.append(event)
            logger.info(f"Calendar event detected: {event.start_datetime} - {event.end_datetime} | {event.title}")
        except (KeyError, ValueError) as e:
            logger.warning(f"Failed to parse event from Claude response: {event_data}. Error: {e}")
            continue

    return parsed_events
