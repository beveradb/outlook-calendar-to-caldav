#!/bin/zsh
export PATH=/opt/homebrew/bin:$PATH
source ~/Projects/calendar-sync/.venv/bin/activate
~/Projects/calendar-sync/.venv/bin/python ~/Projects/calendar-sync/sync_outlook_caldav.py --config ~/Projects/calendar-sync/config.json
