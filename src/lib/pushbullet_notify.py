"""
Pushbullet notification logic for calendar sync tool.
"""
import requests
from typing import Optional

PUSHBULLET_API_URL = "https://api.pushbullet.com/v2/pushes"

def send_pushbullet_notification(api_key: str, message: str, title: str = "Calendar Sync") -> Optional[str]:
    headers = {
        "Access-Token": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "type": "note",
        "title": title,
        "body": message
    }
    # Try to get verify_ssl from config, default to True if not found
    try:
        import src.config
        config = src.config.Config.load_from_file()
        verify_ssl = getattr(config, "verify_ssl", True)
    except Exception:
        verify_ssl = True
    try:
        response = requests.post(PUSHBULLET_API_URL, json=data, headers=headers, timeout=5, verify=verify_ssl)
        response.raise_for_status()
        resp_json = response.json()
        # Return just the iden string if present (for tests)
        if isinstance(resp_json, dict) and "iden" in resp_json:
            return resp_json["iden"]
        return resp_json
    except Exception as e:
        err_str = str(e)
        if "Unauthorized" in err_str or "Invalid API key" in err_str:
            return "Unauthorized"
        return err_str
