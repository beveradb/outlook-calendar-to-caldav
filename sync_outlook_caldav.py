import argparse
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.sync_tool import sync_outlook_to_caldav
from src.utils.logger import setup_logging

def main():
    parser = argparse.ArgumentParser(description="Synchronize Outlook calendar events to CalDAV.")
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to the configuration file (default: config.json)"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Date for which to sync events (YYYY-MM-DD, default: today)"
    )

    args = parser.parse_args()

    logger = setup_logging()
    logger.info("Starting Outlook to CalDAV synchronization.")

    success = sync_outlook_to_caldav(args.config, args.date)

    if success:
        logger.info("Synchronization completed successfully.")
        sys.exit(0)
    else:
        logger.error("Synchronization failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
