

# Outlook to CalDAV Sync Tool

Synchronize your Microsoft Outlook Calendar to any CalDAV server (e.g., Radicale, Nextcloud, Apple Calendar) using OCR and UI automation on macOS.

**Critical Warning:**
> **When you run `sync_outlook_caldav.py`, _all events in the target CalDAV calendar for the selected date will be deleted before new events are created_. This is a primitive solution to avoid duplicates.**
> 
> Make sure you are syncing to a dedicated calendar or are comfortable with this destructive behavior. Existing events for the selected date will be lost and replaced by the events extracted from Outlook.

**Important:**
> The `caldav_url` in your config **must be the full URL to the calendar collection you want to update** (not just the server root or user path). For Radicale, this is typically:
>
> `https://your-server/username/CALENDAR_ID/`
>
> Example:
> `https://calendar.yourdomain.com/somepath/84996a40-5960-433b-9206-98c4032e46a0/`

---


## Features
- Extracts events from Outlook calendar using UI automation and OCR (no Microsoft server/API required)
- Maps and uploads events to a CalDAV server (supports self-hosted and cloud)
- **Deletes all events in the target calendar for the selected date before uploading new ones (prevents duplicates)**
- Robust error handling, logging, and conflict resolution (Outlook always wins)
- CLI and scheduler support (cron/launchd)

---

## Requirements
- **macOS** with Microsoft Outlook installed and logged-in user session
- **Python 3.11+**
- **Tesseract OCR** (`brew install tesseract`)
- Accessibility permission for automation (System Settings → Privacy & Security → Accessibility)
- A reachable CalDAV server (e.g., Radicale, Nextcloud, Apple Calendar)

---

## Installation
1. **Clone the repository:**
   ```sh
   git clone https://github.com/beveradb/outlook-calendar-to-caldav.git
   cd outlook-calendar-to-caldav
   ```
2. **Set up Python environment:**
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   pip install pillow pytesseract caldav pyobjc
   ```
3. **Install Tesseract OCR:**
   ```sh
   brew install tesseract
   ```
4. **Grant Accessibility permissions:**
   - Open System Settings → Privacy & Security → Accessibility
   - Add Terminal (or your Python IDE) to the list and enable access

---

## Configuration
1. **Create/Edit the config file:**
   Copy and edit `config.example.json` to create `config.json`:
   ```json
    {
       "caldav_url": "https://calendar.yourdomain.com/somepath/84996a40-5960-433b-9206-98c4032e46a0/",
       "caldav_username": "your_username",
       "caldav_password": "your_password",
       "outlook_calendar_name": "Calendar",
       "sync_interval_minutes": 15,
       "log_level": "INFO",
       "verify_ssl": false,
       "pushbullet_api_key": "YOUR_PUSHBULLET_API_KEY"
    }
    # Set "verify_ssl": false to disable SSL certificate verification (for self-signed/test servers)
   ```
   - `caldav_url`: Your CalDAV server's calendar URL (ending with `/`)
   - `caldav_username`/`caldav_password`: CalDAV credentials
   - `outlook_calendar_name`: Name of the Outlook calendar to sync
   - `pushbullet_api_key`: (Optional) Your Pushbullet API key. If set, notifications will be sent to your Pushbullet account on successful sync or error.

### Pushbullet Notifications

This tool supports sending push notifications to your devices using Pushbullet. Notifications are sent for both successful syncs and errors, helping you monitor calendar sync status without manually checking logs.

**How Pushbullet Notifications Work:**
- If you provide a Pushbullet API key in your `config.json`, the tool will send notifications to your Pushbullet account.
- On successful sync, you receive a notification like:
   - "Outlook to CalDAV synced successfully, X events created"
- On error, you receive a notification with the error message (e.g., network issues, authentication failures, or sync errors).
- If no API key is set, notifications are disabled and you will only see log output.

**Setup Instructions:**
1. Sign up for Pushbullet and get your API key from https://www.pushbullet.com/#settings
2. Add your API key to `config.json` as `"pushbullet_api_key": "YOUR_PUSHBULLET_API_KEY"`
3. Run the sync tool as usual. Notifications will be sent to all devices linked to your Pushbullet account.

**Security Note:**
- Your Pushbullet API key is sensitive. Never share or commit it to public repositories.
- The tool only sends notifications; it does not access or read your Pushbullet messages.

**Notification Details:**
- Success: "Outlook to CalDAV synced successfully, X events created"
- Error: "Outlook to CalDAV sync failed: <error details>"

**Troubleshooting:**
- If you do not receive notifications, check your API key and device setup in Pushbullet.
- Errors in notification delivery are logged in `logs/calendar_sync.log`.

---

## Running the Tool Manually
1. **Activate your Python environment:**
   ```sh
   source .venv/bin/activate
   ```
2. **Run the sync tool:**
   ```sh
   python sync_outlook_caldav.py
   ```
   - The config file path `config.json` will be used by default, use `--config` to use another path.
   - By default, syncs today's events. Use `--date YYYY-MM-DD` to sync a specific date.

---


## What to Expect
- **Outlook will launch and switch to calendar view automatically.**
- The tool will take a screenshot, run OCR, parse events, and upload them to your CalDAV server.
- **All events in the target CalDAV calendar for the selected date will be deleted before new events are created.**
   - This ensures no duplicates, but means any existing events for that date will be lost and replaced by the new sync.
- **Log output:**
   - Logs are written to `logs/calendar_sync.log` (and printed to the console)
   - Look for lines like:
      - `INFO - Starting Outlook to CalDAV synchronization.`
      - `INFO - Configuration loaded successfully.`
      - `INFO - Launching Outlook and navigating to calendar...`
      - `INFO - Synchronization completed successfully.`
   - **Errors** will be logged as `ERROR` or `WARNING` lines

---


## Troubleshooting & Tips
- **No events appear on CalDAV?**
   - Check the log file for errors (authentication, network, OCR failures, etc.)
   - Ensure the CalDAV URL and credentials are correct
   - Make sure Outlook is open and accessible
- **OCR errors?**
   - Try increasing screen brightness or calendar font size
   - Check that Tesseract is installed and working
- **Automation errors?**
   - Ensure Terminal/Python has Accessibility permissions
- **Event Deletion & Idempotency:**
   - The tool deletes all events in the target calendar for the selected date before uploading new ones. This avoids duplicates but is destructive for that date.
   - There is no incremental sync; all events for the date are replaced each run.

---

## Scheduling (Optional)
- See `scripts/README.md` for instructions on running the tool automatically with `cron` or `launchd`.

---

## Support & Contributions
- See `quickstart.md` and `specs/002-synchronise-outlook-work/` for more details and advanced usage.
- Issues and PRs welcome!
