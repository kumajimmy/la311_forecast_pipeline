"""CLI entrypoint for LA 311 ingestion."""

import argparse
import logging
import sys
from datetime import date, timedelta

from . import availability, client, writer

log = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ingest LA 311 data to raw partitions.")

    date_group = p.add_mutually_exclusive_group()
    date_group.add_argument("--date", type=date.fromisoformat, help="Single date (YYYY-MM-DD)")
    date_group.add_argument("--latest", action="store_true",
                            help="Ingest latest available date(s)")

    p.add_argument("--start", type=date.fromisoformat, help="Range start (inclusive)")
    p.add_argument("--end", type=date.fromisoformat, help="Range end (inclusive)")
    p.add_argument("--days-back", type=int, default=1,
                   help="With --latest, ingest N days ending at latest (default 1)")
    p.add_argument("--limit", type=int, default=None, help="Max records per day (for testing)")
    p.add_argument("--on-empty", choices=["fail", "warn", "skip"], default="warn",
                   help="Behavior when no records found (default: warn)")

    args = p.parse_args(argv)

    if args.latest and (args.start or args.end):
        p.error("--latest cannot be used with --start/--end")

    return args


def resolve_dates(args: argparse.Namespace) -> list[date]:
    if args.latest:
        latest_date, has_data = availability.check_latest()
        if not has_data:
            return []
        n = args.days_back
        return [latest_date - timedelta(days=i) for i in range(n - 1, -1, -1)]

    if args.date:
        return [args.date]
    if args.start and args.end:
        days = []
        d = args.start
        while d <= args.end:
            days.append(d)
            d += timedelta(days=1)
        return days
    # default: yesterday
    return [date.today() - timedelta(days=1)]


def _handle_empty(args: argparse.Namespace, msg: str) -> None:
    """Apply --on-empty policy. May call sys.exit(1) for 'fail'."""
    if args.on_empty == "fail":
        log.error(msg)
        sys.exit(1)
    elif args.on_empty == "warn":
        log.warning(msg)
    else:  # skip
        log.info(msg)


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = parse_args(argv)
    dates = resolve_dates(args)

    if not dates:
        _handle_empty(args, "No dates resolved (upstream may be unavailable)")
        return

    log.info("Ingesting %d day(s): %s .. %s", len(dates), dates[0], dates[-1])

    for day in dates:
        records = client.fetch_day(day, limit=args.limit)
        if records:
            writer.write_day(day, records)
        else:
            _handle_empty(args, f"No records for {day}")


if __name__ == "__main__":
    main()
