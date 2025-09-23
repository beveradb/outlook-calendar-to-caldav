# Scheduling the Outlook-to-CalDAV Sync Tool

This directory contains example scripts for scheduling the sync tool to run automatically on macOS (launchd) or Unix-like systems (cron).

## 1. Using Cron (cross-platform, simple)

- Script: `scripts/schedule_sync_cron.sh`
- Installs a cron job to run the sync every N minutes (default: 30).
- Usage:

```sh
bash scripts/schedule_sync_cron.sh [interval_minutes]
```
- The script will append a line to your crontab to run:

```
python3 /Users/AK17/Projects/calendar-sync/sync_outlook_caldav.py --config /Users/AK17/Projects/calendar-sync/specs/002-synchronise-outlook-work/config.yaml --state /Users/AK17/Projects/calendar-sync/specs/002-synchronise-outlook-work/sync_state.json
```

- Output is logged to `sync_cron.log` in the project root.

## 2. Using launchd (macOS only, robust)

- File: `scripts/com.yourorg.outlook-caldav-sync.plist`
- Copy this file to `~/Library/LaunchAgents/` and load it with:

```sh
cp scripts/com.yourorg.outlook-caldav-sync.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.yourorg.outlook-caldav-sync.plist
```

- By default, runs every 1800 seconds (30 minutes). Edit `<integer>1800</integer>` to change interval.
- Logs output to `sync_launchd.log` in the project root.
- Unload with:

```sh
launchctl unload ~/Library/LaunchAgents/com.yourorg.outlook-caldav-sync.plist
```

## Customization
- Edit the paths in the scripts if your project is in a different location.
- For more advanced scheduling, see `man 5 crontab` or Apple launchd documentation.
