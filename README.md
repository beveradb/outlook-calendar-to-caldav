
# Outlook to CalDAV Sync Tool

Synchronize your Microsoft Outlook Calendar to any CalDAV server (e.g., Radicale, Nextcloud, Apple Calendar) using OCR and UI automation on macOS.

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
- Idempotent sync: avoids duplicate uploads
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
       "sync_state_filepath": "sync_state.json",
       "verify_ssl": false
    }
    # Set "verify_ssl": false to disable SSL certificate verification (for self-signed/test servers)
   ```
   - `caldav_url`: Your CalDAV server's calendar URL (ending with `/`)
   - `caldav_username`/`caldav_password`: CalDAV credentials
   - `outlook_calendar_name`: Name of the Outlook calendar to sync
   - `sync_state_filepath`: Path to the sync state file (tracks idempotency)

2. **(Optional) Prepare sync state file:**
   - The tool will create/update this file automatically (default: `sync_state.json`)

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
- **Idempotency:**
  - The tool will not re-upload events it has already synced (tracked in `sync_state.json`)

---

## Scheduling (Optional)
- See `scripts/README.md` for instructions on running the tool automatically with `cron` or `launchd`.

---

## Support & Contributions
- See `quickstart.md` and `specs/002-synchronise-outlook-work/` for more details and advanced usage.
- Issues and PRs welcome!
