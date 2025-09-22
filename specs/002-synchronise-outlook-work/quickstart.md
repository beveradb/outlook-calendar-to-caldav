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

