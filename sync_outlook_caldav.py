import argparse
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.sync_tool import sync_outlook_to_caldav, sync_from_images
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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run: log actions but do not modify the remote CalDAV server."
    )

    parser.add_argument(
        "--images",
        nargs="+",
        metavar="IMG",
        help="Parse-only mode: sync these Outlook week captures (one per week; join scrolled "
             "captures of one week with '+'). Skips launching Outlook and screenshotting.",
    )
    parser.add_argument(
        "--expect-weeks",
        nargs="+",
        metavar="YYYY-MM-DD",
        help="With --images: the Monday each capture should show (one per image). A capture "
             "whose visible range doesn't start on its Monday aborts the sync.",
    )
    parser.add_argument(
        "--json-result",
        metavar="PATH",
        help="With --images: write {ok, created, deleted, per_image, ranges, error} here.",
    )

    args = parser.parse_args()

    if args.images:
        logger = setup_logging()
        logger.info(f"Starting parse-only sync of {len(args.images)} capture(s).")
        try:
            from datetime import date
            weeks = [date.fromisoformat(w) for w in args.expect_weeks] if args.expect_weeks else None
            if weeks is not None and len(weeks) != len(args.images):
                raise ValueError("--expect-weeks needs one Monday per --images entry")
            result = sync_from_images(args.config, args.images, dry_run=args.dry_run,
                                      expect_weeks=weeks)
        except Exception as e:
            logger.exception("Parse-only sync failed")
            result = {"ok": False, "created": 0, "deleted": 0, "per_image": [], "ranges": [],
                      "error": f"{type(e).__name__}: {e}"}
        if args.json_result:
            with open(args.json_result, "w") as f:
                json.dump(result, f)
        logger.info(f"Result: {result}")
        sys.exit(0 if result["ok"] else 1)

    logger = setup_logging()
    logger.info("Starting Outlook to CalDAV synchronization.")

    success = sync_outlook_to_caldav(args.config, args.date, dry_run=args.dry_run)

    if success:
        logger.info("Synchronization completed successfully.")
        sys.exit(0)
    else:
        logger.error("Synchronization failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
