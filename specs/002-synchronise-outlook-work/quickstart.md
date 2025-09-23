# Quickstart: Outlook → CalDAV sync (PoC)

Prerequisites
- macOS machine with Microsoft Outlook installed and logged-in user session.
- Python 3.11
- `tesseract` OCR engine installed (e.g., `brew install tesseract`)
- Accessibility permission granted to the tool (System Settings → Privacy & Security → Accessibility)
- A reachable CalDAV server with credentials (test Radicale server recommended for local testing)

Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install pillow pytesseract caldav pyobjc
```

Configure
- Create `config.json` at the repo root or feature folder with CalDAV endpoint and credentials, OCR engine choice, and `conflict_policy`.

Dry run
```bash
python sync_outlook_caldav.py --config specs/002-synchronise-outlook-work/config.json --dry-run
```

Schedule
- Use `launchd` or `cron` to run the script periodically; ensure a GUI session is present for UI automation.
- Example (cron):

    ```sh
    bash scripts/schedule_sync_cron.sh 30
    # This will run the sync every 30 minutes using your config and sync_state files.
    ```
- Example (launchd, macOS):

    1. Copy the launchd plist:
        ```sh
        cp scripts/com.beveradb.outlook-caldav-sync.plist ~/Library/LaunchAgents/
        launchctl load ~/Library/LaunchAgents/com.beveradb.outlook-caldav-sync.plist
        ```
    2. Edit the interval or paths in the plist as needed.
    3. Logs will appear in `sync_launchd.log` in the project root.

See `scripts/README.md` for details and customization tips.

