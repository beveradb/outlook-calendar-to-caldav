"""
Claude Vision (via AWS Bedrock) calendar event extractor.

Uses Claude Opus on Bedrock to extract calendar events from Outlook
calendar screenshots. Authenticates using the ambient AWS credentials
(SSO session / profile already configured for Claude Code).
"""

import base64
import json
import os
import subprocess
import sys
from datetime import date, datetime
from typing import List

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, TokenRetrievalError

from src.models.calendar_data import ParsedEvent, WeekExtraction
from src.utils.logger import logger

DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-4-6"
DEFAULT_REGION = "us-east-1"
SSO_LOGIN_TIMEOUT = 120  # seconds; unattended runs must never hang on a login


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
        try:
            result = subprocess.run(
                ["aws", "sso", "login"],
                check=False,
                capture_output=False,
                timeout=SSO_LOGIN_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"aws sso login timed out after {SSO_LOGIN_TIMEOUT}s")
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


def _invoke_vision(image_path: str, prompt: str, model_id: str, region: str) -> str:
    """Send one image + prompt to Claude on Bedrock; return the reply text without code fences."""
    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")
    ext = image_path.lower().rsplit(".", 1)[-1]
    media_type = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/png")
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 8192,
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_base64}},
            {"type": "text", "text": prompt},
        ]}],
    })
    client = boto3.client("bedrock-runtime", region_name=region)
    logger.info(f"Sending {os.path.basename(image_path)} to Claude on Bedrock ({model_id})...")
    response = client.invoke_model(modelId=model_id, contentType="application/json",
                                   accept="application/json", body=body)
    text = json.loads(response["body"].read())["content"][0]["text"].strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


WEEK_PROMPT = """You are reading a screenshot of the Microsoft Outlook for Mac window showing a
calendar in Work Week view with the List layout. The header near the top shows the date range of
the week being displayed (e.g. "November 23 - November 27, 2026"); day headers such as
"Monday, November 23" group the events below them.

Return ONE JSON object and nothing else:
{
  "range": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
  "events": [
    {"title": "...", "date": "YYYY-MM-DD", "start_time": "HH:MM", "end_time": "HH:MM",
     "location": "optional", "description": "optional"}
  ]
}

Rules:
- "range" is the date range printed in the window's header. Read it from the header text, not
  from today's date. If you cannot read it with certainty, set "range" to null.
- Take each event's date from the day header it sits under.
- Times are 24-hour, as shown in the row (e.g. "Tue 11/24/26, 12:15 (15 minutes)" means
  start 12:15, end 12:30; "14:00 - 15:00" means start 14:00, end 15:00).
- For an all-day or multi-day event use start_time "00:00" and end_time "23:59" on the date
  under which it is listed.
- Skip events whose title is struck through or starts with "Canceled:".
- Include every remaining row. If there are no events, return "events": []."""


def _parse_date(s):
    try:
        return date.fromisoformat(str(s))
    except (TypeError, ValueError):
        return None


def extract_week_with_bedrock(image_path: str, model_id: str = None, region: str = None) -> WeekExtraction:
    """
    Extract one week's events AND the visible date range from an Outlook List-view capture.
    The range is what makes a capture trustworthy enough to delete against; it is None
    when the model could not read it.
    """
    _ensure_aws_session()
    text = _invoke_vision(image_path, WEEK_PROMPT, model_id or DEFAULT_MODEL_ID, region or DEFAULT_REGION)
    data = json.loads(text)
    rng = data.get("range") or {}
    start, end = _parse_date(rng.get("start")), _parse_date(rng.get("end"))
    if not (start and end and start <= end):
        start = end = None
    events = []
    for e in data.get("events") or []:
        try:
            events.append(ParsedEvent(
                start_datetime=f"{e['date']}T{e['start_time']}:00",
                end_datetime=f"{e['date']}T{e['end_time']}:00",
                title=e["title"], location=e.get("location"), description=e.get("description"),
                confidence_score=0.95))
        except (KeyError, TypeError) as err:
            logger.warning(f"Skipping malformed event from Claude: {err}")
    logger.info(f"{os.path.basename(image_path)}: range {start}..{end}, {len(events)} events")
    return WeekExtraction(start, end, events)
