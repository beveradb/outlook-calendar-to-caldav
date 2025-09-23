#!/bin/bash
# scripts/schedule_sync_cron.sh
# Example cron job installer for periodic Outlook-to-CalDAV sync
# Usage: bash scripts/schedule_sync_cron.sh [interval_minutes]
# Default: every 30 minutes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON="python3"
SYNC_SCRIPT="$PROJECT_ROOT/sync_outlook_caldav.py"
CONFIG="$PROJECT_ROOT/specs/002-synchronise-outlook-work/config.yaml"
STATE="$PROJECT_ROOT/specs/002-synchronise-outlook-work/sync_state.json"
LOGFILE="$PROJECT_ROOT/sync_cron.log"

INTERVAL="${1:-30}"

CRON_LINE="*/$INTERVAL * * * * $PYTHON $SYNC_SCRIPT --config $CONFIG --state $STATE >> $LOGFILE 2>&1"

# Check if already installed
(crontab -l 2>/dev/null | grep -F "$SYNC_SCRIPT" >/dev/null) && {
  echo "Cron job already installed. Remove it first if you want to change the interval."
  exit 1
}

# Install new cron job
(crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
echo "Installed cron job: $CRON_LINE"
